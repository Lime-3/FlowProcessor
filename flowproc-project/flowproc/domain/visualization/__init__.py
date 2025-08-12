"""
Flow Cytometry Visualization Package

This package provides simple visualization tools for flow cytometry data.
"""

# Simple visualizer for quick plotting
from .flow_cytometry_visualizer import (
    plot,
    compare_groups,
    scatter,
    bar,
    box,
    histogram
)

# Unified timecourse visualization system
from .time_plots import create_timecourse_visualization

# Utility functions
from .column_utils import detect_flow_columns
from .plot_creators import (
    create_single_metric_plot,
    create_cell_type_comparison_plot,
    create_basic_plot
)
from .legend_config import configure_legend
# PlotConfig class removed - constants are imported directly where needed
# plot_utils functions imported individually where needed

# Export simple interface
__all__ = [
    # Simple interface
    'plot',
    'compare_groups',
    'scatter',
    'bar',
    'box',
    'histogram',
    
    # Unified timecourse system
    'create_timecourse_visualization',
    
    # Utilities
    'detect_flow_columns',
    'create_single_metric_plot',
    'create_cell_type_comparison_plot', 
    'create_basic_plot',
    'configure_legend'
]
