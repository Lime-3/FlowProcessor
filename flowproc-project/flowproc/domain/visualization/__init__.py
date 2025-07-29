"""
Visualization domain module for flow cytometry data.
"""

from .service import VisualizationService
from .plotly_renderer import PlotlyRenderer
from .themes import VisualizationThemes

__all__ = [
    'VisualizationService',
    'PlotlyRenderer',
    'VisualizationThemes'
]

"""
Flow cytometry visualization module.

This module provides a modern, modular architecture for creating interactive
visualizations from flow cytometry data. The refactored design follows clean
architecture principles with clear separation of concerns.

Public API:
-----------

High-level functions (recommended):
    create_visualization()          - Main visualization creation function
    create_time_course_visualization() - Time-course optimized visualization  
    create_publication_figure()     - Publication-ready figures
    create_quick_plot()            - Quick exploratory plots
    
Configuration and models:
    VisualizationConfig            - Configuration class
    ProcessedData                  - Processed data container
    VisualizationResult           - Result container with metadata
    
Core classes (for advanced usage):
    DataProcessor                  - Data processing engine
    Visualizer                     - Core visualization engine
    VisualizationService          - Service layer
    
Factory classes:
    DataProcessorFactory          - Factory for creating processors
    VisualizationFactory          - Factory for creating visualizers
    ConfigPresets                 - Predefined configuration presets
    
Legacy compatibility:
    visualize_data()              - Legacy API (deprecated)

Examples:
---------

Basic usage:
    >>> from flowproc.domain.visualization import create_visualization
    >>> fig = create_visualization("data.csv", metric="Freq. of Parent")
    >>> fig.show()

Time course analysis:
    >>> fig = create_time_course_visualization(
    ...     "timecourse_data.csv",
    ...     metric="Freq. of Parent",
    ...     width=1200,
    ...     height=600
    ... )

Advanced configuration:
    >>> from flowproc.domain.visualization import VisualizationConfig, DataProcessor, Visualizer
    >>> config = VisualizationConfig(
    ...     metric="Freq. of Parent",
    ...     time_course_mode=True,
    ...     theme="publication",
    ...     user_group_labels=["Control", "Treatment A", "Treatment B"]
    ... )
    >>> processor = DataProcessor(df, 'SampleID', config)
    >>> processed_data = processor.process()
    >>> visualizer = Visualizer(config)
    >>> fig = visualizer.create_figure(processed_data)

Quick exploratory plots:
    >>> from flowproc.domain.visualization import create_quick_plot
    >>> fig = create_quick_plot(
    ...     df, 
    ...     x_col="Group", 
    ...     y_col="Freq. of Parent CD4",
    ...     plot_type="scatter",
    ...     color_col="Tissue"
    ... )
"""

# Import core models and data structures
from .models import (
    ProcessedData,
    PlotData,
    VisualizationRequest,
    VisualizationResult
)

# Import configuration classes
from .config import (
    VisualizationConfig,
    ValidationResult,
    ConfigurationValidator,
    ConfigPresets
)

# Import core processing and visualization classes
from .data_processor import (
    DataProcessor,
    DataProcessorFactory,
    preprocess_flowcytometry_data,
    detect_data_characteristics
)

from .core import (
    Visualizer,
    VisualizationFactory
)

# Import service layer
from .service import VisualizationService

# Import high-level API functions (main public interface)
from .facade import (
    # Main functions
    create_visualization,
    create_time_course_visualization,
    create_publication_figure,
    create_quick_plot,
    batch_create_visualizations,
    validate_data_for_visualization,
    
    # Quick plot convenience functions
    quick_scatter_plot,
    quick_bar_plot,
    quick_line_plot,
    quick_box_plot,
    
    # Legacy compatibility
    visualize_data  # Deprecated but maintained for compatibility
)

# Import existing components that are being kept
from .plotly_renderer import PlotlyRenderer

# Version and metadata
__version__ = "3.0.0"  # Major version bump for architectural refactoring
__author__ = "FlowProc Development Team"
__description__ = "Modern flow cytometry visualization with clean architecture"

