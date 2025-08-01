"""
Core plot creation functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import plotly.express as px
from typing import Optional, List

from .legend_config import configure_legend, apply_default_layout
from .data_aggregation import aggregate_by_group_with_sem, aggregate_multiple_metrics_by_group
from .column_utils import extract_cell_type_name

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame


def create_single_metric_plot(df: DataFrame, y_col: str, plot_type: str, **kwargs):
    """
    Create a plot for a single metric with aggregation.
    
    Args:
        df: DataFrame containing the data
        y_col: Column to plot on y-axis
        plot_type: Type of plot ('scatter', 'bar', 'box', 'line', 'histogram')
        **kwargs: Additional keyword arguments
        
    Returns:
        Plotly Figure object
    """
    # Aggregate data by Group
    agg_df = aggregate_by_group_with_sem(df, y_col)
    
    # Create plot based on type with error bars
    if plot_type == "scatter":
        fig = px.scatter(agg_df, x='Group', y='mean', error_y='sem', **kwargs)
    elif plot_type == "bar":
        fig = px.bar(agg_df, x='Group', y='mean', error_y='sem', **kwargs)
    elif plot_type == "box":
        # For box plots, use original data to show distribution
        fig = px.box(df, x='Group', y=y_col, **kwargs)
    elif plot_type == "line":
        fig = px.line(agg_df, x='Group', y='mean', error_y='sem', **kwargs)
    elif plot_type == "histogram":
        fig = px.histogram(df, x=y_col, **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration to ALL plot types
    color_col = kwargs.get('color')
    width = kwargs.get('width')
    height = kwargs.get('height')
    fig = configure_legend(fig, df, color_col, is_subplot=False, width=width, height=height)
        
    # Update y-axis title to show it's mean with error bars
    if 'title' not in kwargs:
        fig.update_layout(title=f"Mean {y_col} ± SEM by Group")
    
    return fig


def create_cell_type_comparison_plot(df: DataFrame, freq_cols: List[str], plot_type: str, **kwargs):
    """
    Create a plot comparing all cell types with cell types in legend.
    
    Args:
        df: DataFrame containing the data
        freq_cols: List of frequency columns to compare
        plot_type: Type of plot ('scatter', 'bar', 'box', 'line', 'histogram')
        **kwargs: Additional keyword arguments
        
    Returns:
        Plotly Figure object
    """
    # Prepare data for plotting all cell types together
    combined_df = aggregate_multiple_metrics_by_group(df, freq_cols)
    
    # Create plot with cell types in legend
    if plot_type == "scatter":
        fig = px.scatter(combined_df, x='Group', y='mean', color='Cell Type', error_y='sem', **kwargs)
    elif plot_type == "bar":
        fig = px.bar(combined_df, x='Group', y='mean', color='Cell Type', error_y='sem', barmode='group', **kwargs)
    elif plot_type == "box":
        # For box plots, use original data
        melted_df = df.melt(id_vars=['Group'], value_vars=freq_cols, 
                           var_name='Cell Type', value_name='Frequency')
        melted_df['Cell Type'] = melted_df['Cell Type'].apply(extract_cell_type_name)
        fig = px.box(melted_df, x='Group', y='Frequency', color='Cell Type', **kwargs)
    elif plot_type == "line":
        fig = px.line(combined_df, x='Group', y='mean', color='Cell Type', error_y='sem', **kwargs)
    elif plot_type == "histogram":
        # For histogram, use original data
        melted_df = df.melt(id_vars=['Group'], value_vars=freq_cols, 
                           var_name='Cell Type', value_name='Frequency')
        melted_df['Cell Type'] = melted_df['Cell Type'].apply(extract_cell_type_name)
        fig = px.histogram(melted_df, x='Frequency', color='Cell Type', **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration to ALL plot types
    width = kwargs.get('width')
    height = kwargs.get('height')
    fig = configure_legend(fig, combined_df, 'Cell Type', is_subplot=False, width=width, height=height)
        
    # Update title
    if 'title' not in kwargs:
        fig.update_layout(title=f"Cell Type Comparison by Group")
    
    return fig


def create_time_course_single_plot(df: DataFrame, time_col: str, value_col: str, 
                                 group_col: Optional[str], sample_size: Optional[int] = None, **kwargs):
    """
    Create a single time course plot with optional grouping.
    
    Args:
        df: DataFrame containing the data
        time_col: Time column name
        value_col: Value column to plot
        group_col: Optional group column for color coding
        sample_size: Optional sample size for large datasets
        **kwargs: Additional keyword arguments
        
    Returns:
        Plotly Figure object
    """
    # Sample data if specified
    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
    
    # Create time course plot
    if group_col and group_col in df.columns:
        fig = px.line(df, x=time_col, y=value_col, color=group_col, **kwargs)
    else:
        fig = px.line(df, x=time_col, y=value_col, **kwargs)
    
    # Apply standardized legend configuration
    width = kwargs.get('width')
    height = kwargs.get('height')
    fig = configure_legend(fig, df, group_col, is_subplot=False, width=width, height=height)
    
    # Update title
    if 'title' not in kwargs:
        title = f"{value_col} over Time"
        if group_col:
            title += f" by {group_col}"
        fig.update_layout(title=title)
    
    return fig


def create_basic_plot(df: DataFrame, x: str, y: str, plot_type: str, **kwargs):
    """
    Create a basic plot without aggregation.
    
    Args:
        df: DataFrame containing the data
        x: Column for x-axis
        y: Column for y-axis
        plot_type: Type of plot ('scatter', 'bar', 'box', 'line', 'histogram')
        **kwargs: Additional keyword arguments
        
    Returns:
        Plotly Figure object
    """
    # Create plot based on type
    if plot_type == "scatter":
        fig = px.scatter(df, x=x, y=y, **kwargs)
    elif plot_type == "bar":
        fig = px.bar(df, x=x, y=y, **kwargs)
    elif plot_type == "box":
        fig = px.box(df, x=x, y=y, **kwargs)
    elif plot_type == "line":
        fig = px.line(df, x=x, y=y, **kwargs)
    elif plot_type == "histogram":
        fig = px.histogram(df, x=y, **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration
    color_col = kwargs.get('color')
    width = kwargs.get('width')
    height = kwargs.get('height')
    fig = configure_legend(fig, df, color_col, is_subplot=False, width=width, height=height)
    
    # Update title
    if 'title' not in kwargs:
        fig.update_layout(title=f"{y} vs {x}")
    
    return fig 