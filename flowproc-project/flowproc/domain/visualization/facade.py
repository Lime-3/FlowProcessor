"""
High-level API facade for the visualization system.

This module provides simple, convenient functions for creating visualizations
without needing to understand the underlying architecture. It serves as the
main entry point for most users.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
import pandas as pd
import plotly.graph_objects as go

from .models import ProcessedData, VisualizationRequest, VisualizationResult
from .config import VisualizationConfig, ConfigPresets, ConfigurationValidator
from .data_processor import DataProcessor, DataProcessorFactory, preprocess_flowcytometry_data
from .core import Visualizer, VisualizationFactory
from .service import VisualizationService
from ..parsing import load_and_parse_df
from ...core.exceptions import VisualizationError, DataError
from ...logging_config import setup_logging

logger = logging.getLogger(__name__)

# Type aliases
PathLike = Union[str, Path]
DataFrame = pd.DataFrame
Figure = go.Figure


def create_visualization(
    data_source: Union[PathLike, DataFrame],
    metric: Optional[str] = None,
    output_html: Optional[PathLike] = None,
    width: int = 600,
    height: Optional[int] = 300,
    theme: str = "default",
    time_course_mode: bool = False,
    tissue_filter: Optional[str] = None,
    subpopulation_filter: Optional[str] = None,
    user_group_labels: Optional[List[str]] = None,
    **kwargs
) -> Figure:
    """
    Create a visualization from flow cytometry data.
    
    This is the main high-level function for creating visualizations. It handles
    data loading, processing, and visualization creation in a single call.
    
    Args:
        data_source: Path to CSV file or pandas DataFrame
        metric: Specific metric to visualize (None for all)
        output_html: Path to save HTML output (optional)
        width: Plot width in pixels
        height: Plot height in pixels (None for dynamic)
        theme: Theme name ('default', 'scientific', 'publication', etc.)
        time_course_mode: Whether to create time-course visualization
        tissue_filter: Filter to specific tissue
        subpopulation_filter: Filter to specific subpopulation
        user_group_labels: Custom labels for groups
        **kwargs: Additional configuration parameters
        
    Returns:
        Plotly Figure object
        
    Raises:
        VisualizationError: If visualization creation fails
        FileNotFoundError: If input file doesn't exist
        ValueError: If parameters are invalid
        
    Examples:
        >>> # Basic usage
        >>> fig = create_visualization("data.csv", metric="Freq. of Parent")
        >>> fig.show()
        
        >>> # Time course analysis
        >>> fig = create_visualization(
        ...     "timecourse.csv",
        ...     metric="Freq. of Parent",
        ...     time_course_mode=True,
        ...     width=1200,
        ...     height=600
        ... )
        
        >>> # With filtering and custom labels
        >>> fig = create_visualization(
        ...     "data.csv",
        ...     tissue_filter="SP",
        ...     user_group_labels=["Control", "Treatment A", "Treatment B"],
        ...     theme="publication"
        ... )
    """
    # Initialize logging
    setup_logging(filemode='a')
    logger.debug(f"Creating visualization for {data_source}, metric={metric}")
    
    try:
        # Load data if path provided
        if isinstance(data_source, (str, Path)):
            data_path = Path(data_source)
            if not data_path.exists():
                raise FileNotFoundError(f"Data file does not exist: {data_path}")
            
            df, sid_col = load_and_parse_df(data_path)
            logger.info(f"Loaded data: {df.shape[0]} rows, {df.shape[1]} columns")
        else:
            # Assume it's a DataFrame
            df = data_source
            sid_col = 'SampleID'  # Default assumption
            if sid_col not in df.columns:
                # Try to find a suitable ID column
                id_candidates = [col for col in df.columns if 'id' in col.lower()]
                if id_candidates:
                    sid_col = id_candidates[0]
                else:
                    raise ValueError("No sample ID column found. DataFrame must have 'SampleID' column or similar.")
        
        # Preprocess data
        df = preprocess_flowcytometry_data(df, sid_col)
        
        # Validate time course mode
        if time_course_mode:
            has_time = "Time" in df.columns and df["Time"].notna().any()
            if not has_time:
                logger.warning("No time data available, falling back to standard mode")
                time_course_mode = False
        
        # Create configuration
        config = VisualizationConfig(
            metric=metric,
            width=width,
            height=height,
            theme=theme,
            time_course_mode=time_course_mode,
            tissue_filter=tissue_filter,
            subpopulation_filter=subpopulation_filter,
            user_group_labels=user_group_labels,
            **kwargs
        )
        
        # Validate configuration
        validation = ConfigurationValidator.validate_config(config)
        if not validation.valid:
            raise ValueError(f"Invalid configuration: {', '.join(validation.errors)}")
        
        # Process data
        processor = DataProcessor(df, sid_col, config)
        processed_data = processor.process()
        
        # Create visualization
        visualizer = Visualizer(config)
        fig = visualizer.create_figure(processed_data)
        
        # Save HTML if path provided
        if output_html:
            output_path = Path(output_html)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            fig.write_html(
                str(output_path),
                include_plotlyjs=True,
                full_html=True,
                config={
                    'editable': True,
                    'edits': {
                        'axisTitleText': True,
                        'titleText': True,
                        'legendText': True
                    }
                }
            )
            
            logger.info(f"Saved visualization to {output_path}")
        
        logger.info("Visualization created successfully")
        return fig
        
    except (FileNotFoundError, ValueError, VisualizationError):
        raise  # Re-raise expected exceptions
    except Exception as e:
        logger.error(f"Unexpected error creating visualization: {e}", exc_info=True)
        raise VisualizationError(f"Visualization creation failed: {str(e)}") from e


def create_quick_plot(
    df: DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    plot_type: str = "scatter",
    title: Optional[str] = None,
    theme: str = "default",
    **kwargs
) -> Figure:
    """
    Create a quick exploratory plot from DataFrame columns.
    
    This function provides a fast way to create simple plots for data exploration
    without the full flow cytometry processing pipeline.
    
    Args:
        df: Input DataFrame
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        color_col: Column name for color mapping (optional)
        size_col: Column name for size mapping (optional)
        plot_type: Type of plot ('scatter', 'bar', 'line', 'box', 'histogram')
        title: Plot title (optional)
        theme: Theme name
        **kwargs: Additional configuration parameters
        
    Returns:
        Plotly Figure object
        
    Examples:
        >>> # Scatter plot
        >>> fig = create_quick_plot(
        ...     df, 
        ...     x_col="Group", 
        ...     y_col="Freq. of Parent CD4",
        ...     color_col="Tissue",
        ...     plot_type="scatter"
        ... )
        
        >>> # Box plot
        >>> fig = create_quick_plot(
        ...     df,
        ...     x_col="Group",
        ...     y_col="Median CD4",
        ...     plot_type="box"
        ... )
    """
    try:
        # Validate inputs
        if df.empty:
            raise ValueError("DataFrame cannot be empty")
        
        missing_cols = [col for col in [x_col, y_col] if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns: {', '.join(missing_cols)}")
        
        # Use service for plot creation
        service = VisualizationService()
        
        # Prepare configuration
        plot_config = {
            'x': x_col,
            'y': y_col,
            'title': title or f"{y_col} vs {x_col}",
            'theme': theme,
            **kwargs
        }
        
        if color_col and color_col in df.columns:
            plot_config['color'] = color_col
        
        if size_col and size_col in df.columns:
            plot_config['size'] = size_col
        
        # Create plot
        fig = service.create_plot(df, plot_type, plot_config)
        
        logger.debug(f"Created quick {plot_type} plot: {x_col} vs {y_col}")
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create quick plot: {e}")
        raise VisualizationError(f"Quick plot creation failed: {str(e)}") from e


def create_time_course_visualization(
    data_source: Union[PathLike, DataFrame],
    metric: Optional[str] = None,
    output_html: Optional[PathLike] = None,
    width: int = 1200,
    height: int = 600,
    **kwargs
) -> Figure:
    """
    Create a time-course visualization optimized for temporal data.
    
    This is a convenience function that creates visualizations specifically
    optimized for time-course analysis.
    
    Args:
        data_source: Path to CSV file or pandas DataFrame
        metric: Specific metric to visualize
        output_html: Path to save HTML output
        width: Plot width (default: 1200 for time-course)
        height: Plot height (default: 600 for time-course)
        **kwargs: Additional configuration parameters
        
    Returns:
        Plotly Figure object
        
    Examples:
        >>> fig = create_time_course_visualization(
        ...     "timecourse_data.csv",
        ...     metric="Freq. of Parent",
        ...     output_html="timecourse_analysis.html"
        ... )
    """
    return create_visualization(
        data_source=data_source,
        metric=metric,
        output_html=output_html,
        width=width,
        height=height,
        time_course_mode=True,
        show_individual_points=True,
        theme="scientific",
        **kwargs
    )


def create_publication_figure(
    data_source: Union[PathLike, DataFrame],
    metric: str,
    output_path: Optional[PathLike] = None,
    width: int = 800,
    height: int = 600,
    format: str = "svg",
    **kwargs
) -> Figure:
    """
    Create a publication-ready figure with optimized styling.
    
    Args:
        data_source: Path to CSV file or pandas DataFrame
        metric: Specific metric to visualize
        output_path: Path to save output file
        width: Plot width
        height: Plot height
        format: Output format ('svg', 'png', 'pdf')
        **kwargs: Additional configuration parameters
        
    Returns:
        Plotly Figure object
        
    Examples:
        >>> fig = create_publication_figure(
        ...     "data.csv",
        ...     metric="Freq. of Parent",
        ...     output_path="figure1.svg",
        ...     format="svg"
        ... )
    """
    fig = create_visualization(
        data_source=data_source,
        metric=metric,
        width=width,
        height=height,
        theme="publication",
        show_individual_points=False,
        error_bars=True,
        interactive=False,
        **kwargs
    )
    
    # Save in requested format if path provided
    if output_path and format != "html":
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "svg":
            fig.write_image(str(output_path), format="svg")
        elif format == "png":
            fig.write_image(str(output_path), format="png", scale=2)  # High DPI
        elif format == "pdf":
            fig.write_image(str(output_path), format="pdf")
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved publication figure to {output_path}")
    
    return fig


def batch_create_visualizations(
    data_sources: List[Union[PathLike, DataFrame]],
    output_dir: PathLike,
    config: Optional[VisualizationConfig] = None,
    **kwargs
) -> List[VisualizationResult]:
    """
    Create visualizations for multiple data sources in batch.
    
    Args:
        data_sources: List of data sources (file paths or DataFrames)
        output_dir: Directory to save output files
        config: Shared configuration (optional)
        **kwargs: Configuration parameters (if config not provided)
        
    Returns:
        List of VisualizationResult objects
        
    Examples:
        >>> results = batch_create_visualizations(
        ...     ["data1.csv", "data2.csv", "data3.csv"],
        ...     output_dir="batch_results",
        ...     metric="Freq. of Parent",
        ...     theme="publication"
        ... )
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Use provided config or create from kwargs
    if config is None:
        config = VisualizationConfig(**kwargs)
    
    for i, data_source in enumerate(data_sources):
        try:
            # Generate output filename
            if isinstance(data_source, (str, Path)):
                source_name = Path(data_source).stem
            else:
                source_name = f"data_{i+1}"
            
            output_file = output_path / f"{source_name}_visualization.html"
            
            # Create visualization
            fig = create_visualization(
                data_source=data_source,
                output_html=output_file,
                **config.__dict__
            )
            
            # Create result
            result = VisualizationResult(
                figure=fig,
                metadata={
                    'source': str(data_source),
                    'output_file': str(output_file),
                    'batch_index': i
                }
            )
            
            results.append(result)
            logger.info(f"Created visualization {i+1}/{len(data_sources)}: {source_name}")
            
        except Exception as e:
            logger.error(f"Failed to create visualization for {data_source}: {e}")
            # Create error result
            error_result = VisualizationResult(
                figure=go.Figure(),  # Empty figure
                metadata={
                    'source': str(data_source),
                    'error': str(e),
                    'batch_index': i
                },
                warnings=[f"Failed to process: {str(e)}"]
            )
            results.append(error_result)
    
    logger.info(f"Batch processing completed: {len(results)} results")
    return results


