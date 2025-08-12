# SEM Error Bars Implementation for Timecourse Plots

## Overview
This document summarizes the implementation of Standard Error of the Mean (SEM) error bars for timecourse plots in the FlowProcessor application.

## What Was Implemented

### 1. Single Timecourse Plots
- **File**: `flowproc/domain/visualization/time_plots.py`
- **Function**: `_create_single_metric_timecourse()`
- **Changes**: Added `error_y='sem'` parameter to plotly express functions when aggregation is "mean_sem"
- **Result**: Line, scatter, and area plots now display SEM error bars when grouping is enabled

### 2. Overlay Timecourse Plots
- **File**: `flowproc/domain/visualization/time_plots.py`
- **Function**: `_create_overlay_timecourse()`
- **Changes**: Added manual error bar configuration using `go.Scatter` with `error_y` parameter
- **Result**: Multiple metric overlay plots now display SEM error bars for each trace

### 3. Faceted Timecourse Plots
- **File**: `flowproc/domain/visualization/faceted_plots.py`
- **Functions**: 
  - `_create_faceted_plot()` (base function)
  - `create_cell_type_faceted_plot()`
  - `create_group_faceted_plot()`
- **Changes**: 
  - Added aggregation parameters (`aggregation`, `group_col`)
  - Implemented SEM calculation and error bar display for both faceting modes
  - Added numpy import for mathematical operations
- **Result**: Both cell type and group faceted plots now display SEM error bars

## Technical Details

### SEM Calculation
```python
# For timecourse plots, aggregate by both group and time
agg_df = df.groupby([group_col, time_col])[value_col].agg(['mean', 'std', 'count']).reset_index()
agg_df['sem'] = agg_df['std'] / np.sqrt(agg_df['count'])
```

### Error Bar Configuration
```python
# For plotly express
fig = px.line(plot_df, x=time_col, y=y_col, color=group_col, error_y='sem', **kwargs)

# For manual go.Scatter
error_y_data = dict(
    type='data',
    array=group_data['sem'],
    visible=True
)
fig.add_trace(go.Scatter(..., error_y=error_y_data))
```

### Aggregation Modes
- **"mean_sem"**: Calculates mean ± SEM with error bars
- **"median_iqr"**: Calculates median ± IQR (not yet implemented)
- **"raw"**: Uses raw data without aggregation or error bars

## Usage Examples

### Basic Timecourse with SEM
```python
fig = create_timecourse_visualization(
    "data.csv",
    time_column="Time",
    metric="Freq. of Parent CD4",
    group_by="Group",
    aggregation="mean_sem",  # Enable SEM error bars
    plot_type="line"
)
```

### Faceted Timecourse with SEM
```python
fig = create_timecourse_visualization(
    "data.csv",
    time_column="Time",
    group_by="Group",
    facet_by="Cell Type",
    aggregation="mean_sem",  # Enable SEM error bars
    plot_type="line"
)
```

## Benefits

1. **Statistical Rigor**: Provides visual representation of data variability
2. **Replicate Handling**: Automatically handles multiple replicates per timepoint
3. **Consistent Interface**: Same aggregation parameter works across all plot types
4. **Performance**: Efficient aggregation reduces data points while preserving statistical information

## Testing

The implementation was tested with:
- Single timecourse plots (✅ PASS)
- Faceted timecourse plots (✅ PASS)  
- Overlay timecourse plots (✅ PASS)

All test cases confirmed that SEM error bars are properly displayed when `aggregation="mean_sem"` is specified.

## Future Enhancements

1. **Additional Aggregation Methods**: Implement median ± IQR error bars
2. **Custom Error Bar Styling**: Allow customization of error bar appearance
3. **Confidence Intervals**: Add option for confidence interval bands instead of error bars
4. **Statistical Tests**: Integrate significance testing between groups

## Files Modified

1. `flowproc/domain/visualization/time_plots.py` - Main timecourse functions
2. `flowproc/domain/visualization/faceted_plots.py` - Faceted plot functions
3. `flowproc/domain/visualization/data_aggregation.py` - Already had SEM calculation functions

## Conclusion

SEM error bars are now fully implemented across all timecourse visualization types in the FlowProcessor application. Users can enable them by setting `aggregation="mean_sem"` when creating timecourse plots, providing a robust statistical representation of their flow cytometry time series data.
