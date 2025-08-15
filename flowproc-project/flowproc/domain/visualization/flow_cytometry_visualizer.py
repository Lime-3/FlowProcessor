"""
Visualizer -  Interface for Flow Cytometry Visualization

"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Union

from .column_utils import detect_flow_columns, analyze_data_size, extract_metric_name, create_comprehensive_plot_title
from .plot_creators import create_single_metric_plot, create_cell_type_comparison_plot, create_basic_plot
from .plot_config import DEFAULT_WIDTH, DEFAULT_HEIGHT
# Legacy timecourse functions removed - use create_timecourse_visualization from time_plots module directly
from .faceted_plots import create_cell_type_faceted_plot
from .legend_config import configure_legend

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame


def plot(data: Union[str, DataFrame], 
         x: Optional[str] = None, 
         y: Optional[str] = None,
         plot_type: str = "scatter",
         save_html: Optional[str] = None,
         filter_options=None,
         **kwargs):
    """
    Simple plotting function - handles 90% of visualization needs.
    
    Args:
        data: CSV file path or DataFrame
        x: X-axis column name (auto-detected if None)
        y: Y-axis column name (auto-detected if None)
        plot_type: 'scatter', 'bar', 'box', 'line', 'histogram'
        save_html: Optional path to save HTML file
        **kwargs: Additional plotly parameters
    
    Returns:
        Plotly Figure object
    
    Examples:
        >>> # Basic scatter plot (auto-detects columns)
        >>> fig = plot("data.csv")
        >>> fig.show()
        
        >>> # Box plot with custom title
        >>> fig = plot(df, x="Tissue", y="Median CD4", plot_type="box", 
        ...           title="CD4 Expression by Tissue")
        
        >>> # Save to HTML
        >>> fig = plot("data.csv", save_html="output.html")
    """
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        # Use the proper parsing logic to detect Group column
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect columns for flow cytometry data
    if x is None or y is None:
        flow_cols = detect_flow_columns(df)
        
        # Debug logging
        logger.debug(f"Detected flow columns: {flow_cols}")
        logger.debug(f"Available columns: {list(df.columns)}")
        
        if x is None:
            # Prioritize Group column as default x-axis for flow cytometry data
            if 'Group' in df.columns:
                x = 'Group'
            elif 'group' in df.columns:
                x = 'group'
            elif flow_cols['frequencies']:
                x = flow_cols['frequencies'][0]
            else:
                x = df.columns[0] if len(df.columns) > 0 else "Sample"
        
        if y is None:
            # Prioritize "Freq. of Parent" or "Freq. of Live" as default y-axis for flow cytometry data
            freq_parent_cols = [col for col in flow_cols['frequencies'] if 'freq. of parent' in col.lower()]
            freq_live_cols = [col for col in flow_cols['frequencies'] if 'freq. of live' in col.lower()]
            
            if freq_parent_cols:
                y = freq_parent_cols[0]
            elif freq_live_cols:
                y = freq_live_cols[0]
            elif flow_cols['frequencies']:
                y = flow_cols['frequencies'][0]
            elif flow_cols['medians']:
                y = flow_cols['medians'][0]
            elif flow_cols['means']:
                y = flow_cols['means'][0]
            else:
                y = df.columns[1] if len(df.columns) > 1 else "Value"
    
    # Ensure consistent sizing using centralized defaults
    if 'width' not in kwargs:
        kwargs['width'] = DEFAULT_WIDTH
    if 'height' not in kwargs:
        kwargs['height'] = DEFAULT_HEIGHT
    
    # Create plot based on type
    # Check if y is a metric type (like "Freq. of Parent") or a specific column
    from .column_utils import detect_available_metric_types, get_matching_columns_for_metric
    metric_types = detect_available_metric_types(df)
    
    if y in metric_types:
        # Find all columns matching this metric type
        matching_cols = get_matching_columns_for_metric(df, y)
        
        # Debug logging
        logger.debug(f"Looking for metric type '{y}', found matching columns: {matching_cols}")
        
        if matching_cols:
            if len(matching_cols) > 1:
                # Multiple columns found - use cell type comparison plot for standard mode
                # This will show groups on x-axis and populations in legend
                logger.info(f"Multiple columns found for metric type '{y}', using cell type comparison plot")
                from .plot_creators import create_cell_type_comparison_plot
                
                if plot_type == "scatter":
                    fig = create_cell_type_comparison_plot(df, matching_cols, "scatter", filter_options=filter_options, **kwargs)
                elif plot_type == "bar":
                    fig = create_cell_type_comparison_plot(df, matching_cols, "bar", filter_options=filter_options, **kwargs)
                elif plot_type == "box":
                    fig = create_cell_type_comparison_plot(df, matching_cols, "box", filter_options=filter_options, **kwargs)
                elif plot_type == "line":
                    fig = create_cell_type_comparison_plot(df, matching_cols, "line", filter_options=filter_options, **kwargs)
                elif plot_type == "histogram":
                    fig = create_cell_type_comparison_plot(df, matching_cols, "histogram", filter_options=filter_options, **kwargs)
                else:
                    raise ValueError(f"Unknown plot type: {plot_type}")
                
                # Save if requested
                if save_html:
                    from .plotly_renderer import PlotlyRenderer
                    renderer = PlotlyRenderer()
                    renderer.export_to_html_optimized(fig, save_html, 'minimal')
                    logger.info(f"Saved cell type comparison plot to {save_html}")
                
                return fig
            else:
                # Single column found - use single metric plot
                y = matching_cols[0]
                logger.info(f"Single column found for metric type '{y}', using single metric plot: {y}")
        else:
            # Fallback to first available frequency column
            if flow_cols['frequencies']:
                y = flow_cols['frequencies'][0]
                logger.warning(f"No columns found for metric type '{y}', using fallback: {y}")
            else:
                raise ValueError(f"No columns found for metric type '{y}' and no fallback columns available")
    
    # Validate that y exists in DataFrame columns for single-column modes
    if y not in df.columns:
        raise ValueError(f"Invalid metric '{y}'")

    # Create plot based on type (for single column or specific column)
    if plot_type == "scatter":
        fig = create_single_metric_plot(df, y, "scatter", filter_options=filter_options, **kwargs)
    elif plot_type == "bar":
        fig = create_single_metric_plot(df, y, "bar", filter_options=filter_options, **kwargs)
    elif plot_type == "box":
        fig = create_single_metric_plot(df, y, "box", filter_options=filter_options, **kwargs)
    elif plot_type == "line":
        fig = create_single_metric_plot(df, y, "line", filter_options=filter_options, **kwargs)
    elif plot_type == "histogram":
        fig = create_basic_plot(df, x, y, "histogram", filter_options=filter_options, **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved plot to {save_html}")
    
    return fig


def compare_groups(data, groups: Optional[List[str]] = None,
                  metric: Optional[str] = None,
                  plot_type: str = "box",
                  save_html: Optional[str] = None,
                  filter_options=None,
                  **kwargs):
    """
    Compare groups using a specific metric.
    
    Args:
        data: CSV file path or DataFrame
        groups: List of groups to compare (auto-detected if None)
        metric: Metric to compare (auto-detected if None)
        plot_type: Type of plot ('scatter', 'bar', 'box', 'line')
        save_html: Optional path to save HTML file
        filter_options: Optional filter options
        **kwargs: Additional plotly parameters
    
    Returns:
        Plotly Figure object
    """
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect groups and metric
    if groups is None:
        if 'Group' in df.columns:
            groups = sorted(df['Group'].unique())
        else:
            groups = ['Group 1', 'Group 2']  # Default fallback
    
    if metric is None:
        flow_cols = detect_flow_columns(df)
        if flow_cols['frequencies']:
            metric = flow_cols['frequencies'][0]
        elif flow_cols['medians']:
            metric = flow_cols['medians'][0]
        else:
            metric = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Ensure consistent sizing using centralized defaults
    if 'width' not in kwargs:
        kwargs['width'] = DEFAULT_WIDTH
    if 'height' not in kwargs:
        kwargs['height'] = DEFAULT_HEIGHT
    
    # Check if metric is a metric type (like "Freq. of Parent") or a specific column
    from .column_utils import detect_available_metric_types, get_matching_columns_for_metric
    metric_types = detect_available_metric_types(df)
    
    if metric in metric_types:
        # Find all columns matching this metric type
        matching_cols = get_matching_columns_for_metric(df, metric)
        
        # Debug logging
        logger.debug(f"Looking for metric type '{metric}', found matching columns: {matching_cols}")
        
        if matching_cols:
            # Use the first matching column for single metric plots
            metric = matching_cols[0]
            logger.info(f"Using column '{metric}' for metric type '{metric}'")
        else:
            # Fallback to first available frequency column
            flow_cols = detect_flow_columns(df)
            if flow_cols['frequencies']:
                metric = flow_cols['frequencies'][0]
                logger.warning(f"No columns found for metric type '{metric}', using fallback: {metric}")
            else:
                raise ValueError(f"No columns found for metric type '{metric}' and no fallback columns available")
    
    # Create comparison plot
    if plot_type == "box":
        fig = create_basic_plot(df, 'Group', metric, "box", filter_options=filter_options, **kwargs)
    elif plot_type == "bar":
        fig = create_basic_plot(df, 'Group', metric, "bar", filter_options=filter_options, **kwargs)
    elif plot_type == "scatter":
        fig = create_basic_plot(df, 'Group', metric, "scatter", filter_options=filter_options, **kwargs)
    else:
        raise ValueError(f"Unsupported plot type for group comparison: {plot_type}")
    
    # Update title
    if 'title' not in kwargs:
        metric_name = extract_metric_name(metric)
        comprehensive_title = create_comprehensive_plot_title(df, metric_name, filter_options=filter_options)
        fig.update_layout(title=f"{comprehensive_title} by Group")
    
    # Save if requested
    if save_html:
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved group comparison plot to {save_html}")
    
    return fig


# Convenience functions for common use cases
def scatter(data, x=None, y=None, **kwargs):
    """Quick scatter plot."""
    return plot(data, x=x, y=y, plot_type="scatter", **kwargs)


def bar(data, x=None, y=None, **kwargs):
    """Quick bar plot."""
    return plot(data, x=x, y=y, plot_type="bar", **kwargs)


def box(data, x=None, y=None, **kwargs):
    """Quick box plot."""
    return plot(data, x=x, y=y, plot_type="box", **kwargs)


def histogram(data, x=None, **kwargs):
    """Quick histogram."""
    return plot(data, x=x, y=x, plot_type="histogram", **kwargs)


# Legacy time_plot and time_plot_faceted functions have been removed
# Use create_timecourse_visualization from time_plots module instead


__all__ = [
    'plot',
    'compare_groups',
    'scatter',
    'bar', 
    'box',
    'histogram'
] 