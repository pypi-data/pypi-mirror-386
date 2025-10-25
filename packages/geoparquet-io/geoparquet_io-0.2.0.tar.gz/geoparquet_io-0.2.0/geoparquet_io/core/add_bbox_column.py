#!/usr/bin/env python3

import click

from geoparquet_io.core.common import add_computed_column, find_primary_geometry_column


def add_bbox_column(
    input_parquet,
    output_parquet,
    bbox_column_name="bbox",
    dry_run=False,
    verbose=False,
    compression="ZSTD",
    compression_level=None,
    row_group_size_mb=None,
    row_group_rows=None,
):
    """
    Add a bbox struct column to a GeoParquet file.

    Args:
        input_parquet: Path to the input parquet file
        output_parquet: Path to the output parquet file
        bbox_column_name: Name for the bbox column (default: 'bbox')
        dry_run: Whether to print SQL commands without executing them
        verbose: Whether to print verbose output
        compression: Compression type (ZSTD, GZIP, BROTLI, LZ4, SNAPPY, UNCOMPRESSED)
        compression_level: Compression level (varies by format)
        row_group_size_mb: Target row group size in MB
        row_group_rows: Exact number of rows per row group
    """
    # Get geometry column for the SQL expression
    geom_col = find_primary_geometry_column(input_parquet, verbose)

    # Define the SQL expression (the only unique part)
    sql_expression = f"""STRUCT_PACK(
        xmin := ST_XMin({geom_col}),
        ymin := ST_YMin({geom_col}),
        xmax := ST_XMax({geom_col}),
        ymax := ST_YMax({geom_col})
    )"""

    # Use the generic helper for all boilerplate
    add_computed_column(
        input_parquet=input_parquet,
        output_parquet=output_parquet,
        column_name=bbox_column_name,
        sql_expression=sql_expression,
        extensions=None,  # Only needs spatial, which is loaded by default
        dry_run=dry_run,
        verbose=verbose,
        compression=compression,
        compression_level=compression_level,
        row_group_size_mb=row_group_size_mb,
        row_group_rows=row_group_rows,
        dry_run_description="Bounding box struct (xmin, ymin, xmax, ymax)",
    )

    if not dry_run:
        click.echo(f"Successfully added bbox column '{bbox_column_name}' to: {output_parquet}")


if __name__ == "__main__":
    add_bbox_column()
