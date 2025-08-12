"""
Core plot creation functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import plotly.express as px
from typing import Optional, List

from .legend_config import configure_legend
from .data_aggregation import aggregate_by_group_with_sem, aggregate_multiple_metrics_by_group
from .column_utils import extract_cell_type_name, extract_metric_name, create_comprehensive_plot_title

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame


def create_single_metric_plot(df: DataFrame, y_col: str, plot_type: str, filter_options=None, **kwargs):
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

    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration to ALL plot types
    color_col = kwargs.get('color')
    width = kwargs.get('width', 1200)  # Use default width if not specified
    height = kwargs.get('height', 500)  # Use default height if not specified (reduced from 700 for better aspect ratio)
    
    # Determine appropriate legend title based on plot type
    legend_title = "Groups" if color_col else "Populations"
    
    fig = configure_legend(
        fig, df, color_col, is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
        
    # Update title, y-axis title and legend title
    if 'title' not in kwargs:
        metric_name = extract_metric_name(y_col)
        logger.debug(f"Single metric plot - Creating title with metric: {metric_name}")
        comprehensive_title = create_comprehensive_plot_title(df, metric_name, [y_col], filter_options=filter_options)
        logger.debug(f"Single metric plot - Comprehensive title created: {comprehensive_title}")
        fig.update_layout(
            title=comprehensive_title,
            yaxis_title=metric_name,
            legend_title="Mean ± SEM"
        )
        
        # Debug: Verify the title was applied
        if hasattr(fig.layout, 'title') and hasattr(fig.layout.title, 'text'):
            logger.info(f"Title applied successfully to single metric plot: '{fig.layout.title.text}'")
        else:
            logger.warning("Title not found in single metric plot layout after update")
    
    # Ensure consistent sizing
    fig.update_layout(
        width=width,
        height=height
    )
    
    # Ensure all x-axis ticks are shown with correct group numbers
    if 'Group' in df.columns:
        # Convert group values to numeric if they're strings representing numbers
        unique_groups = df['Group'].unique()
        try:
            # Try to convert to numeric and sort
            numeric_groups = sorted([float(g) if isinstance(g, str) else g for g in unique_groups])
            # Convert back to original type (int if whole numbers)
            unique_groups = [int(g) if g.is_integer() else g for g in numeric_groups]
        except (ValueError, AttributeError):
            # If conversion fails, use regular sorting
            unique_groups = sorted(unique_groups)
        
        # Use the actual group values for both positions and labels
        fig.update_xaxes(tickmode='array', tickvals=unique_groups, ticktext=unique_groups)
    
    return fig


def create_cell_type_comparison_plot(df: DataFrame, freq_cols: List[str], plot_type: str, filter_options=None, **kwargs):
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
    
    # Get the base metric name from the first column (they should all be the same type)
    base_metric = extract_metric_name(freq_cols[0]) if freq_cols else "Value"

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
        # For histograms, use original data melted by cell type
        melted_df = df.melt(id_vars=['Group'], value_vars=freq_cols, 
                           var_name='Cell Type', value_name='Frequency')
        melted_df['Cell Type'] = melted_df['Cell Type'].apply(extract_cell_type_name)
        fig = px.histogram(melted_df, x='Frequency', color='Cell Type', barmode='overlay', **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration to ALL plot types
    width = kwargs.get('width', 1200)  # Use default width if not specified
    height = kwargs.get('height', 500)  # Use default height if not specified (reduced from 700 for better aspect ratio)
    
    # Determine appropriate legend title for cell type comparison
    legend_title = "Cell Types"
    
    fig = configure_legend(
        fig, combined_df, 'Cell Type', is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
        
    # Update title, y-axis, and legend
    if 'title' not in kwargs:
        comprehensive_title = create_comprehensive_plot_title(df, base_metric, freq_cols, filter_options=filter_options)
        fig.update_layout(
            title=comprehensive_title,
            yaxis_title=base_metric,
            legend_title="Mean ± SEM"
        )
    
    # Ensure consistent sizing
    fig.update_layout(
        width=width,
        height=height
    )
    
    # Ensure all x-axis ticks are shown with correct group numbers
    if 'Group' in combined_df.columns:
        # Convert group values to numeric if they're strings representing numbers
        unique_groups = combined_df['Group'].unique()
        try:
            # Try to convert to numeric and sort
            numeric_groups = sorted([float(g) if isinstance(g, str) else g for g in unique_groups])
            # Convert back to original type (int if whole numbers)
            unique_groups = [int(g) if g.is_integer() else g for g in numeric_groups]
        except (ValueError, AttributeError):
            # If conversion fails, use regular sorting
            unique_groups = sorted(unique_groups)
        
        # Use the actual group values for both positions and labels
        fig.update_xaxes(tickmode='array', tickvals=unique_groups, ticktext=unique_groups)
    
    return fig


# create_time_course_single_plot function has been moved to time_plots.py as part of the unified timecourse system


def create_basic_plot(df: DataFrame, x: str, y: str, plot_type: str, filter_options=None, **kwargs):
    """
    Create a basic plot without aggregation.
    
    Args:
        df: DataFrame containing the data
        x: Column for x-axis
        y: Column for y-axis
        plot_type: Type of plot ('scatter', 'bar', 'box', 'line')
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

    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration
    color_col = kwargs.get('color')
    width = kwargs.get('width', 1200)  # Use default width if not specified
    height = kwargs.get('height', 500)  # Use default height if not specified
    
    # Determine appropriate legend title based on plot type
    legend_title = "Groups" if color_col else "Populations"
    
    fig = configure_legend(
        fig, df, color_col, is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
    
    # Update title
    if 'title' not in kwargs:
        metric_name = extract_metric_name(y) if y != x else y
        if x == 'Group':
            comprehensive_title = create_comprehensive_plot_title(df, metric_name, [y], filter_options=filter_options)
        else:
            comprehensive_title = f"{metric_name} vs {x}"
        fig.update_layout(title=comprehensive_title)
    
    # Ensure consistent sizing
    fig.update_layout(
        width=width,
        height=height
    )
    
    return fig 


# Export available functions
__all__ = [
    'create_single_metric_plot',
    'create_cell_type_comparison_plot', 
    'create_basic_plot'
] 