#!/usr/bin/env python3

import click

from geoparquet_io.core.common import (
    find_primary_geometry_column,
    safe_file_url,
)


def _find_optimal_iterations(total_rows, target_rows, verbose=False):
    """
    Find optimal iteration count to get closest to target_rows per partition.

    Uses adaptive search: tests iterations until we start moving away from target.
    """
    best_iterations = None
    best_distance = float("inf")

    # Test iterations from 1 to 20
    for i in range(1, 21):
        partitions = 2**i
        avg_rows_per_partition = total_rows / partitions
        distance = abs(avg_rows_per_partition - target_rows)

        if distance < best_distance:
            best_distance = distance
            best_iterations = i
        elif distance > best_distance * 1.5:
            # We're moving away from target significantly, stop
            break

    return best_iterations


def _build_sampling_query(
    input_url, geom_col, kdtree_column_name, iterations, sample_size, con, verbose=False
):
    """
    Build a sampling-based KD-tree query that computes boundaries on a sample,
    then applies them to the full dataset using iterative CTEs.

    Strategy:
    1. Sample the data and compute KD-tree to get split boundaries
    2. Build a series of CTEs that iteratively compute partition IDs
    3. Each CTE checks boundaries and appends '0' or '1' to partition ID
    """
    # Phase 1: Compute boundaries from sample
    # We need to capture the actual boundary value used at each split
    boundaries_query = f"""
        WITH RECURSIVE kdtree_sample(iteration, x, y, partition_id, split_value) AS (
            SELECT
                0 AS iteration,
                ST_X(ST_Centroid({geom_col})) AS x,
                ST_Y(ST_Centroid({geom_col})) AS y,
                '0' AS partition_id,
                NULL::DOUBLE AS split_value
            FROM '{input_url}' USING SAMPLE {sample_size} ROWS

            UNION ALL

            SELECT
                iteration + 1 AS iteration,
                x,
                y,
                IF(
                    IF(MOD(iteration, 2) = 0, x, y) < APPROX_QUANTILE(
                        IF(MOD(iteration, 2) = 0, x, y),
                        0.5
                    ) OVER (
                        PARTITION BY partition_id
                    ),
                    partition_id || '0',
                    partition_id || '1'
                ) AS partition_id,
                APPROX_QUANTILE(
                    IF(MOD(iteration, 2) = 0, x, y),
                    0.5
                ) OVER (
                    PARTITION BY partition_id
                ) AS split_value
            FROM kdtree_sample
            WHERE
                iteration < {iterations}
        )
        SELECT DISTINCT
            iteration,
            partition_id,
            split_value
        FROM kdtree_sample
        WHERE iteration > 0 AND split_value IS NOT NULL
        ORDER BY iteration, partition_id
    """

    # Execute to get boundaries
    boundaries_result = con.execute(boundaries_query).fetchall()

    # Build boundaries dictionary: {(iteration, partition_id): split_value}
    # The partition_id here is the NEW partition after the split
    # To get parent, we strip the last character
    boundaries = {}
    for iteration, partition_id, split_value in boundaries_result:
        parent_partition = partition_id[:-1] if len(partition_id) > 0 else ""
        # Only store one boundary per (iteration, parent) - they should all be the same
        if (iteration, parent_partition) not in boundaries:
            boundaries[(iteration, parent_partition)] = split_value

    # Phase 2: Build iterative query that applies boundaries
    if verbose:
        click.echo("Step 2/2: Building query to apply boundaries to full dataset...")
    # Build series of CTEs, one per iteration
    cte_parts = []

    # CTE 0: Load data with coordinates and initialize partition to '0'
    cte_parts.append(f"""
        data_with_coords AS (
            SELECT *,
                ST_X(ST_Centroid({geom_col})) AS _kdtree_x,
                ST_Y(ST_Centroid({geom_col})) AS _kdtree_y,
                '0' AS _kdtree_partition
            FROM '{input_url}'
        )
    """)

    # CTEs 1..iterations: For each iteration, append '0' or '1' based on boundary
    for i in range(1, iterations + 1):
        if verbose:
            click.echo(f"  Iteration {i}/{iterations}...")
        prev_cte = f"iter_{i - 1}" if i > 1 else "data_with_coords"
        current_cte = f"iter_{i}"

        # Dimension to check: x if (i-1) is even, y if odd
        dim_col = "_kdtree_x" if (i - 1) % 2 == 0 else "_kdtree_y"

        # Build CASE statement for all possible parent partitions at this iteration
        # Get all unique parent partitions that could exist at iteration i-1
        possible_parents = set()
        for iter_num, parent in boundaries.keys():
            if iter_num == i:
                possible_parents.add(parent)

        if not possible_parents:
            # If no boundaries found (shouldn't happen), just append '0'
            case_logic = "_kdtree_partition || '0'"
        else:
            # Build CASE statement
            case_parts = []
            for parent in sorted(possible_parents):
                split_val = boundaries.get((i, parent))
                if split_val is not None:
                    case_parts.append(
                        f"WHEN _kdtree_partition = '{parent}' AND {dim_col} < {split_val} THEN _kdtree_partition || '0'"
                    )
                    case_parts.append(
                        f"WHEN _kdtree_partition = '{parent}' AND {dim_col} >= {split_val} THEN _kdtree_partition || '1'"
                    )

            # Default: append '0' (shouldn't reach here but safety)
            case_logic = f"CASE {' '.join(case_parts)} ELSE _kdtree_partition || '0' END"

        cte_parts.append(f"""
        {current_cte} AS (
            SELECT * EXCLUDE(_kdtree_partition),
                {case_logic} AS _kdtree_partition
            FROM {prev_cte}
        )
        """)

    # Final SELECT
    if verbose:
        click.echo("  Query built, executing on full dataset...")
    final_cte = f"iter_{iterations}"
    cte_sql = ",\n".join(cte_parts)

    full_query = f"""
        WITH {cte_sql}
        SELECT * EXCLUDE(_kdtree_x, _kdtree_y, _kdtree_partition),
            _kdtree_partition AS {kdtree_column_name}
        FROM {final_cte}
    """

    return full_query


