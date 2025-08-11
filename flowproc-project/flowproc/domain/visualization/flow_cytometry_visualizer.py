"""
Simple Visualizer - Minimal Interface for Flow Cytometry Visualization (Refactored)

This module provides a super simple interface for creating visualizations
without the complexity of the full system. Just 3 main functions for 90% of use cases.

This is the refactored version that uses modular components.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Union

from .column_utils import detect_flow_columns
from .plot_creators import create_single_metric_plot, create_cell_type_comparison_plot, create_basic_plot
from .time_plots import time_plot, time_plot_faceted
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
            elif flow_cols['counts']:
                y = flow_cols['counts'][0]
            elif flow_cols['geometric_means']:
                y = flow_cols['geometric_means'][0]
            elif flow_cols['cvs']:
                y = flow_cols['cvs'][0]
            elif flow_cols['mads']:
                y = flow_cols['mads'][0]
            else:
                # Fallback to any column that's not metadata
                metadata_cols = ['SampleID', 'Group', 'Animal', 'Well', 'Time', 'Replicate', 'Tissue']
                non_metadata_cols = [col for col in df.columns if col not in metadata_cols]
                if non_metadata_cols:
                    y = non_metadata_cols[0]
                else:
                    y = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # For flow cytometry data, aggregate by Group and show Mean+/-SEM
    if x == 'Group' and 'Group' in df.columns:
        # Check if y is a metric type (like "Freq. of Parent") or a specific column
        from .column_utils import detect_available_metric_types, get_matching_columns_for_metric
        
        available_metric_types = detect_available_metric_types(df)
        if y in available_metric_types:
            # Find all columns matching this metric type using the new dynamic function
            matching_cols = get_matching_columns_for_metric(df, y)
            
            # Debug logging
            logger.debug(f"Looking for metric type '{y}', found matching columns: {matching_cols}")
            
            if matching_cols:
                # Always use cell type comparison plot for consistent multi-subpopulation display
                fig = create_cell_type_comparison_plot(df, matching_cols, plot_type, **kwargs)
            else:
                # No matching columns found - try to find any frequency column as fallback
                logger.warning(f"No columns found matching metric type '{y}'. Available columns: {list(df.columns)}")
                freq_cols = [col for col in df.columns if 'freq' in col.lower()]
                if freq_cols:
                    logger.info(f"Using fallback frequency columns: {freq_cols}")
                    fig = create_cell_type_comparison_plot(df, freq_cols, plot_type, **kwargs)
                else:
                    # Last resort - use all non-metadata columns
                    metadata_cols = ['SampleID', 'Group', 'Animal', 'Well', 'Time', 'Replicate', 'Tissue']
                    non_metadata_cols = [col for col in df.columns if col not in metadata_cols]
                    if non_metadata_cols:
                        logger.info(f"Using fallback columns: {non_metadata_cols}")
                        fig = create_cell_type_comparison_plot(df, non_metadata_cols, plot_type, **kwargs)
                    else:
                        raise ValueError(f"No suitable columns found for metric type '{y}'. Available: {list(df.columns)}")
        else:
            # Specific column - find all similar columns for consistent display
            if y not in df.columns:
                raise ValueError(f"Column '{y}' not found. Available: {list(df.columns)}")
            
            # Try to find related columns for multi-subpopulation display
            related_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['freq', 'mean', 'median', 'count']) and col != y]
            if related_cols:
                all_cols = [y] + related_cols
                logger.info(f"Found related columns for '{y}': {all_cols}")
                fig = create_cell_type_comparison_plot(df, all_cols, plot_type, **kwargs)
            else:
                # Single column fallback - still use comparison plot for consistency
                fig = create_cell_type_comparison_plot(df, [y], plot_type, **kwargs)
        
        # Apply standardized legend configuration to Group plots as well
        color_col = kwargs.get('color')
        width = kwargs.get('width')
        height = kwargs.get('height')
        fig = configure_legend(fig, df, color_col, is_subplot=False, width=width, height=height)
    else:
        # For non-Group plots, use original data
        fig = create_basic_plot(df, x, y, plot_type, filter_options=filter_options, **kwargs)
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved plot to {save_html}")
    
    return fig


def compare_groups(data: Union[str, DataFrame],
                  groups: Optional[List[str]] = None,
                  metric: Optional[str] = None,
                  plot_type: str = "box",
                  save_html: Optional[str] = None,
                  **kwargs):
    """
    Compare multiple groups for a specific metric.
    
    Args:
        data: CSV file path or DataFrame
        groups: List of group names to compare (auto-detected if None)
        metric: Metric column to compare (auto-detected if None)
        plot_type: 'box', 'bar', or 'scatter'
        save_html: Optional path to save HTML file
    
    Returns:
        Plotly Figure object
    
    Examples:
        >>> fig = compare_groups("data.csv")
        >>> fig.show()
    """
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        # Use the proper parsing logic to detect Group column
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect metric if not provided
    if metric is None:
        flow_cols = detect_flow_columns(df)
        metric = flow_cols['frequencies'][0] if flow_cols['frequencies'] else df.columns[0]
    
    # For flow cytometry data, each row is typically a sample
    # Create sample groups if not provided
    if groups is None:
        df = df.copy()
        df['Sample_Group'] = [f'Sample_{i+1}' for i in range(len(df))]
        group_col = 'Sample_Group'
    else:
        # Filter to specified groups if provided
        df_filtered = df[df['Group'].isin(groups)]
        if df_filtered.empty:
            raise ValueError(f"No data found for groups: {groups}")
        df = df_filtered
        group_col = 'Group'
    
    # Create comparison plot
    if plot_type == "box":
        fig = create_basic_plot(df, group_col, metric, "box", filter_options=filter_options, **kwargs)
    elif plot_type == "bar":
        fig = create_basic_plot(df, group_col, metric, "bar", filter_options=filter_options, **kwargs)
    elif plot_type == "scatter":
        fig = create_basic_plot(df, group_col, metric, "scatter", filter_options=filter_options, **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration  
    width = kwargs.get('width')
    height = kwargs.get('height')
    fig = configure_legend(fig, df, None, is_subplot=False, width=width, height=height)
    
    # Create comprehensive title with metric, tissue, and timepoint info
    from .column_utils import create_comprehensive_plot_title
    comprehensive_title = create_comprehensive_plot_title(df, metric, filter_options=filter_options)
    
    fig.update_layout(
        title=comprehensive_title,
        xaxis_title="Group",
        yaxis_title=metric
    )
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved comparison plot to {save_html}")
    
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


# Time plot functions already imported at top

__all__ = [
    'plot',
    'time_plot', 
    'time_plot_faceted',
    'compare_groups',
    'scatter',
    'bar', 
    'box',
    'histogram'
] 