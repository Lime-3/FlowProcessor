# Legend Enhancement Summary

## Overview
This document summarizes the enhancements made to the FlowProcessor visualization system to add legend titles and mean +/- SEM labels at the bottom of legends.

## New Features Added

### 1. Legend Titles
- **Configurable legend titles**: Legends can now display custom titles above the legend items
- **Automatic title detection**: The system automatically determines appropriate legend titles based on plot type:
  - "Groups" for plots with group-based coloring
  - "Cell Types" for cell type comparison plots
  - "Populations" for population-based plots
  - "Metrics" for multi-metric plots

### 2. Mean +/- SEM Labels
- **Bottom legend labels**: All legends now display "Mean ± SEM" at the bottom
- **Automatic positioning**: Labels are positioned below the legend items
- **Consistent styling**: Labels use consistent font size and color (gray, slightly smaller than legend text)

## Implementation Details

### Modified Files

#### 1. `flowproc/domain/visualization/legend_config.py`
- **Enhanced `configure_legend()` function**: Added `legend_title` and `show_mean_sem_label` parameters
- **Updated `_configure_global_legend()`**: Added support for legend titles and mean +/- SEM annotations
- **Updated `_create_subplot_legend_annotation()`**: Added support for legend titles and mean +/- SEM labels in subplot legends
- **Fixed title restoration logic**: Prevents existing titles from overriding new custom titles

#### 2. `flowproc/domain/visualization/faceted_plots.py`
- **Updated legend configuration calls**: Added automatic legend title detection and mean +/- SEM labels
- **Smart title selection**: Automatically chooses "Groups" or "Cell Types" based on faceting type

#### 3. `flowproc/domain/visualization/time_plots.py`
- **Enhanced timecourse plots**: Added legend titles and mean +/- SEM labels
- **Context-aware titles**: Uses "Groups", "Populations", or "Metrics" based on plot context

#### 4. `flowproc/domain/visualization/plot_creators.py`
- **Updated all plotting functions**: Added legend titles and mean +/- SEM labels
- **Consistent legend styling**: All plot types now use the enhanced legend system

#### 5. `tests/unit/test_refactored_visualization.py`
- **Updated test cases**: Added tests for new legend parameters
- **Enhanced assertions**: Tests now verify legend titles and positioning

### New Parameters

The `configure_legend()` function now accepts these additional parameters:

```python
def configure_legend(
    fig, df, color_col, ...,
    legend_title: Optional[str] = None,      # Custom legend title
    show_mean_sem_label: bool = True        # Show "Mean ± SEM" label
):
```

### Legend Title Examples

- **Single metric plots**: "Groups" or "Populations"
- **Cell type comparisons**: "Cell Types"
- **Faceted plots**: "Groups" (when faceting by group) or "Cell Types" (when faceting by cell type)
- **Timecourse plots**: "Groups", "Populations", or "Metrics"

## Usage Examples

### Basic Legend with Title
```python
from flowproc.domain.visualization.legend_config import configure_legend

fig = configure_legend(
    fig, df, 'Group',
    legend_title="Experimental Groups",
    show_mean_sem_label=True
)
```

### Automatic Title Detection
```python
# The system automatically detects appropriate titles
fig = configure_legend(fig, df, 'Group', show_mean_sem_label=True)
# Results in "Groups" title for group-based plots
```

## Benefits

1. **Improved Clarity**: Legend titles make it immediately clear what the legend represents
2. **Professional Appearance**: Mean +/- SEM labels provide important statistical context
3. **Consistent Experience**: All plots now have uniform legend styling
4. **Automatic Optimization**: System automatically chooses appropriate titles based on plot context
5. **Backward Compatibility**: Existing code continues to work with enhanced legends

## Testing

- **Unit tests updated**: All legend configuration tests pass
- **Integration verified**: Tested with various plot types and configurations
- **Visual verification**: Generated test plots to confirm appearance

## Future Enhancements

Potential areas for future improvement:
- **Customizable SEM label text**: Allow custom text instead of "Mean ± SEM"
- **Legend position options**: More flexible legend positioning
- **Legend styling themes**: Different visual themes for legends
- **Interactive legends**: Enhanced legend interactivity features

## Conclusion

The legend enhancement system provides a significant improvement to the FlowProcessor visualization capabilities, making plots more professional and informative while maintaining backward compatibility and ease of use.
