# CLI Overview

The `gpio` command provides a comprehensive CLI for GeoParquet file operations.

## Command Structure

```
gpio [OPTIONS] COMMAND [ARGS]...
```

## Available Commands

### Core Commands

- **[inspect](inspect.md)** - Examine file metadata and preview data
- **[check](check.md)** - Validate files against best practices
- **[sort](sort.md)** - Spatially sort using Hilbert curves
- **[add](add.md)** - Enhance files with spatial indices
- **[partition](partition.md)** - Split files into optimized partitions
- **[format](format.md)** - Apply formatting best practices

## Global Options

```bash
--version    # Show version number
--help       # Show help message
```

## Getting Help

Every command has detailed help:

```bash
# General help
gpio --help

# Command group help
gpio add --help
gpio partition --help
gpio check --help

# Specific command help
gpio add bbox --help
gpio partition h3 --help
gpio check spatial --help
```

## Legacy Alias

The `gt` command is available as an alias for backwards compatibility:

```bash
gt inspect myfile.parquet  # Same as: gpio inspect myfile.parquet
```

## Common Patterns

### File Operations

Most commands follow this pattern:

```bash
gpio COMMAND INPUT OUTPUT [OPTIONS]
```

Examples:

```bash
gpio add bbox input.parquet output.parquet
gpio sort hilbert input.parquet sorted.parquet
```

### In-Place Operations

Some commands modify files in place:

```bash
gpio format bbox-metadata myfile.parquet
```

### Analysis Commands

Analysis commands take a single input:

```bash
gpio inspect myfile.parquet
gpio check all myfile.parquet
```

### Partition Commands

Partition commands output to directories:

```bash
gpio partition h3 input.parquet output_dir/
```

## Common Options

Many commands share these options:

### Compression

```bash
--compression [ZSTD|GZIP|BROTLI|LZ4|SNAPPY|UNCOMPRESSED]
--compression-level [1-22]  # Varies by format
```

### Row Group Sizing

```bash
--row-group-size [exact row count]
--row-group-size-mb [target size: '256MB', '1GB', etc.]
```

### Workflow Control

```bash
--dry-run      # Preview without executing
--verbose      # Detailed output
--preview      # Preview results (partition commands)
--force        # Override warnings
```

## Exit Codes

- `0` - Success
- `1` - Error (with error message printed)
- `2` - Invalid usage (incorrect arguments)

## Next Steps

Explore individual command references for detailed options and examples.
