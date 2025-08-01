"""
Flow cytometry visualization package.

This package provides visualization tools for flow cytometry data analysis.
"""

# Import the main interface functions from the main visualizer
from .flow_cytometry_visualizer import (
    plot,
    time_plot,
    time_plot_faceted,
    compare_groups,
    scatter,
    bar,
    box,
    histogram
)

# Import the refactored modules for advanced usage
from . import (
    column_utils,
    legend_config,
    data_aggregation,
    plot_creators,
    faceted_plots,
    time_plots,
    plotly_renderer,
    plot_config,
    plot_utils
)

__all__ = [
    # Main interface functions
    'plot',
    'time_plot',
    'time_plot_faceted', 
    'compare_groups',
    'scatter',
    'bar',
    'box',
    'histogram',
    
    # Module names
    'column_utils',
    'legend_config', 
    'data_aggregation',
    'plot_creators',
    'faceted_plots',
    'time_plots',
    'plotly_renderer',
    'plot_config',
    'plot_utils'
]