def validate_data_for_visualization(
    data_source: Union[PathLike, DataFrame],
    config: Optional[VisualizationConfig] = None
) -> Dict[str, Any]:
    """
    Validate data and configuration for visualization creation.
    
    This function performs comprehensive validation without creating the
    actual visualization, useful for checking data quality and compatibility.
    
    Args:
        data_source: Path to CSV file or pandas DataFrame
        config: Visualization configuration (optional)
        
    Returns:
        Dictionary with validation results and recommendations
        
    Examples:
        >>> validation = validate_data_for_visualization("data.csv")
        >>> if validation['valid']:
        ...     print("Data is ready for visualization")
        >>> else:
        ...     print("Issues found:", validation['issues'])
    """
    try:
        # Load data if needed
        if isinstance(data_source, (str, Path)):
            # Validate file first
            file_validation = ConfigurationValidator.validate_file_path(data_source)
            if not file_validation.valid:
                return {
                    'valid': False,
                    'issues': file_validation.errors,
                    'warnings': file_validation.warnings
                }
            
            df, sid_col = load_and_parse_df(data_source)
        else:
            df = data_source
            sid_col = 'SampleID'
        
        # Validate configuration if provided
        config_issues = []
        config_warnings = []
        
        if config:
            config_validation = ConfigurationValidator.validate_config(config)
            config_issues.extend(config_validation.errors)
            config_warnings.extend(config_validation.warnings)
        
        # Validate data structure
        from .data_processor import DataProcessor
        data_warnings = DataProcessor.validate_data_for_processing(df, sid_col)
        
        # Detect data characteristics
        from .data_processor import detect_data_characteristics
        characteristics = detect_data_characteristics(df)
        
        # Generate recommendations
        recommendations = []
        
        if characteristics['has_time_data']:
            recommendations.append("Consider using time_course_mode=True for temporal analysis")
        
        if characteristics['num_groups'] > 6:
            recommendations.append("Consider using a wider plot (width > 1000) for many groups")
        
        if characteristics['missing_data_percentage'] > 10:
            recommendations.append("High percentage of missing data may affect results")
        
        # Suggest optimal configuration
        suggested_config = ConfigurationValidator.suggest_config_for_data(
            data_shape=df.shape,
            has_time_data=characteristics['has_time_data'],
            num_groups=characteristics['num_groups'],
            num_tissues=characteristics['num_tissues']
        )
        
        return {
            'valid': len(config_issues) == 0,
            'issues': config_issues,
            'warnings': config_warnings + data_warnings,
            'data_characteristics': characteristics,
            'recommendations': recommendations,
            'suggested_config': suggested_config.__dict__
        }
        
    except Exception as e:
        return {
            'valid': False,
            'issues': [f"Validation failed: {str(e)}"],
            'warnings': [],
            'error': str(e)
        }


