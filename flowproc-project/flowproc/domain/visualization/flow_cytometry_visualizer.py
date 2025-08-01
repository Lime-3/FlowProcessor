"""
Flow Cytometry Visualizer - Main Interface for Flow Cytometry Visualization

This module provides the main interface for creating flow cytometry visualizations.
It offers a clean, high-level API that handles 90% of common visualization needs
while delegating to specialized modules for specific functionality.

Key Functions:
- plot(): Main plotting function with auto-detection
- time_plot(): Time course visualization
- compare_groups(): Group comparison plots
- Convenience functions: scatter(), bar(), box(), histogram()

This module uses a modular architecture with specialized components for:
- Column detection and analysis
- Plot creation and styling
- Legend configuration
- Data aggregation and processing
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
            # Prioritize "Freq. of Parent" as default y-axis for flow cytometry data
            freq_parent_cols = [col for col in flow_cols['frequencies'] if 'freq. of parent' in col.lower()]
            if freq_parent_cols:
                y = freq_parent_cols[0]
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
        metric_types = ['Freq. of Parent', 'Freq. of Total', 'Count', 'Median', 'Mean', 'Geometric Mean', 'Mode', 'CV', 'MAD']
        if y in metric_types:
            # Find all columns matching this metric type
            matching_cols = [col for col in df.columns if y.lower() in col.lower()]
            
            # Debug logging
            logger.debug(f"Looking for metric type '{y}', found matching columns: {matching_cols}")
            
            if len(matching_cols) > 1:
                # Create a combined plot with all matching columns
                fig = create_cell_type_comparison_plot(df, matching_cols, plot_type, **kwargs)
            elif len(matching_cols) == 1:
                # Single column - use normal aggregation
                fig = create_single_metric_plot(df, matching_cols[0], plot_type, **kwargs)
            else:
                # No matching columns found - try to find any frequency column as fallback
                logger.warning(f"No columns found matching metric type '{y}'. Available columns: {list(df.columns)}")
                freq_cols = [col for col in df.columns if 'freq' in col.lower()]
                if freq_cols:
                    logger.info(f"Using fallback frequency column: {freq_cols[0]}")
                    fig = create_single_metric_plot(df, freq_cols[0], plot_type, **kwargs)
                else:
                    # Last resort - use first non-metadata column
                    metadata_cols = ['SampleID', 'Group', 'Animal', 'Well', 'Time', 'Replicate', 'Tissue']
                    non_metadata_cols = [col for col in df.columns if col not in metadata_cols]
                    if non_metadata_cols:
                        logger.info(f"Using fallback column: {non_metadata_cols[0]}")
                        fig = create_single_metric_plot(df, non_metadata_cols[0], plot_type, **kwargs)
                    else:
                        raise ValueError(f"No suitable columns found for metric type '{y}'. Available: {list(df.columns)}")
        else:
            # Specific column - use normal aggregation
            # Validate column exists
            if y not in df.columns:
                raise ValueError(f"Column '{y}' not found. Available: {list(df.columns)}")
            fig = create_single_metric_plot(df, y, plot_type, **kwargs)
        
        # Apply standardized legend configuration to Group plots as well
        color_col = kwargs.get('color')
        fig = configure_legend(fig, df, color_col, **kwargs)
    else:
        # For non-Group plots, use original data
        fig = create_basic_plot(df, x, y, plot_type, **kwargs)
    
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
        fig = create_basic_plot(df, group_col, metric, "box", **kwargs)
    elif plot_type == "bar":
        fig = create_basic_plot(df, group_col, metric, "bar", **kwargs)
    elif plot_type == "scatter":
        fig = create_basic_plot(df, group_col, metric, "scatter", **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration
    fig = configure_legend(fig, df, None, **kwargs)
    
    fig.update_layout(
        title=f"{metric} Comparison Across Groups",
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


# Re-export time plot functions for convenience
from .time_plots import time_plot, time_plot_faceted

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