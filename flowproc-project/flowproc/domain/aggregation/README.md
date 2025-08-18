# Aggregation Domain Module

This module provides a clean, unified architecture for data aggregation in FlowProcessor. It consolidates all aggregation logic into logical layers while maintaining backward compatibility.

## Architecture Overview

### 1. Core Layer (`core.py`)
**Simple, focused statistical functions** for basic aggregation needs:
- `group_stats()` - Single column aggregation with mean/std/count/sem
- `group_stats_multi()` - Multi-column aggregation in long format
- `timecourse_group_stats()` - Time-based aggregation
- `generic_aggregate()` - Flexible aggregation with custom methods

**Use when:** You need simple statistical aggregation without complex flow cytometry logic.

### 2. Service Layer (`service.py`)
**Unified aggregation service** that handles complex flow cytometry operations:
- Tissue parsing and validation
- Time course processing
- Complex grouping and splitting
- Performance optimization and memory management

**Use when:** You need full flow cytometry aggregation with tissue parsing, time courses, etc.

### 3. Specialized Interfaces
**Domain-specific wrappers** that use the unified service:
- `visualization/data_aggregation.py` - For plotting and visualization
- `export/data_aggregator.py` - For Excel and export operations
- `processing/aggregators.py` - For processing workflows

## Quick Start

### Simple Aggregation
```python
from flowproc.domain.aggregation import group_stats, group_stats_multi

# Single column aggregation
result = group_stats(df, 'CD4+', 'Group')
# Returns: Group | mean | std | count | sem

# Multi-column aggregation
result = group_stats_multi(df, ['CD4+', 'CD8+'], 'Group', 'Cell Type', 'Frequency')
# Returns: Group | Cell Type | mean | std | count | sem
```

### Complex Flow Cytometry Aggregation
```python
from flowproc.domain.aggregation import AggregationService

# Create service
service = AggregationService(df, 'SampleID')

# Aggregate all metrics
result = service.aggregate_all_metrics()
# Returns: List of DataFrames (one per tissue if multiple detected)

# Or aggregate specific metrics
result = service.flow_cytometry_aggregate('Frequency', ['CD4+|GFP-A+', 'CD8+|GFP-A+'])
```

### Export Aggregation
```python
from flowproc.domain.aggregation import AggregationService

service = AggregationService(df, 'SampleID')
result = service.export_aggregate(
    value_cols=['CD4+', 'CD8+'],
    group_cols=['Group', 'Time'],
    agg_methods={'CD4+': 'mean', 'CD8+': 'median'}
)
```

## Migration Guide

### From Old VectorizedAggregator
```python
# OLD
from flowproc.domain.processing.vectorized_aggregator import VectorizedAggregator
aggregator = VectorizedAggregator(df, 'SampleID')
result = aggregator.aggregate_all_metrics()

# NEW
from flowproc.domain.aggregation import AggregationService
service = AggregationService(df, 'SampleID')
result = service.aggregate_all_metrics()
```

### From Old DataAggregator
```python
# OLD
from flowproc.domain.export.data_aggregator import DataAggregator
aggregator = DataAggregator('mean')
result = aggregator.aggregate_by_group(df, ['CD4+'], ['Group'])

# NEW
from flowproc.domain.aggregation import AggregationService
service = AggregationService(df, 'SampleID')
result = service.export_aggregate(['CD4+'], ['Group'], {'CD4+': 'mean'})
```

## Configuration Options

### AggregationConfig
```python
config = AggregationConfig(
    groups=[1, 2, 3],
    times=[0, 24, 48],
    tissues_detected=True,
    group_map={1: 'Control', 2: 'Treatment', 3: 'Vehicle'},
    sid_col='SampleID',
    time_course_mode=True,
    include_sem=True,
    split_by_tissue=True
)
```

### Performance Tuning
```python
service = AggregationService(df, 'SampleID')

# Configure for your use case
config = service.get_config()
config.include_sem = False  # Disable SEM calculation for speed
config.split_by_tissue = False  # Keep all tissues together

# Use configuration
result = service.aggregate_all_metrics(config=config)
```

## Best Practices

### 1. Choose the Right Layer
- **Core functions**: Simple statistical aggregation
- **Service**: Complex flow cytometry operations
- **Specialized interfaces**: Domain-specific needs

### 2. Memory Management
```python
service = AggregationService(df, 'SampleID')
try:
    result = service.aggregate_all_metrics()
    return result
finally:
    service.cleanup()  # Always cleanup
```

### 3. Reuse Services
```python
service = AggregationService(df, 'SampleID')

# Multiple operations
result1 = service.simple_aggregate('CD4+', 'Group')
result2 = service.flow_cytometry_aggregate('Frequency', ['CD8+'])

# Cleanup when done
service.cleanup()
```

### 4. Error Handling
```python
try:
    service = AggregationService(df, 'SampleID')
    result = service.aggregate_all_metrics()
except ValueError as e:
    logger.error(f"Aggregation failed: {e}")
    return None
finally:
    if 'service' in locals():
        service.cleanup()
```

## Performance Characteristics

- **Core functions**: Fast, minimal overhead
- **Service layer**: Optimized for large datasets with vectorized operations
- **Memory usage**: Automatic cleanup and optimization
- **Scalability**: Handles datasets from 1K to 1M+ rows efficiently

## Testing

All aggregation functions include comprehensive tests:
```bash
# Run aggregation tests
pytest tests/unit/test_aggregation.py -v

# Run performance tests
pytest tests/performance/test_aggregation_performance.py -v
```

## Contributing

When adding new aggregation functionality:

1. **Core functions**: Add to `core.py` if it's a simple statistical operation
2. **Complex logic**: Add to `AggregationService` in `service.py`
3. **Domain-specific**: Add to appropriate specialized interface
4. **Tests**: Include unit tests and performance benchmarks
5. **Documentation**: Update this README and docstrings