# Define public API
__all__ = [
    # Version info
    '__version__',
    
    # High-level API functions (primary interface)
    'create_visualization',
    'create_time_course_visualization', 
    'create_publication_figure',
    'create_quick_plot',
    'batch_create_visualizations',
    'validate_data_for_visualization',
    
    # Quick plot convenience functions
    'quick_scatter_plot',
    'quick_bar_plot',
    'quick_line_plot',
    'quick_box_plot',
    
    # Configuration and models
    'VisualizationConfig',
    'ProcessedData',
    'VisualizationResult',
    'VisualizationRequest',
    'PlotData',
    'ValidationResult',
    
    # Core classes (for advanced usage)
    'DataProcessor',
    'Visualizer',
    'VisualizationService',
    
    # Factory classes
    'DataProcessorFactory',
    'VisualizationFactory',
    'ConfigPresets',
    'ConfigurationValidator',
    
    # Utilities
    'preprocess_flowcytometry_data',
    'detect_data_characteristics',
    
    # Themes and rendering
    'VisualizationThemes',
    'PlotlyRenderer',
    
    # Legacy compatibility (deprecated)
    'visualize_data',
]

# Module-level configuration
import logging
logger = logging.getLogger(__name__)

# Log the architectural change
logger.debug(f"FlowProc Visualization v{__version__} - Modular architecture loaded")

# Backward compatibility warnings
import warnings

def _deprecated_import_warning():
    """Issue warning for deprecated import patterns."""
    import inspect
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_filename = frame.f_back.f_code.co_filename
        caller_lineno = frame.f_back.f_lineno
        
        # Check if caller is importing deprecated patterns
        # This is a simple heuristic - could be more sophisticated
        if 'visualize.py' in caller_filename:
            warnings.warn(
                "Direct imports from visualize.py are deprecated. "
                "Use 'from flowproc.domain.visualization import ...' instead.",
                DeprecationWarning,
                stacklevel=3
            )

# Convenience function for getting started
def get_started_example():
    """
    Print a getting started example for new users.
    
    This function provides a quick introduction to the new API
    for users who are familiar with the old monolithic approach.
    """
    example = """
    Getting Started with FlowProc Visualization v3.0
    ===============================================
    
    The visualization system has been refactored into a clean, modular architecture.
    Here are some examples to get you started:
    
    ## Basic Usage (Recommended)
    
    ```python
    from flowproc.domain.visualization import create_visualization
    
    # Simple visualization
    fig = create_visualization("data.csv", metric="Freq. of Parent")
    fig.show()
    
    # Save as HTML
    fig = create_visualization(
        "data.csv", 
        metric="Freq. of Parent",
        output_html="my_plot.html",
        theme="publication"
    )
    ```
    
    ## Time Course Analysis
    
    ```python
    from flowproc.domain.visualization import create_time_course_visualization
    
    fig = create_time_course_visualization(
        "timecourse_data.csv",
        metric="Freq. of Parent",
        width=1200,
        height=600
    )
    fig.show()
    ```
    
    ## Advanced Configuration
    
    ```python
    from flowproc.domain.visualization import (
        VisualizationConfig, DataProcessor, Visualizer
    )
    
    # Create custom configuration
    config = VisualizationConfig(
        metric="Freq. of Parent",
        time_course_mode=True,
        theme="publication",
        user_group_labels=["Control", "Treatment A", "Treatment B"],
        tissue_filter="SP",
        width=1000,
        height=600
    )
    
    # Process data
    processor = DataProcessor(df, 'SampleID', config)
    processed_data = processor.process()
    
    # Create visualization
    visualizer = Visualizer(config)
    fig = visualizer.create_figure(processed_data)
    ```
    
    ## Quick Exploratory Plots
    
    ```python
    from flowproc.domain.visualization import create_quick_plot
    
    # Scatter plot
    fig = create_quick_plot(
        df, 
        x_col="Group", 
        y_col="Freq. of Parent CD4",
        color_col="Tissue",
        plot_type="scatter"
    )
    
    # Box plot
    fig = create_quick_plot(
        df,
        x_col="Group",
        y_col="Median CD4", 
        plot_type="box"
    )
    ```
    
    ## Configuration Presets
    
    ```python
    from flowproc.domain.visualization import ConfigPresets, Visualizer
    
    # Use predefined configurations
    config = ConfigPresets.publication_figure()
    config = ConfigPresets.time_course_analysis()
    config = ConfigPresets.quick_exploration()
    
    visualizer = Visualizer(config)
    ```
    
    ## Migration from Legacy API
    
    Old code:
    ```python
    from .facade import visualize_data
    fig = visualize_data(csv_path, output_html, metric="Freq. of Parent")
    ```
    
    New code:
    ```python
    from flowproc.domain.visualization import create_visualization
    fig = create_visualization(csv_path, metric="Freq. of Parent", output_html=output_html)
    ```
    
    ## Key Benefits of the New Architecture
    
    ✅ **Modular Design**: Clear separation of concerns
    ✅ **Type Safety**: Comprehensive type hints for better IDE support  
    ✅ **Testability**: Each component can be tested in isolation
    ✅ **Extensibility**: Easy to add new visualization types and themes
    ✅ **Performance**: Optimized data processing with vectorized operations
    ✅ **Maintainability**: Clean interfaces and well-documented APIs
    ✅ **Backwards Compatibility**: Legacy functions still work (with deprecation warnings)
    
    For more examples and documentation, see the project README and test files.
    """
    
    print(example)

