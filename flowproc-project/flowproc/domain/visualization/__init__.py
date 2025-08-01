"""
Visualization module for flow cytometry data.

This module provides comprehensive visualization capabilities for flow cytometry data,
including time-course analysis, bar plots, and interactive dashboards.
"""

# Core visualization components
from .models import ProcessedData, PlotData, VisualizationResult
from .config import VisualizationConfig, ConfigPresets, ConfigurationValidator
from .data_processor import DataProcessor, DataProcessorFactory, preprocess_flowcytometry_data
from .unified_service import UnifiedVisualizationService, get_unified_visualization_service
from .plot_factory import PlotFactory, PlotCreator, BasePlotCreator
from .plotly_renderer import PlotlyRenderer

# High-level API
from .facade import (
    create_visualization,
    create_quick_plot,
    create_time_course_visualization,
    create_publication_figure,
    batch_create_visualizations,
    validate_data_for_visualization,
    visualize_data
)

# Quick plot functions
from .facade import (
    quick_scatter_plot,
    quick_bar_plot,
    quick_line_plot,
    quick_box_plot
)

# Simple visualizer for direct plotting
from .simple_visualizer import (
    plot,
    time_plot,
    time_plot_faceted,
    compare_groups
)

# Legacy compatibility
from .visualize import visualize_data as legacy_visualize_data

# Export all public APIs
__all__ = [
    # Core components
    'ProcessedData',
    'PlotData', 
    'VisualizationResult',
    'VisualizationConfig',
    'ConfigPresets',
    'ConfigurationValidator',
    'DataProcessor',
    'DataProcessorFactory',
    'preprocess_flowcytometry_data',
    'UnifiedVisualizationService',
    'get_unified_visualization_service',
    'PlotFactory',
    'PlotCreator',
    'BasePlotCreator',
    'PlotlyRenderer',
    
    # High-level API
    'create_visualization',
    'create_quick_plot',
    'create_time_course_visualization',
    'create_publication_figure',
    'batch_create_visualizations',
    'validate_data_for_visualization',
    'visualize_data',
    
    # Quick plot functions
    'quick_scatter_plot',
    'quick_bar_plot',
    'quick_line_plot',
    'quick_box_plot',
    
    # Simple visualizer
    'plot',
    'time_plot',
    'time_plot_faceted',
    'compare_groups',
    
    # Legacy compatibility
    'legacy_visualize_data'
]
