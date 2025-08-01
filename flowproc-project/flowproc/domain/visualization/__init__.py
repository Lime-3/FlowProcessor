"""
Simplified Visualization Module - Based on Simple Visualizer

This module provides a clean, simple interface for flow cytometry visualization
using the proven simple_visualizer as the foundation.
"""

# Main visualization functions (the standard interface)
from .simple_visualizer import (
    plot,                    # Main plotting function
    time_plot,              # Time-course analysis
    time_plot_faceted,      # Faceted time-course plots
    compare_groups,         # Group comparisons
    scatter,                # Quick scatter plots
    bar,                    # Quick bar plots
    box,                    # Quick box plots
    histogram               # Quick histograms
)

# Utility functions
from .simple_visualizer import (
    _detect_flow_columns,   # Column detection
    _analyze_data_size      # Data analysis
)

# Export the main interface
__all__ = [
    # Main functions
    'plot',
    'time_plot', 
    'time_plot_faceted',
    'compare_groups',
    
    # Quick plot functions
    'scatter',
    'bar', 
    'box',
    'histogram',
    
    # Utilities
    '_detect_flow_columns',
    '_analyze_data_size'
]

# Legacy compatibility (deprecated)
def create_visualization(*args, **kwargs):
    """Legacy function - use plot() instead."""
    import warnings
    warnings.warn(
        "create_visualization() is deprecated. Use plot() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return plot(*args, **kwargs)

def create_time_course_visualization(*args, **kwargs):
    """Legacy function - use time_plot() instead."""
    import warnings
    warnings.warn(
        "create_time_course_visualization() is deprecated. Use time_plot() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return time_plot(*args, **kwargs)