# Configuration validation helper
def check_configuration(config_dict: dict) -> ValidationResult:
    """
    Helper function to validate configuration dictionaries.
    
    Args:
        config_dict: Dictionary with configuration parameters
        
    Returns:
        ValidationResult with validation status and messages
        
    Examples:
        >>> result = check_configuration({
        ...     'metric': 'Freq. of Parent',
        ...     'width': 800,
        ...     'height': 600,
        ...     'theme': 'publication'
        ... })
        >>> if result.valid:
        ...     print("Configuration is valid")
    """
    try:
        config = VisualizationConfig(**config_dict)
        return ConfigurationValidator.validate_config(config)
    except Exception as e:
        result = ValidationResult(valid=False)
        result.add_error(f"Invalid configuration: {str(e)}")
        return result

# Data inspection helper
def inspect_data(data_source, sample_id_col='SampleID'):
    """
    Helper function to inspect data before visualization.
    
    Args:
        data_source: Path to CSV file or DataFrame
        sample_id_col: Sample ID column name
        
    Returns:
        Dictionary with data characteristics and recommendations
        
    Examples:
        >>> info = inspect_data("data.csv")
        >>> print(f"Data shape: {info['shape']}")
        >>> print(f"Has time data: {info['has_time_data']}")
        >>> print(f"Number of groups: {info['num_groups']}")
    """
    if isinstance(data_source, (str, Path)):
        from ..parsing import load_and_parse_df
        df, sid_col = load_and_parse_df(data_source)
    else:
        df = data_source
        sid_col = sample_id_col
    
    return detect_data_characteristics(df)

# Make sure Path is available for inspect_data
from pathlib import Path

# Performance monitoring helper
def benchmark_visualization(func, *args, **kwargs):
    """
    Helper function to benchmark visualization performance.
    
    Args:
        func: Visualization function to benchmark
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Tuple of (result, benchmark_info)
        
    Examples:
        >>> result, benchmark = benchmark_visualization(
        ...     create_visualization,
        ...     "data.csv",
        ...     metric="Freq. of Parent"
        ... )
        >>> print(f"Execution time: {benchmark['execution_time']:.2f}s")
    """
    import time
    import tracemalloc
    
    # Start monitoring
    tracemalloc.start()
    start_time = time.perf_counter()
    
    try:
        result = func(*args, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)
    
    # Stop monitoring
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    benchmark_info = {
        'success': success,
        'error': error,
        'execution_time': end_time - start_time,
        'memory_current_mb': current / 1024 / 1024,
        'memory_peak_mb': peak / 1024 / 1024,
    }
    
    return result, benchmark_info

# Add benchmark helper to public API
__all__.extend([
    'get_started_example',
    'check_configuration', 
    'inspect_data',
    'benchmark_visualization'
])