def add_kdtree_column(
    input_parquet,
    output_parquet,
    kdtree_column_name="kdtree_cell",
    iterations=9,
    dry_run=False,
    verbose=False,
    compression="ZSTD",
    compression_level=None,
    row_group_size_mb=None,
    row_group_rows=None,
    force=False,
    sample_size=100000,
    auto_target_rows=None,
):
    """
    Add a KD-tree cell ID column to a GeoParquet file.

    Creates balanced spatial partitions using recursive splits alternating
    between X and Y dimensions at medians.

    By default, uses approximate computation: computes partition boundaries
    on a sample, then applies to full dataset in a single pass.

    Performance Note: Approximate mode is O(n), exact mode is O(n × iterations).

    Args:
        input_parquet: Path to the input parquet file
        output_parquet: Path to the output parquet file
        kdtree_column_name: Name for the KD-tree column (default: 'kdtree_cell')
        iterations: Number of recursive splits (1-20). Determines partition count: 2^iterations.
                   If None, will be auto-computed based on auto_target_rows.
        dry_run: Whether to print SQL commands without executing them
        verbose: Whether to print verbose output
        compression: Compression type (ZSTD, GZIP, BROTLI, LZ4, SNAPPY, UNCOMPRESSED)
        compression_level: Compression level (varies by format)
        row_group_size_mb: Target row group size in MB
        row_group_rows: Exact number of rows per row group
        force: Force operation even on large datasets (not recommended)
        sample_size: Number of points to sample for computing boundaries. None for exact mode (default: 100000)
        auto_target_rows: If set, auto-compute iterations to target this many rows per partition
    """
    # Get total row count for auto mode or validation
    input_url = safe_file_url(input_parquet, verbose)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")

    total_count = con.execute(f"SELECT COUNT(*) FROM '{input_url}'").fetchone()[0]

    # Auto-compute iterations if requested
    if iterations is None:
        if auto_target_rows is None:
            raise click.BadParameter("Either iterations or auto_target_rows must be specified")

        # Get file size for MB calculations
        import os

        file_size_mb = os.path.getsize(input_parquet) / (1024 * 1024)

        # Handle MB-based or row-based targets
        if isinstance(auto_target_rows, tuple):
            mode, value = auto_target_rows
            if mode == "mb":
                # Calculate target rows: (total_rows * target_mb) / file_size_mb
                target_rows = int((total_count * value) / file_size_mb)
                target_desc = f"{value:,.1f} MB"
            else:
                target_rows = value
                target_desc = f"{value:,} rows"
        else:
            target_rows = auto_target_rows
            target_desc = f"{auto_target_rows:,} rows"

        iterations = _find_optimal_iterations(total_count, target_rows, verbose)
        partition_count = 2**iterations

        if verbose or not dry_run:
            avg_rows = total_count / partition_count
            avg_mb = file_size_mb / partition_count
            click.echo(
                f"Auto-selected {partition_count} partitions (avg ~{avg_rows:,.0f} rows, ~{avg_mb:,.1f} MB/partition, target: {target_desc})"
            )

    # Validate iterations
    if not 1 <= iterations <= 20:
        raise click.BadParameter(f"Iterations must be between 1 and 20, got {iterations}")

    # Get geometry column for the SQL expression
    geom_col = find_primary_geometry_column(input_parquet, verbose)

    con.close()

    # Note: With approximate mode (default), large datasets are handled efficiently in O(n)

    # KD-tree requires a full table scan with recursive CTE - can't be done as a simple column expression
    # We need to use a different approach than add_computed_column
    # Build a query that selects all original columns plus the KD-tree partition ID

    # Reconnect for actual processing
    input_url = safe_file_url(input_parquet, verbose)

    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")

    if not dry_run and auto_target_rows is None:
        # Only print if we haven't already printed in auto mode
        partition_count = 2**iterations
        mode_str = "exact" if sample_size is None else f"approx (sample: {sample_size:,})"
        click.echo(
            f"Processing {total_count:,} features with {partition_count} partitions ({mode_str})..."
        )

    # Choose algorithm based on sample_size
    if sample_size is None:
        # Exact mode: use full recursive CTE (slower but deterministic)
        if verbose:
            click.echo(f"Computing KD-tree partitions (exact mode: {iterations} iterations)...")
            click.echo("  This will process the full dataset recursively...")
        # https://duckdb.org/2024/09/09/spatial-extension.html
        query = f"""
            WITH RECURSIVE kdtree(iteration, x, y, partition_id, row_id) AS (
                SELECT
                    0 AS iteration,
                    ST_X(ST_Centroid({geom_col})) AS x,
                    ST_Y(ST_Centroid({geom_col})) AS y,
                    '0' AS partition_id,
                    ROW_NUMBER() OVER () AS row_id
                FROM '{input_url}'

                UNION ALL

                SELECT
                    iteration + 1 AS iteration,
                    x,
                    y,
                    IF(
                        IF(MOD(iteration, 2) = 0, x, y) < APPROX_QUANTILE(
                            IF(MOD(iteration, 2) = 0, x, y),
                            0.5
                        ) OVER (
                            PARTITION BY partition_id
                        ),
                        partition_id || '0',
                        partition_id || '1'
                    ) AS partition_id,
                    row_id
                FROM kdtree
                WHERE
                    iteration < {iterations}
            ),
            kdtree_final AS (
                SELECT row_id, partition_id
                FROM kdtree
                WHERE iteration = {iterations}
            ),
            original_with_rownum AS (
                SELECT *, ROW_NUMBER() OVER () AS row_id
                FROM '{input_url}'
            )
            SELECT original_with_rownum.* EXCLUDE (row_id), kdtree_final.partition_id AS {kdtree_column_name}
            FROM original_with_rownum
            JOIN kdtree_final ON original_with_rownum.row_id = kdtree_final.row_id
        """
    else:
        # Approximate mode: compute boundaries on sample, apply to full dataset (faster)
        if verbose:
            click.echo(
                f"Step 1/2: Computing split boundaries from {sample_size:,} sample points..."
            )
        query = _build_sampling_query(
            input_url, geom_col, kdtree_column_name, iterations, sample_size, con, verbose
        )

    # Prepare KD-tree metadata for GeoParquet spec
    partition_count = 2**iterations
    kdtree_metadata = {
        "covering": {
            "kdtree": {
                "column": kdtree_column_name,
                "iterations": iterations,
                "partitions": partition_count,
            }
        }
    }

    if dry_run:
        click.echo(
            click.style(
                "\n=== DRY RUN MODE - SQL Commands that would be executed ===\n",
                fg="yellow",
                bold=True,
            )
        )
        click.echo(click.style(f"-- Input: {input_url}", fg="cyan"))
        click.echo(click.style(f"-- Output: {output_parquet}", fg="cyan"))
        click.echo(click.style(f"-- Column: {kdtree_column_name}", fg="cyan"))
        click.echo(click.style(f"-- Partitions: {partition_count}", fg="cyan"))
        click.echo()
        click.echo(query)
        return

    # Get metadata before processing
    from geoparquet_io.core.common import get_parquet_metadata, write_parquet_with_metadata

    metadata, _ = get_parquet_metadata(input_parquet, verbose)

    # Execute the query and write output
    if verbose:
        click.echo("Writing output file...")
    write_parquet_with_metadata(
        con,
        query,
        output_parquet,
        original_metadata=metadata,
        compression=compression,
        compression_level=compression_level,
        row_group_size_mb=row_group_size_mb,
        row_group_rows=row_group_rows,
        custom_metadata=kdtree_metadata,
        verbose=verbose,
    )

    con.close()

    if not dry_run:
        click.echo(
            f"Added KD-tree column '{kdtree_column_name}' ({partition_count} partitions) to: {output_parquet}"
        )


if __name__ == "__main__":
    add_kdtree_column()
