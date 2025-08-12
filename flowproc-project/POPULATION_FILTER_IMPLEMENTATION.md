# Population Filter Implementation for Timecourse Plots

## Overview

This implementation adds a population dropdown filter to the FlowProcessor visualization dialog, specifically for timecourse plots. When timecourse mode is enabled, users can select a single population to display, ensuring that single timecourse plots show only one population instead of multiple overlaid populations.

## Key Features

### 1. Population Dropdown Filter
- **Location**: Added to the visualization dialog settings panel
- **Visibility**: Only visible when timecourse mode is enabled
- **Options**: 
  - "All Populations" - for faceted plots
  - Individual population names (e.g., "CD4+", "CD8+", "B Cells")
  - "No Populations Available" - fallback when no populations detected

### 2. Smart Population Detection
- **Automatic Detection**: Analyzes data columns to identify available populations
- **Metric-Based**: Populations are detected based on the selected Y-axis metric
- **Fallback Detection**: Uses flow cytometry column detection if metric-based detection fails
- **Name Extraction**: Intelligently extracts population names from column headers

### 3. Single Population Timecourse Plots
- **Filtered Display**: When a population is selected, only that population is shown
- **Single Trace**: Ensures single timecourse plots display one population line
- **Fallback Logic**: If population filter doesn't match, falls back to showing all populations

## Implementation Details

### Files Modified

#### 1. `flowproc/presentation/gui/views/dialogs/visualization_dialog.py`
- Added `selected_population` to `VisualizationOptions` dataclass
- Added population dropdown UI components
- Implemented population filter population logic
- Added population name extraction methods
- Updated timecourse toggle handler to show/hide population filter
- Modified plot generation to pass population filter

#### 2. `flowproc/domain/visualization/time_plots.py`
- Added `population_filter` parameter to `create_timecourse_visualization`
- Updated `_prepare_data` to filter value columns based on population
- Modified `_create_single_timecourse` to handle single population requests
- Enhanced logging for population filtering operations

### Key Methods Added

#### Population Detection
```python
def _populate_population_options(self, df: pd.DataFrame):
    """Populate population filter with available populations from the data."""
    
def _extract_population_name(self, column_name: str, metric: str) -> Optional[str]:
    """Extract population name from a column that contains both metric and population info."""
    
def _extract_population_name_from_column(self, column_name: str) -> Optional[str]:
    """Extract population name from a column without knowing the metric."""
```

#### Population Filtering
```python
# In _prepare_data function
if population_filter:
    # Filter value columns to only include those matching the selected population
    filtered_value_cols = []
    for col in value_cols:
        if population_filter in col:
            filtered_value_cols.append(col)
    
    if filtered_value_cols:
        value_cols = filtered_value_cols
        logger.info(f"Applied population filter '{population_filter}': {len(value_cols)} columns remaining")
    else:
        logger.warning(f"No columns found matching population '{population_filter}', using all available columns")
```

## Usage

### 1. Enable Timecourse Mode
- Check the "Time Course Mode" checkbox in the visualization dialog

### 2. Select Population
- The population dropdown will appear
- Choose from available populations or "All Populations"

### 3. Generate Plot
- Click "Generate Plot" to create a timecourse visualization
- If a specific population is selected, only that population will be displayed
- If "All Populations" is selected, a faceted plot will be created

## Benefits

1. **Cleaner Single Timecourse Plots**: No more overlaid populations cluttering the visualization
2. **Better User Control**: Users can focus on specific populations of interest
3. **Improved Readability**: Single population plots are easier to interpret
4. **Consistent Behavior**: Aligns with user expectations for single timecourse plots
5. **Flexible Options**: Users can still view all populations when needed

## Technical Notes

- **Performance**: Population filtering is applied at the column selection level, not data filtering
- **Fallback**: Robust fallback logic ensures plots always generate even with invalid population filters
- **Logging**: Comprehensive logging for debugging and monitoring
- **UI State**: Population filter automatically shows/hides based on timecourse mode
- **Data Integrity**: Original data is never modified, only the columns used for plotting

## Testing

The implementation has been tested with:
- ✅ Multiple population datasets
- ✅ Single population filtering
- ✅ Non-existent population fallback
- ✅ UI state management
- ✅ Data flow integrity

## Future Enhancements

1. **Population Grouping**: Group related populations (e.g., "T Cell Subsets")
2. **Custom Population Names**: Allow users to define custom population labels
3. **Population Hierarchy**: Support for nested population structures
4. **Batch Population Selection**: Select multiple populations for comparison
5. **Population Statistics**: Show population-specific summary statistics
