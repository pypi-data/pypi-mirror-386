# Quick Start

Get started with geoparquet-io in 5 minutes.

## Installation

```bash
uv pip install geoparquet-io
```

See the [Installation Guide](installation.md) for more options.

## Basic Workflow

### 1. Inspect Your File

First, take a look at what's in your GeoParquet file:

```bash
gpio inspect myfile.parquet
```

This shows you:

- File size and row count
- Coordinate reference system (CRS)
- Bounding box
- Column schema with types

Add `--head 10` to preview the first 10 rows, or `--stats` for column statistics.

### 2. Check Quality

Validate your file against GeoParquet best practices:

```bash
gpio check all myfile.parquet
```

This checks:

- Spatial ordering
- Compression settings
- Bbox metadata structure
- Row group optimization

### 3. Optimize Your File

Add a bounding box column for faster spatial queries:

```bash
gpio add bbox input.parquet output.parquet
```

Sort data using a Hilbert curve for better spatial locality:

```bash
gpio sort hilbert input.parquet sorted.parquet
```

### 4. Add Spatial Indices

Enhance your data with spatial indexing:

```bash
# Add H3 hexagonal cell IDs (resolution 9 ≈ 105m² cells)
gpio add h3 input.parquet output_h3.parquet --resolution 9

# Add KD-tree partition IDs (auto-selects optimal partition count)
gpio add kdtree input.parquet output_kdtree.parquet

# Add country codes via spatial join
gpio add admin-divisions buildings.parquet buildings_with_countries.parquet
```

### 5. Partition Large Datasets

Split large files into manageable partitions:

```bash
# Preview what partitions would be created
gpio partition admin buildings.parquet --preview

# Partition by country code
gpio partition admin buildings.parquet output_dir/

# Partition by H3 cells at resolution 7 (~5km² cells)
gpio partition h3 points.parquet output_dir/ --resolution 7

# Partition by KD-tree (auto-balanced spatial partitions)
gpio partition kdtree large_file.parquet output_dir/
```

## Common Patterns

### Quality Check → Optimize → Validate

```bash
# 1. Check current state
gpio check all input.parquet

# 2. Optimize
gpio add bbox input.parquet temp.parquet
gpio sort hilbert temp.parquet optimized.parquet

# 3. Verify improvements
gpio check all optimized.parquet
```

### Inspect → Enhance → Partition

```bash
# 1. Understand your data
gpio inspect buildings.parquet --stats

# 2. Add country codes
gpio add admin-divisions buildings.parquet buildings_enhanced.parquet

# 3. Split by country
gpio partition admin buildings_enhanced.parquet by_country/
```

### Preview Before Processing

Always use `--preview` to understand what will happen:

```bash
# Preview partitioning strategy
gpio partition string input.parquet --column region --preview

# Preview with analysis
gpio partition h3 input.parquet --resolution 8 --preview

# If satisfied, run without --preview
gpio partition h3 input.parquet output/ --resolution 8
```

## Using the Python API

You can also use geoparquet-io from Python:

```python
from geoparquet_io.core.add_bbox_column import add_bbox_column
from geoparquet_io.core.hilbert_order import hilbert_order

# Add bounding box
add_bbox_column(
    input_parquet="input.parquet",
    output_parquet="output.parquet",
    bbox_name="bbox",
    verbose=True
)

# Sort by Hilbert curve
hilbert_order(
    input_parquet="input.parquet",
    output_parquet="sorted.parquet",
    geometry_column="geometry",
    verbose=True
)
```

See the [Python API documentation](../api/overview.md) for more details.

## Getting Help

Every command has detailed help:

```bash
# General help
gpio --help

# Command group help
gpio add --help
gpio partition --help

# Specific command help
gpio add bbox --help
gpio partition h3 --help
```

## Next Steps

Now that you know the basics, explore:

- [User Guide](../guide/inspect.md) - Detailed documentation for all features
- [CLI Reference](../cli/overview.md) - Complete command reference
- [Examples](../examples/basic.md) - Real-world usage patterns