# Convenience functions for common use cases
def quick_scatter_plot(df: DataFrame, x: str, y: str, **kwargs) -> Figure:
    """Quick scatter plot creation."""
    return create_quick_plot(df, x, y, plot_type="scatter", **kwargs)


def quick_bar_plot(df: DataFrame, x: str, y: str, **kwargs) -> Figure:
    """Quick bar plot creation."""
    return create_quick_plot(df, x, y, plot_type="bar", **kwargs)


def quick_line_plot(df: DataFrame, x: str, y: str, **kwargs) -> Figure:
    """Quick line plot creation."""
    return create_quick_plot(df, x, y, plot_type="line", **kwargs)


def quick_box_plot(df: DataFrame, x: str, y: str, **kwargs) -> Figure:
    """Quick box plot creation."""
    return create_quick_plot(df, x, y, plot_type="box", **kwargs)


# Legacy compatibility function
def visualize_data(
    csv_path: PathLike,
    output_html: PathLike,
    metric: Optional[str] = None,
    width: int = 600,
    height: Optional[int] = None,
    theme: str = "default",
    time_course_mode: bool = False,
    user_replicates: Optional[List[int]] = None,
    auto_parse_groups: bool = True,
    user_group_labels: Optional[List[str]] = None,
    tissue_filter: Optional[str] = None,
    subpopulation_filter: Optional[str] = None
) -> Figure:
    """
    Legacy compatibility function for the original visualize_data API.
    
    This function maintains compatibility with existing code while
    using the new modular architecture under the hood.
    
    Args:
        csv_path: Path to input CSV file
        output_html: Path for output HTML file
        metric: Specific metric to visualize
        width: Plot width in pixels
        height: Plot height in pixels
        theme: Theme name
        time_course_mode: Whether to use time-course visualization
        user_replicates: User-defined replicates (deprecated)
        auto_parse_groups: Whether to auto-parse groups (deprecated)
        user_group_labels: User-defined group labels
        tissue_filter: Tissue filter
        subpopulation_filter: Subpopulation filter
        
    Returns:
        Plotly Figure object
    """
    import warnings
    warnings.warn(
        "visualize_data() is deprecated. Use create_visualization() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return create_visualization(
        data_source=csv_path,
        metric=metric,
        output_html=output_html,
        width=width,
        height=height,
        theme=theme,
        time_course_mode=time_course_mode,
        user_group_labels=user_group_labels,
        tissue_filter=tissue_filter,
        subpopulation_filter=subpopulation_filter
    )
