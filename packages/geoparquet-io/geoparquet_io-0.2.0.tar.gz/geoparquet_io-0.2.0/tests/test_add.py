"""
Tests for add commands.
"""

import os

import duckdb
import pytest
from click.testing import CliRunner

from geoparquet_io.cli.main import add


class TestAddCommands:
    """Test suite for add commands."""

    def test_add_bbox_to_buildings(self, buildings_test_file, temp_output_file):
        """Test adding bbox column to buildings file (which doesn't have bbox)."""
        runner = CliRunner()
        result = runner.invoke(add, ["bbox", buildings_test_file, temp_output_file])
        assert result.exit_code == 0
        assert os.path.exists(temp_output_file)

        # Verify bbox column was added
        conn = duckdb.connect()
        columns = conn.execute(f'DESCRIBE SELECT * FROM "{temp_output_file}"').fetchall()
        column_names = [col[0] for col in columns]
        assert "bbox" in column_names

        # Verify row count matches
        input_count = conn.execute(f'SELECT COUNT(*) FROM "{buildings_test_file}"').fetchone()[0]
        output_count = conn.execute(f'SELECT COUNT(*) FROM "{temp_output_file}"').fetchone()[0]
        assert input_count == output_count

        # Verify bbox structure
        bbox_col = conn.execute(f'DESCRIBE SELECT * FROM "{temp_output_file}"').fetchall()
        bbox_info = [col for col in bbox_col if col[0] == "bbox"][0]
        assert "STRUCT" in bbox_info[1]

    def test_add_bbox_to_places(self, places_test_file, temp_output_file):
        """Test adding bbox column to places file (which already has bbox)."""
        runner = CliRunner()
        result = runner.invoke(add, ["bbox", places_test_file, temp_output_file])
        # Should fail because bbox column already exists
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_add_bbox_with_custom_name(self, buildings_test_file, temp_output_file):
        """Test adding bbox column with custom name."""
        runner = CliRunner()
        result = runner.invoke(
            add, ["bbox", buildings_test_file, temp_output_file, "--bbox-name", "bounds"]
        )
        assert result.exit_code == 0
        assert os.path.exists(temp_output_file)

        # Verify custom bbox column name was used
        conn = duckdb.connect()
        columns = conn.execute(f'DESCRIBE SELECT * FROM "{temp_output_file}"').fetchall()
        column_names = [col[0] for col in columns]
        assert "bounds" in column_names

    def test_add_bbox_with_verbose(self, buildings_test_file, temp_output_file):
        """Test adding bbox column with verbose flag."""
        runner = CliRunner()
        result = runner.invoke(add, ["bbox", buildings_test_file, temp_output_file, "--verbose"])
        assert result.exit_code == 0
        assert os.path.exists(temp_output_file)

    def test_add_bbox_preserves_columns(self, buildings_test_file, temp_output_file):
        """Test that add bbox preserves all original columns."""
        runner = CliRunner()
        result = runner.invoke(add, ["bbox", buildings_test_file, temp_output_file])
        assert result.exit_code == 0

        # Verify columns are preserved
        conn = duckdb.connect()
        input_columns = conn.execute(f'DESCRIBE SELECT * FROM "{buildings_test_file}"').fetchall()
        output_columns = conn.execute(f'DESCRIBE SELECT * FROM "{temp_output_file}"').fetchall()

        input_col_names = {col[0] for col in input_columns}
        output_col_names = {col[0] for col in output_columns}

        # All input columns should be in output
        assert input_col_names.issubset(output_col_names)
        # Output should have bbox column added
        assert "bbox" in output_col_names

    def test_add_bbox_nonexistent_file(self, temp_output_file):
        """Test add bbox on nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(add, ["bbox", "nonexistent.parquet", temp_output_file])
        # Should fail with non-zero exit code
        assert result.exit_code != 0

    # H3 tests
    def test_add_h3_to_buildings(self, buildings_test_file, temp_output_file):
        """Test adding H3 column to buildings file."""
        runner = CliRunner()
        result = runner.invoke(add, ["h3", buildings_test_file, temp_output_file])
        assert result.exit_code == 0
        assert os.path.exists(temp_output_file)

        # Verify h3_cell column was added
        conn = duckdb.connect()
        conn.execute("INSTALL spatial; LOAD spatial;")
        conn.execute("INSTALL h3 FROM community; LOAD h3;")

        columns = conn.execute(f'DESCRIBE SELECT * FROM "{temp_output_file}"').fetchall()
        column_names = [col[0] for col in columns]
        assert "h3_cell" in column_names

        # Verify row count is preserved
        input_count = conn.execute(f'SELECT COUNT(*) FROM "{buildings_test_file}"').fetchone()[0]
        output_count = conn.execute(f'SELECT COUNT(*) FROM "{temp_output_file}"').fetchone()[0]
        assert input_count == output_count

        # Verify H3 column is VARCHAR
        h3_col = [col for col in columns if col[0] == "h3_cell"][0]
        assert "VARCHAR" in h3_col[1]

        # Verify H3 cells are valid
        valid_count = conn.execute(
            f'SELECT COUNT(*) FROM "{temp_output_file}" '
            f"WHERE h3_is_valid_cell(h3_string_to_h3(h3_cell))"
        ).fetchone()[0]
        assert valid_count == output_count

    def test_add_h3_default_resolution(self, buildings_test_file, temp_output_file):
        """Test that H3 uses resolution 9 by default."""
        runner = CliRunner()
        result = runner.invoke(add, ["h3", buildings_test_file, temp_output_file])
        assert result.exit_code == 0

        # Verify all cells are resolution 9
        conn = duckdb.connect()
        conn.execute("INSTALL spatial; LOAD spatial;")
        conn.execute("INSTALL h3 FROM community; LOAD h3;")

        resolutions = conn.execute(
            f'SELECT DISTINCT h3_get_resolution(h3_string_to_h3(h3_cell)) FROM "{temp_output_file}"'
        ).fetchall()
        assert len(resolutions) == 1
        assert resolutions[0][0] == 9

    def test_add_h3_custom_resolution(self, buildings_test_file, temp_output_file):
        """Test adding H3 column with custom resolution."""
        runner = CliRunner()
        result = runner.invoke(
            add, ["h3", buildings_test_file, temp_output_file, "--resolution", "13"]
        )
        assert result.exit_code == 0

        # Verify all cells are resolution 13
        conn = duckdb.connect()
        conn.execute("INSTALL spatial; LOAD spatial;")
        conn.execute("INSTALL h3 FROM community; LOAD h3;")

        resolutions = conn.execute(
            f'SELECT DISTINCT h3_get_resolution(h3_string_to_h3(h3_cell)) FROM "{temp_output_file}"'
        ).fetchall()
        assert len(resolutions) == 1
        assert resolutions[0][0] == 13

    def test_add_h3_with_custom_name(self, buildings_test_file, temp_output_file):
        """Test adding H3 column with custom name."""
        runner = CliRunner()
        result = runner.invoke(
            add, ["h3", buildings_test_file, temp_output_file, "--h3-name", "h3_building"]
        )
        assert result.exit_code == 0
        assert os.path.exists(temp_output_file)

        # Verify custom H3 column name was used
        conn = duckdb.connect()
        columns = conn.execute(f'DESCRIBE SELECT * FROM "{temp_output_file}"').fetchall()
        column_names = [col[0] for col in columns]
        assert "h3_building" in column_names

    def test_add_h3_with_verbose(self, buildings_test_file, temp_output_file):
        """Test adding H3 column with verbose flag."""
        runner = CliRunner()
        result = runner.invoke(add, ["h3", buildings_test_file, temp_output_file, "--verbose"])
        assert result.exit_code == 0
        assert os.path.exists(temp_output_file)
        assert "Loading DuckDB extension: h3" in result.output

    def test_add_h3_preserves_columns(self, buildings_test_file, temp_output_file):
        """Test that add H3 preserves all original columns."""
        runner = CliRunner()
        result = runner.invoke(add, ["h3", buildings_test_file, temp_output_file])
        assert result.exit_code == 0

        # Verify columns are preserved
        conn = duckdb.connect()
        input_columns = conn.execute(f'DESCRIBE SELECT * FROM "{buildings_test_file}"').fetchall()
        output_columns = conn.execute(f'DESCRIBE SELECT * FROM "{temp_output_file}"').fetchall()

        input_col_names = {col[0] for col in input_columns}
        output_col_names = {col[0] for col in output_columns}

        # All input columns should be in output
        assert input_col_names.issubset(output_col_names)
        # Output should have h3_cell column added
        assert "h3_cell" in output_col_names

    def test_add_h3_nonexistent_file(self, temp_output_file):
        """Test add H3 on nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(add, ["h3", "nonexistent.parquet", temp_output_file])
        # Should fail with non-zero exit code
        assert result.exit_code != 0

    def test_add_h3_metadata(self, buildings_test_file, temp_output_file):
        """Test that H3 metadata is added to GeoParquet file."""
        import json

        import pyarrow.parquet as pq

        runner = CliRunner()
        result = runner.invoke(
            add, ["h3", buildings_test_file, temp_output_file, "--resolution", "13"]
        )
        assert result.exit_code == 0

        # Read metadata
        pf = pq.ParquetFile(temp_output_file)
        metadata = pf.schema_arrow.metadata
        assert b"geo" in metadata

        geo_meta = json.loads(metadata[b"geo"].decode("utf-8"))

        # Verify H3 covering metadata exists
        assert "columns" in geo_meta
        assert "geometry" in geo_meta["columns"]
        assert "covering" in geo_meta["columns"]["geometry"]
        assert "h3" in geo_meta["columns"]["geometry"]["covering"]

        # Verify H3 metadata content
        h3_meta = geo_meta["columns"]["geometry"]["covering"]["h3"]
        assert h3_meta["column"] == "h3_cell"
        assert h3_meta["resolution"] == 13

    # Note: add admin-divisions tests are skipped because they require a countries file
    # and network access. These should be tested separately with appropriate test data.
    @pytest.mark.skip(reason="Requires countries file and network access")
    def test_add_admin_divisions(self, places_test_file, temp_output_file):
        """Test adding admin divisions (skipped - requires countries file)."""
        pass
