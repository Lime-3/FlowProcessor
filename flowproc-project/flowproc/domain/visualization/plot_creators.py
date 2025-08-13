"""
Core plot creation functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List, Callable, Dict, Union
from pathlib import Path
import numpy as np

from .legend_config import configure_legend
from .plot_factory import build_plot_from_df
from .data_aggregation import aggregate_by_group_with_sem, aggregate_multiple_metrics_by_group
from .column_utils import extract_cell_type_name, extract_metric_name, create_comprehensive_plot_title
from .plot_config import (
    DEFAULT_WIDTH, MARGIN, VERTICAL_SPACING, HORIZONTAL_SPACING,
    MAX_CELL_TYPES
)
from .plot_utils import (
    format_time_title, validate_plot_data, limit_cell_types, calculate_subplot_dimensions, 
    calculate_aspect_ratio_dimensions, get_group_label_map, calculate_layout_for_long_labels
)

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame
Figure = go.Figure


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
    # Extract internal-only option so it isn't passed to Plotly
    user_group_labels = kwargs.pop('user_group_labels', None)
    kwargs.pop('fixed_layout', None)

    # Aggregate data by Group
    agg_df = aggregate_by_group_with_sem(df, y_col)
    
    # Create plot based on type with centralized factory
    if plot_type == "box":
        # For box plots, use original data to show distribution
        fig = build_plot_from_df("box", df, x='Group', y=y_col, **kwargs)
    elif plot_type == "histogram":
        # For histograms, use original data to show distribution
        fig = build_plot_from_df("histogram", df, x=y_col, **kwargs)
    else:
        # Bar charts: vertical orientation; populations grouped side-by-side when color is used
        if plot_type == "bar":
            fig = build_plot_from_df("bar", agg_df, x='Group', y='mean', error_y='sem', **kwargs)
        else:
            fig = build_plot_from_df(plot_type, agg_df, x='Group', y='mean', error_y='sem', **kwargs)
    
    # Apply standardized legend configuration to ALL plot types
    color_col = kwargs.get('color')
    width = kwargs.get('width', 1000)  # Use default width if not specified
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
            yaxis_title=metric_name
        )
        
        # Debug: Verify the title was applied
        if hasattr(fig.layout, 'title') and hasattr(fig.layout.title, 'text'):
            logger.info(f"Title applied successfully to single metric plot: '{fig.layout.title.text}'")
        else:
            logger.warning("Title not found in single metric plot layout after update")
    
    # Ensure consistent sizing
    fig.update_layout(
        width=width,
        height=height,
        autosize=False
    )
    
    # Ensure all x-axis ticks are shown with customized labels if available
    if 'Group' in df.columns:
        unique_groups = df['Group'].unique()
        try:
            numeric_groups = sorted([float(g) if isinstance(g, str) else g for g in unique_groups])
            tickvals = [int(g) if hasattr(g, 'is_integer') and g.is_integer() else g for g in numeric_groups]
        except Exception:
            tickvals = sorted(unique_groups)

        group_label_map = get_group_label_map(df, user_group_labels)
        ticktext = [group_label_map.get(g, g) for g in tickvals]
        fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=ticktext)

        # Adjust layout for long labels to avoid vertical squish (preserve width and legend placement)
        try:
            if user_group_labels:
                legend_labels = [trace.name for trace in fig.data] if fig.data else []
                layout_adj = calculate_layout_for_long_labels(
                    labels=[str(t) for t in ticktext],
                    legend_items=len(legend_labels),
                    title=str(getattr(fig.layout.title, 'text', '') or ''),
                    legend_labels=[str(name) for name in legend_labels],
                    default_width=width,
                    default_height=height
                )
                # Preserve plot area size; expand only bottom margin and total height for labels
                current_margin = dict(fig.layout.margin) if fig.layout.margin else MARGIN.copy()
                proposed_margin = layout_adj.get('margin', MARGIN).copy()
                proposed_margin['r'] = max(proposed_margin.get('r', 0), current_margin.get('r', 0), MARGIN.get('r', 0))
                new_bottom = max(proposed_margin.get('b', 0), current_margin.get('b', 0))
                delta_bottom = max(0, new_bottom - current_margin.get('b', 0))
                fig.update_layout(
                    width=width,
                    height=height + delta_bottom,
                    margin=dict(l=current_margin.get('l', 50), r=proposed_margin['r'], t=current_margin.get('t', 50), b=new_bottom)
                )
                fig.update_xaxes(tickangle=layout_adj.get('xaxis_tickangle', 0))
        except Exception:
            pass
    
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
    logger.debug(f"Creating cell type comparison plot with {len(freq_cols)} columns: {freq_cols}")
    logger.debug(f"Input DataFrame shape: {df.shape}")
    logger.debug(f"Input DataFrame columns: {list(df.columns)}")
    
    # Extract internal-only option so it isn't passed to Plotly
    user_group_labels = kwargs.pop('user_group_labels', None)
    kwargs.pop('fixed_layout', None)

    # Prepare data for plotting all cell types together
    combined_df = aggregate_multiple_metrics_by_group(df, freq_cols)
    logger.debug(f"Aggregated data shape: {combined_df.shape}")
    logger.debug(f"Aggregated data columns: {list(combined_df.columns)}")
    
    # Get the base metric name from the first column (they should all be the same type)
    base_metric = extract_metric_name(freq_cols[0]) if freq_cols else "Value"
    logger.debug(f"Base metric name: {base_metric}")

    # Create plot with cell types in legend using centralized factory
    if plot_type == "box":
        # For box plots, use original data
        melted_df = df.melt(id_vars=['Group'], value_vars=freq_cols, 
                           var_name='Cell Type', value_name='Frequency')
        from .column_utils import build_unique_cell_type_labels
        label_map = build_unique_cell_type_labels(freq_cols)
        melted_df['Cell Type'] = melted_df['Cell Type'].map(label_map).fillna(melted_df['Cell Type'])
        fig = build_plot_from_df("box", melted_df, x='Group', y='Frequency', color='Cell Type', **kwargs)
        logger.debug(f"Created box plot with {len(fig.data)} traces")
    elif plot_type == "histogram":
        # For histograms, use original data melted by cell type
        melted_df = df.melt(id_vars=['Group'], value_vars=freq_cols, 
                           var_name='Cell Type', value_name='Frequency')
        from .column_utils import build_unique_cell_type_labels
        label_map = build_unique_cell_type_labels(freq_cols)
        melted_df['Cell Type'] = melted_df['Cell Type'].map(label_map).fillna(melted_df['Cell Type'])
        fig = build_plot_from_df("histogram", melted_df, x='Frequency', color='Cell Type', **kwargs)
        logger.debug(f"Created histogram plot with {len(fig.data)} traces")
    else:
        # scatter, bar, line → use aggregated df with SEM
        if plot_type == "bar":
            # Vertical grouped bars: populations next to one another
            kwargs.setdefault('barmode', 'group')
            fig = build_plot_from_df("bar", combined_df, x='Group', y='mean', color='Cell Type', error_y='sem', **kwargs)
        else:
            fig = build_plot_from_df(plot_type, combined_df, x='Group', y='mean', color='Cell Type', error_y='sem', **kwargs)
        logger.debug(f"Created {plot_type} plot with {len(fig.data)} traces")

    logger.debug("Figure created successfully, applying legend configuration")
    
    # Apply standardized legend configuration to ALL plot types
    width = kwargs.get('width', 1000)  # Use default width if not specified
    height = kwargs.get('height', 500)  # Use default height if not specified (reduced from 700 for better aspect ratio)
    
    # Determine appropriate legend title for cell type comparison
    legend_title = "Cell Types"
    
    fig = configure_legend(
        fig, combined_df, 'Cell Type', is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
    logger.debug("Legend configuration applied")
        
    # Update title, y-axis, and legend
    if 'title' not in kwargs:
        comprehensive_title = create_comprehensive_plot_title(df, base_metric, freq_cols, filter_options=filter_options)
        logger.debug(f"Setting title: {comprehensive_title}")
        fig.update_layout(
            title=comprehensive_title,
            yaxis_title=base_metric
        )
    
    # Ensure consistent sizing
    fig.update_layout(
        width=width,
        height=height,
        autosize=False
    )
    
    # Ensure all x-axis ticks are shown with customized labels if available
    if 'Group' in combined_df.columns:
        unique_groups = combined_df['Group'].unique()
        try:
            numeric_groups = sorted([float(g) if isinstance(g, str) else g for g in unique_groups])
            tickvals = [int(g) if hasattr(g, 'is_integer') and g.is_integer() else g for g in numeric_groups]
        except Exception:
            tickvals = sorted(unique_groups)

        group_label_map = get_group_label_map(combined_df, user_group_labels)
        ticktext = [group_label_map.get(g, g) for g in tickvals]
        fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=ticktext)

        # Adjust layout for long labels to avoid vertical squish (preserve width and legend placement)
        try:
            if user_group_labels:
                legend_labels = [trace.name for trace in fig.data] if fig.data else []
                layout_adj = calculate_layout_for_long_labels(
                    labels=[str(t) for t in ticktext],
                    legend_items=len(legend_labels),
                    title=str(getattr(fig.layout.title, 'text', '') or ''),
                    legend_labels=[str(name) for name in legend_labels],
                    default_width=width,
                    default_height=height
                )
                current_margin = dict(fig.layout.margin) if fig.layout.margin else MARGIN.copy()
                proposed_margin = layout_adj.get('margin', MARGIN).copy()
                proposed_margin['r'] = max(proposed_margin.get('r', 0), current_margin.get('r', 0), MARGIN.get('r', 0))
                new_bottom = max(proposed_margin.get('b', 0), current_margin.get('b', 0))
                delta_bottom = max(0, new_bottom - current_margin.get('b', 0))
                fig.update_layout(
                    width=width,
                    height=height + delta_bottom,
                    margin=dict(l=current_margin.get('l', 50), r=proposed_margin['r'], t=current_margin.get('t', 50), b=new_bottom)
                )
                fig.update_xaxes(tickangle=layout_adj.get('xaxis_tickangle', 0))
        except Exception:
            pass
    
    logger.debug(f"Final figure layout: width={fig.layout.width}, height={fig.layout.height}")
    logger.debug(f"Final figure has {len(fig.data)} traces")
    
    return fig


# create_time_course_single_plot function has been moved to time_plots.py as part of the unified timecourse system


def create_basic_plot(df: DataFrame, x: str, y: str, plot_type: str, filter_options=None, **kwargs):
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
    # Extract internal-only option so it isn't passed to Plotly
    user_group_labels = kwargs.pop('user_group_labels', None)
    kwargs.pop('fixed_layout', None)

    # Create plot via centralized factory
    if plot_type == "histogram":
        fig = build_plot_from_df("histogram", df, x=x, **kwargs)
    elif plot_type == "bar":
        # Basic bar: vertical, grouped when color present
        kwargs.setdefault('barmode', 'group')
        fig = build_plot_from_df("bar", df, x=x, y=y, **kwargs)
    else:
        fig = build_plot_from_df(plot_type, df, x=x, y=y, **kwargs)
    
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
        if plot_type == "histogram":
            # For histograms, use the x column name for the title
            metric_name = extract_metric_name(x)
            comprehensive_title = create_comprehensive_plot_title(df, metric_name, [x], filter_options=filter_options)
        else:
            metric_name = extract_metric_name(y) if y != x else y
            if x == 'Group':
                comprehensive_title = create_comprehensive_plot_title(df, metric_name, [y], filter_options=filter_options)
            else:
                comprehensive_title = f"{metric_name} vs {x}"
        fig.update_layout(title=comprehensive_title)
    
    # Ensure consistent sizing
    fig.update_layout(
        width=width,
        height=height,
        autosize=False
    )
    
    # Map group tick labels if plotting by Group on x-axis
    if x == 'Group' and 'Group' in df.columns:
        unique_groups = df['Group'].unique()
        try:
            numeric_groups = sorted([float(g) if isinstance(g, str) else g for g in unique_groups])
            tickvals = [int(g) if hasattr(g, 'is_integer') and g.is_integer() else g for g in numeric_groups]
        except Exception:
            tickvals = sorted(unique_groups)

        group_label_map = get_group_label_map(df, user_group_labels)
        ticktext = [group_label_map.get(g, g) for g in tickvals]
        fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=ticktext)

        # Adjust layout for long labels to avoid vertical squish (preserve width and legend placement)
        try:
            if user_group_labels:
                legend_labels = [trace.name for trace in fig.data] if fig.data else []
                layout_adj = calculate_layout_for_long_labels(
                    labels=[str(t) for t in ticktext],
                    legend_items=len(legend_labels),
                    title=str(getattr(fig.layout.title, 'text', '') or ''),
                    legend_labels=[str(name) for name in legend_labels],
                    default_width=width,
                    default_height=height
                )
                current_margin = dict(fig.layout.margin) if fig.layout.margin else MARGIN.copy()
                proposed_margin = layout_adj.get('margin', MARGIN).copy()
                proposed_margin['r'] = max(proposed_margin.get('r', 0), current_margin.get('r', 0), MARGIN.get('r', 0))
                new_bottom = max(proposed_margin.get('b', 0), current_margin.get('b', 0))
                delta_bottom = max(0, new_bottom - current_margin.get('b', 0))
                fig.update_layout(
                    width=width,
                    height=height + delta_bottom,
                    margin=dict(l=current_margin.get('l', 50), r=proposed_margin['r'], t=current_margin.get('t', 50), b=new_bottom)
                )
                fig.update_xaxes(tickangle=layout_adj.get('xaxis_tickangle', 0))
        except Exception:
            pass
    
    return fig


# Export available functions
__all__ = [
    'create_single_metric_plot',
    'create_cell_type_comparison_plot', 
    'create_basic_plot',
    'create_cell_type_faceted_plot',
    'create_group_faceted_plot',
    'create_single_column_faceted_plot',
    'create_timecourse_visualization',
    'plot',
    'compare_groups',
    'scatter',
    'bar',
    'box',
    'histogram'
]


def _create_faceted_plot(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    facet_by: Optional[str] = None,
    title: str = "",
    trace_name_fn: Optional[Callable[[str], str]] = None,
    width: int = DEFAULT_WIDTH,
    height: Optional[int] = None,
    vertical_spacing: float = VERTICAL_SPACING,
    horizontal_spacing: float = HORIZONTAL_SPACING,
    max_cell_types: int = MAX_CELL_TYPES,
    filter_options=None,
    aggregation: str = "raw",
    group_col: Optional[str] = None
) -> Figure:
    """
    Base function for creating faceted plots with shared logic.
    
    Args:
        df: DataFrame containing the data
        time_col: Time column name
        value_cols: List of value columns (cell types)
        facet_by: Column to facet by (optional)
        title: Plot title
        trace_name_fn: Function to generate trace names
        width: Figure width
        height: Figure height (calculated automatically if not provided)
        vertical_spacing: Vertical spacing between subplots
        horizontal_spacing: Horizontal spacing between subplots
        max_cell_types: Maximum number of cell types to display
        filter_options: Filtering options for data
        aggregation: Data aggregation method ("mean_sem", "median_iqr", "raw")
        group_col: Column to group by for aggregation (e.g., "Group")
        
    Returns:
        Plotly Figure object with subplots
    """
    # Validate input data
    validate_plot_data(df, time_col, value_cols, facet_by)
    
    # Limit cell types for clarity
    value_cols = limit_cell_types(value_cols, max_cell_types)
    
    # Determine subplot structure
    if facet_by:
        facet_values = sorted(df[facet_by].unique())
        rows, cols = calculate_subplot_dimensions(len(facet_values))
    else:
        rows, cols = calculate_subplot_dimensions(len(value_cols))
    
    # Create subplot titles
    subplot_titles = []
    if facet_by:
        for facet_val in facet_values:
            facet_data = df[df[facet_by] == facet_val]
            if time_col in facet_data.columns:
                time_values = facet_data[time_col].dropna().unique()
                time_info = format_time_title(time_values)
                subplot_titles.append(f"{facet_val}{time_info}")
            else:
                subplot_titles.append(str(facet_val))
    else:
        from .column_utils import create_enhanced_title
        subplot_titles = [create_enhanced_title(df, col, time_col) for col in value_cols]
    
    # Calculate appropriate vertical spacing based on number of rows
    if rows > 1:
        # Ensure vertical spacing doesn't exceed Plotly's limit
        max_spacing = 1.0 / (rows - 1) - 0.01  # Leave a small margin
        adjusted_vertical_spacing = min(vertical_spacing, max_spacing)
    else:
        adjusted_vertical_spacing = vertical_spacing
    
    # Calculate height if not provided
    if height is None:
        height = calculate_aspect_ratio_dimensions(rows, cols, width)
    
    # Create subplot figure
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=adjusted_vertical_spacing,
        horizontal_spacing=horizontal_spacing
    )
    
    # Add traces to subplots
    for i, value_col in enumerate(value_cols):
        if facet_by:
            # Facet by the specified column
            for j, facet_val in enumerate(facet_values):
                facet_data = df[df[facet_by] == facet_val]
                if facet_data.empty:
                    continue
                
                # Determine subplot position
                row = (j // cols) + 1
                col = (j % cols) + 1
                
                # Add trace for this facet value
                if trace_name_fn:
                    trace_name = trace_name_fn(value_col)
                else:
                    trace_name = extract_cell_type_name(value_col)
                
                # Create trace based on plot type
                trace = go.Scatter(
                    x=facet_data[time_col],
                    y=facet_data[value_col],
                    name=trace_name,
                    mode='lines+markers',
                    line=dict(width=2),
                    marker=dict(size=6),
                    showlegend=(i == 0)  # Only show legend for first trace
                )
                
                fig.add_trace(trace, row=row, col=col)
        else:
            # Facet by cell type
            row = (i // cols) + 1
            col = (i % cols) + 1
            
            trace_name = extract_cell_type_name(value_col)
            
            trace = go.Scatter(
                x=df[time_col],
                y=df[value_col],
                name=trace_name,
                mode='lines+markers',
                line=dict(width=2),
                marker=dict(size=6),
                showlegend=True
            )
            
            fig.add_trace(trace, row=row, col=col)
    
    # Update layout
    fig.update_layout(
        title=title,
        width=width,
        height=height,
        margin=MARGIN,
        showlegend=True
    )
    
    # Update axes labels
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            fig.update_xaxes(title_text="Time", row=i, col=j)
            fig.update_yaxes(title_text="Value", row=i, col=j)
    
    return fig


def create_cell_type_faceted_plot(
    df: DataFrame, 
    time_col: str, 
    value_cols: List[str],
    width: int = DEFAULT_WIDTH,
    height: Optional[int] = None,
    max_cell_types: int = MAX_CELL_TYPES,
    filter_options=None,
    aggregation: str = "raw",
    group_col: Optional[str] = None
) -> Figure:
    """
    Create faceted plot with each subplot showing a different cell type in vertically stacked single columns.
    
    Args:
        df: DataFrame containing the data
        time_col: Time column name
        value_cols: List of value columns (cell types)
        width: Figure width
        height: Figure height (calculated automatically if not provided)
        max_cell_types: Maximum number of cell types to display
        filter_options: Filtering options for data
        aggregation: Data aggregation method ("mean_sem", "median_iqr", "raw")
        group_col: Column to group by for aggregation (e.g., "Group")
        
    Returns:
        Plotly Figure object with subplots
    """
    return _create_faceted_plot(
        df=df,
        time_col=time_col,
        value_cols=value_cols,
        title="Time Course by Cell Type",
        width=width,
        height=height,
        max_cell_types=max_cell_types,
        filter_options=filter_options,
        aggregation=aggregation,
        group_col=group_col
    )


def create_group_faceted_plot(
    df: DataFrame, 
    time_col: str, 
    value_cols: List[str], 
    facet_by: str,
    width: int = DEFAULT_WIDTH,
    height: Optional[int] = None,
    max_cell_types: int = MAX_CELL_TYPES,
    filter_options=None,
    aggregation: str = "raw",
    group_col: Optional[str] = None
) -> Figure:
    """
    Create faceted plot with each subplot showing a different group/tissue in vertically stacked single columns.
    
    Args:
        df: DataFrame containing the data
        time_col: Time column name
        value_cols: List of value columns (cell types)
        facet_by: Column to facet by
        width: Figure width
        height: Figure height (calculated automatically if not provided)
        max_cell_types: Maximum number of cell types to display
        filter_options: Filtering options for data
        aggregation: Data aggregation method ("mean_sem", "median_iqr", "raw")
        group_col: Column to group by for aggregation (e.g., "Group")
        
    Returns:
        Plotly Figure object with subplots
    """
    return _create_faceted_plot(
        df=df,
        time_col=time_col,
        value_cols=value_cols,
        facet_by=facet_by,
        title=f"Time Course by {facet_by}",
        trace_name_fn=extract_cell_type_name,
        width=width,
        height=height,
        max_cell_types=max_cell_types,
        filter_options=filter_options,
        aggregation=aggregation,
        group_col=group_col
    )


def create_single_column_faceted_plot(
    df: DataFrame, 
    time_col: str, 
    value_col: str, 
    facet_by: str,
    width: int = DEFAULT_WIDTH,
    height: Optional[int] = None
) -> Figure:
    """
    Create faceted plot for a single column in vertically stacked single columns.
    
    Args:
        df: DataFrame containing the data
        time_col: Time column name
        value_col: Value column to plot
        facet_by: Column to facet by
        width: Figure width
        height: Figure height (calculated automatically if not provided)
        
    Returns:
        Plotly Figure object with subplots
    """
    return _create_faceted_plot(
        df=df,
        time_col=time_col,
        value_cols=[value_col],
        facet_by=facet_by,
        title=f"{value_col} over Time by {facet_by}",
        trace_name_fn=lambda x: f"Group {x}",
        width=width,
        height=height,
        max_cell_types=1  # Single column plot
    ) 


def create_timecourse_visualization(
    data: Union[str, DataFrame],
    time_column: Optional[str] = None,
    metric: Optional[str] = None,
    group_by: Optional[str] = None,
    facet_by: Optional[str] = None,
    plot_type: str = "line",
    aggregation: str = "mean_sem",
    max_cell_types: int = 10,
    sample_size: Optional[int] = None,
    filter_options: Optional[Dict] = None,
    population_filter: Optional[str] = None,
    save_html: Optional[str] = None,
    **kwargs
) -> Figure:
    """
    Unified timecourse visualization function - single entry point for all timecourse plots.
    
    Args:
        data: CSV file path or DataFrame
        time_column: Time column name (auto-detected if None)
        metric: Metric type (e.g., "Freq. of Parent") or specific column name
        group_by: Column to group data by (e.g., "Group", "Treatment")
        facet_by: What to facet by ("Group", "Cell Type", "Tissue", None for single plot)
        plot_type: Plot type ("line", "scatter", "area")
        aggregation: Data aggregation method ("mean_sem", "median_iqr", "raw")
        max_cell_types: Maximum number of cell types to include
        sample_size: Sample size for large datasets
        filter_options: Filtering options for data
        population_filter: Specific population to filter for (None for all populations)
        save_html: Optional path to save HTML file
        **kwargs: Additional plotly parameters
    
    Returns:
        Plotly Figure object
    """
    # Load and prepare data
    df, time_col, value_cols, group_col = _prepare_timecourse_data(
        data, time_column, metric, group_by, max_cell_types, sample_size, population_filter
    )
    
    # Determine visualization strategy
    if facet_by:
        fig = _create_faceted_timecourse(
            df, time_col, value_cols, group_col, facet_by, plot_type, 
            aggregation, filter_options, **kwargs
        )
    else:
        if len(value_cols) == 1:
            fig = _create_single_timecourse(
                df, time_col, value_cols[0], group_col, plot_type, 
                aggregation, filter_options, **kwargs
            )
        else:
            fig = _create_overlay_timecourse(
                df, time_col, value_cols, group_col, plot_type, 
                aggregation, filter_options, **kwargs
            )
    
    # Save if requested
    if save_html:
        _save_timecourse_visualization(fig, save_html)
    
    return fig


def _prepare_timecourse_data(
    data: Union[str, DataFrame],
    time_column: Optional[str],
    metric: Optional[str],
    group_by: Optional[str],
    max_cell_types: int,
    sample_size: Optional[int],
    population_filter: Optional[str]
) -> tuple[DataFrame, str, list[str], Optional[str]]:
    """Prepare and validate data for timecourse visualization."""
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect time column
    time_col = _detect_time_column(df, time_column)
    
    # Auto-detect group column
    group_col = _detect_group_column(df, group_by)
    
    # Handle metric selection and get value columns
    value_cols = _detect_value_columns(df, metric, max_cell_types)
    
    # Apply sampling if needed
    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
        logger.info(f"Applied sampling: {sample_size} data points")
    
    # Apply population filter if provided
    if population_filter:
        # Filter value columns to only include those matching the selected population
        filtered_value_cols = []
        for col in value_cols:
            if population_filter in col:
                filtered_value_cols.append(col)
        
        if filtered_value_cols:
            value_cols = filtered_value_cols
            logger.info(f"Applied population filter '{population_filter}': {len(value_cols)} columns remaining")
        else:
            logger.warning(f"No columns found matching population '{population_filter}', using all available columns")
    
    return df, time_col, value_cols, group_col


def _detect_time_column(df: DataFrame, time_column: Optional[str]) -> str:
    """Auto-detect time column from common patterns."""
    if time_column and time_column in df.columns:
        return time_column
    
    # Look for time-related columns
    time_candidates = [
        col for col in df.columns 
        if any(keyword in col.lower() for keyword in ['time', 'day', 'hour', 'week', 'minute'])
    ]
    
    if time_candidates:
        time_col = time_candidates[0]
        logger.info(f"Auto-detected time column: {time_col}")
        return time_col
    
    # Fallback to first column
    logger.warning(f"No time column detected, using first column: {df.columns[0]}")
    return df.columns[0]


def _detect_group_column(df: DataFrame, group_by: Optional[str]) -> Optional[str]:
    """Auto-detect group column from common patterns."""
    if group_by and group_by in df.columns:
        return group_by
    
    # Look for group-related columns
    group_candidates = [
        col for col in df.columns 
        if any(keyword in col.lower() for keyword in ['group', 'treatment', 'condition', 'sample'])
    ]
    
    # Filter out SampleID columns that are not actual group columns
    filtered_candidates = []
    for col in group_candidates:
        col_lower = col.lower()
        # Skip columns that are clearly sample identifiers, not group columns
        if any(skip_keyword in col_lower for skip_keyword in ['sampleid', 'sample_id', 'id']):
            continue
        # Skip columns that contain file extensions or look like file paths
        if any(ext in col_lower for ext in ['.fcs', '.csv', '.txt']):
            continue
        filtered_candidates.append(col)
    
    if filtered_candidates:
        group_col = filtered_candidates[0]
        logger.info(f"Auto-detected group column: {group_col}")
        return group_col
    
    logger.info("No group column detected")
    return None


def _detect_value_columns(df: DataFrame, metric: Optional[str], max_cell_types: int) -> list[str]:
    """Detect value columns for plotting."""
    from .column_utils import detect_flow_columns, detect_available_metric_types, get_matching_columns_for_metric
    
    if metric:
        # Check if metric is a metric type (like "Freq. of Parent") or a specific column
        metric_types = detect_available_metric_types(df)
        
        if metric in metric_types:
            # Find all columns matching this metric type
            matching_cols = get_matching_columns_for_metric(df, metric)
            if matching_cols:
                # Limit to max_cell_types
                return matching_cols[:max_cell_types]
            else:
                logger.warning(f"No columns found for metric type '{metric}'")
        elif metric in df.columns:
            # Metric is a specific column name
            return [metric]
        else:
            logger.warning(f"Metric '{metric}' not found in data")
    
    # Auto-detect flow cytometry columns
    flow_cols = detect_flow_columns(df)
    
    # Prioritize frequency columns
    if flow_cols['frequencies']:
        return flow_cols['frequencies'][:max_cell_types]
    elif flow_cols['medians']:
        return flow_cols['medians'][:max_cell_types]
    elif flow_cols['means']:
        return flow_cols['means'][:max_cell_types]
    else:
        # Fallback to numeric columns (excluding time and group columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Filter out potential time/group columns
        filtered_cols = [col for col in numeric_cols if not any(keyword in col.lower() for keyword in ['time', 'day', 'hour', 'group', 'sample'])]
        return filtered_cols[:max_cell_types]


def _create_single_timecourse(
    df: DataFrame,
    time_col: str,
    value_col: str,
    group_col: Optional[str],
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> Figure:
    """Create timecourse plot for a single metric."""
    # Debug logging
    logger.info(f"Creating single metric timecourse for column: {value_col}")
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Time column: {time_col}, unique values: {df[time_col].dropna().unique()}")
    logger.info(f"Value column: {value_col}, range: {df[value_col].min():.3f} to {df[value_col].max():.3f}")
    if group_col:
        logger.info(f"Group column: {group_col}, unique values: {df[group_col].dropna().unique()}")
    
    # Apply aggregation if requested
    if aggregation == "mean_sem" and group_col:
        # For timecourse plots, we need to aggregate by both group and time
        plot_df = df.groupby([group_col, time_col])[value_col].agg(['mean', 'std', 'count']).reset_index()
        plot_df['sem'] = plot_df['std'] / np.sqrt(plot_df['count'])
        y_col = 'mean'
        error_y = 'sem'
        logger.info(f"Aggregated data shape: {plot_df.shape}")
        logger.info(f"Aggregated data columns: {list(plot_df.columns)}")
    else:
        plot_df = df
        y_col = value_col
        error_y = None
        logger.info(f"Using raw data, shape: {plot_df.shape}")
    
    # Create plot based on type via centralized factory
    if plot_type in ("line", "scatter", "area"):
        fig = build_plot_from_df(plot_type, plot_df, x=time_col, y=y_col, color=group_col, error_y=error_y, **kwargs)
        logger.info(f"Created {plot_type} plot (group_col={group_col}, error_y={error_y})")
    else:
        raise ValueError(f"Unsupported plot type: {plot_type}")
    
    # Update trace names to use shortnames for better legend display
    for trace in fig.data:
        if trace.name and trace.name != value_col:
            # This is a group trace, keep the group name
            continue
        else:
            # This is the main trace, update to use shortname
            from .column_utils import create_population_shortname
            shortname = create_population_shortname(value_col)
            trace.name = shortname
            logger.info(f"Updated trace name from '{value_col}' to '{shortname}'")
    
    # Debug: Check what traces were created
    logger.info(f"Created figure with {len(fig.data)} traces")
    for i, trace in enumerate(fig.data):
        logger.info(f"Trace {i}: {trace.name}, x points: {len(trace.x)}, y points: {len(trace.y)}")
    
    # Apply legend configuration
    width = kwargs.get('width', 1200)
    height = kwargs.get('height', 500)
    
    # Determine appropriate legend title based on plot type
    if group_col:
        legend_title = "Groups"
    else:
        legend_title = "Populations"
    
    fig = configure_legend(
        fig, df, group_col, is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
    
    # Update title and labels
    if 'title' not in kwargs:
        metric_name = extract_metric_name(value_col)
        logger.debug(f"Time plot - Creating title with metric: {metric_name}")
        from .column_utils import create_timecourse_plot_title
        title = create_timecourse_plot_title(df, metric_name, [value_col], filter_options=filter_options)
        logger.debug(f"Time plot - Title created: {title}")
        fig.update_layout(
            title=title,
            margin=dict(t=80)  # Add more top margin for title spacing
        )
        
        # Debug: Verify the title was applied
        if hasattr(fig.layout, 'title') and hasattr(fig.layout.title, 'text'):
            logger.info(f"Title applied successfully to time plot: '{fig.layout.title.text}'")
        else:
            logger.warning("Title not found in time plot layout after update")
    
    fig.update_layout(
        width=width,
        height=height,
        xaxis_title="Time",
        yaxis_title=extract_metric_name(value_col)
    )
    
    return fig


def _create_overlay_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> Figure:
    """Create timecourse plot with multiple metrics overlaid."""
    fig = go.Figure()
    
    # Apply aggregation if requested
    if aggregation == "mean_sem" and group_col:
        # For timecourse plots, we need to aggregate by both group and time for ALL value columns
        agg_data = []
        for value_col in value_cols:
            # Aggregate each value column separately
            col_agg = df.groupby([group_col, time_col])[value_col].agg(['mean', 'std', 'count']).reset_index()
            col_agg['sem'] = col_agg['std'] / np.sqrt(col_agg['count'])
            col_agg['value_col'] = value_col  # Track which column this data came from
            agg_data.append(col_agg)
        
        # Combine all aggregated data
        plot_df = pd.concat(agg_data, ignore_index=True)
        y_col = 'mean'
        error_y = 'sem'
    else:
        plot_df = df
        y_col = None
        error_y = None
    
    # Add traces for each metric
    for value_col in value_cols:
        if plot_type == "line":
            if group_col and group_col in plot_df.columns:
                # Get data for this specific value column
                if 'value_col' in plot_df.columns:
                    # Using aggregated data
                    col_data = plot_df[plot_df['value_col'] == value_col]
                else:
                    # Using raw data
                    col_data = plot_df
                
                for group in col_data[group_col].unique():
                    group_data = col_data[col_data[group_col] == group]
                    
                    # Add error bars if available
                    error_y_data = None
                    if error_y and error_y in group_data.columns:
                        error_y_data = dict(
                            type='data',
                            array=group_data[error_y],
                            visible=True
                        )
                    
                    # Use shortname for better legend display
                    from .column_utils import create_population_shortname
                    shortname = create_population_shortname(value_col)
                    trace_name = f"{shortname} - {group}"
                    
                    fig.add_trace(go.Scatter(
                        x=group_data[time_col],
                        y=group_data[y_col] if y_col else group_data[value_col],
                        name=trace_name,
                        mode='lines+markers',
                        line=dict(width=2),
                        marker=dict(size=6),
                        error_y=error_y_data
                    ))
            else:
                # No group column, plot all data for this metric
                if 'value_col' in plot_df.columns:
                    # Using aggregated data
                    col_data = plot_df[plot_df['value_col'] == value_col]
                else:
                    # Using raw data
                    col_data = plot_df
                
                # Add error bars if available
                error_y_data = None
                if error_y and error_y in col_data.columns:
                    error_y_data = dict(
                        type='data',
                        array=col_data[error_y],
                        visible=True
                    )
                
                # Use shortname for better legend display
                from .column_utils import create_population_shortname
                shortname = create_population_shortname(value_col)
                
                fig.add_trace(go.Scatter(
                    x=col_data[time_col],
                    y=col_data[y_col] if y_col else col_data[value_col],
                    name=shortname,
                    mode='lines+markers',
                    line=dict(width=2),
                    marker=dict(size=6),
                    error_y=error_y_data
                ))
    
    # Apply legend configuration
    width = kwargs.get('width', 1000)
    height = kwargs.get('height', 480)
    
    # Determine appropriate legend title based on plot type
    if group_col:
        legend_title = "Groups"
    else:
        legend_title = "Metrics"
    
    fig = configure_legend(
        fig, df, group_col, is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
    
    # Update title and labels
    if 'title' not in kwargs:
        logger.debug("Overlay timecourse - Creating title for multiple metrics")
        from .column_utils import create_timecourse_plot_title
        title = create_timecourse_plot_title(df, "Multiple Metrics", value_cols, filter_options=filter_options)
        logger.debug(f"Overlay timecourse - Title created: {title}")
        fig.update_layout(
            title=title,
            margin=dict(t=80)  # Add more top margin for title spacing
        )
        
        # Debug: Verify the title was applied
        if hasattr(fig.layout, 'title') and hasattr(fig.layout.title, 'text'):
            logger.info(f"Title applied successfully to overlay timecourse: '{fig.layout.title.text}'")
        else:
            logger.warning("Title not found in overlay timecourse layout after update")
    
    fig.update_layout(
        width=width,
        height=height,
        xaxis_title="Time",
        yaxis_title="Value"
    )
    
    return fig


def _create_faceted_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    facet_by: str,
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> Figure:
    """Create faceted timecourse plot."""
    if facet_by == "Cell Type":
        return _create_cell_type_faceted_timecourse(
            df, time_col, value_cols, group_col, plot_type, 
            aggregation, filter_options, **kwargs
        )
    else:
        return _create_group_faceted_timecourse(
            df, time_col, value_cols, group_col, facet_by, plot_type, 
            aggregation, filter_options, **kwargs
        )


def _create_cell_type_faceted_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> Figure:
    """Create timecourse plot faceted by cell type."""
    # Create faceted plot using existing infrastructure with aggregation
    fig = create_cell_type_faceted_plot(
        df, time_col, value_cols, filter_options=filter_options, 
        aggregation=aggregation, group_col=group_col, **kwargs
    )
    
    # Update layout for timecourse specifics
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Value"
    )
    
    return fig


def _create_group_faceted_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    facet_by: str,
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> Figure:
    """Create timecourse plot faceted by group/tissue."""
    # Create faceted plot using existing infrastructure with aggregation
    fig = create_group_faceted_plot(
        df, time_col, value_cols, facet_by, filter_options=filter_options,
        aggregation=aggregation, group_col=group_col, **kwargs
    )
    
    # Update layout for timecourse specifics
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Value"
    )
    
    return fig


def _save_timecourse_visualization(fig: Figure, save_path: str) -> None:
    """Save visualization to HTML file."""
    from .plotly_renderer import PlotlyRenderer
    
    renderer = PlotlyRenderer()
    renderer.export_to_html_optimized(fig, save_path, 'minimal')
    logger.info(f"Saved timecourse visualization to {save_path}")


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
        y: Y-axis column name or metric type (auto-detected if None)
        plot_type: 'scatter', 'bar', 'box', 'line', 'histogram'
        save_html: Optional path to save HTML file
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
    
    # Auto-detect columns for flow cytometry data
    if x is None or y is None:
        from .column_utils import detect_flow_columns
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
                y = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Handle case where y is a metric type (like "Freq. of Parent") rather than a column name
    if y and y not in df.columns:
        from .column_utils import detect_available_metric_types, get_matching_columns_for_metric
        metric_types = detect_available_metric_types(df)
        
        logger.debug(f"y parameter '{y}' not found in columns, checking if it's a metric type")
        logger.debug(f"Available metric types: {metric_types}")
        
        if y in metric_types:
            # Find all columns matching this metric type
            matching_cols = get_matching_columns_for_metric(df, y)
            logger.debug(f"Looking for metric type '{y}', found matching columns: {matching_cols}")
            
            if matching_cols:
                if len(matching_cols) == 1:
                    # Single column found - use it directly
                    y = matching_cols[0]
                    logger.info(f"Using single column '{y}' for metric type '{y}'")
                else:
                    # Multiple columns found - use cell type comparison plot
                    logger.info(f"Multiple columns found for metric type '{y}', using cell type comparison plot with {len(matching_cols)} columns")
                    logger.debug(f"Columns to plot: {matching_cols}")
                    result_fig = create_cell_type_comparison_plot(df, matching_cols, plot_type, filter_options=filter_options, **kwargs)
                    logger.debug(f"Cell type comparison plot created successfully, figure has {len(result_fig.data)} traces")
                    
                    # Save HTML if requested (since we're returning early, we need to handle this here)
                    if save_html:
                        from .plotly_renderer import PlotlyRenderer
                        renderer = PlotlyRenderer()
                        renderer.export_to_html_optimized(result_fig, save_html, 'minimal')
                        logger.info(f"Saved cell type comparison plot to {save_html}")
                    
                    return result_fig
            else:
                # No columns found for this metric type - fallback to auto-detection
                logger.warning(f"No columns found for metric type '{y}', falling back to auto-detection")
                from .column_utils import detect_flow_columns
                flow_cols = detect_flow_columns(df)
                if flow_cols['frequencies']:
                    y = flow_cols['frequencies'][0]
                else:
                    raise ValueError(f"No columns found for metric type '{y}' and no fallback columns available")
        else:
            # y is not a metric type and not a column - this is an error
            logger.error(f"Column '{y}' not found in data and not recognized as a metric type")
            logger.error(f"Available columns: {list(df.columns)}")
            logger.error(f"Available metric types: {metric_types}")
            raise ValueError(f"Column '{y}' not found in data and not recognized as a metric type")
    
    # Ensure consistent sizing
    if 'width' not in kwargs:
        kwargs['width'] = 1200
    if 'height' not in kwargs:
        kwargs['height'] = 500
    
    # Create plot
    if plot_type == "histogram":
        fig = create_basic_plot(df, x, x, "histogram", filter_options=filter_options, **kwargs)
    else:
        fig = create_basic_plot(df, x, y, plot_type, filter_options=filter_options, **kwargs)
    
    # Save if requested
    if save_html:
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
                  filter_options=None,
                  **kwargs):
    """
    Compare groups using a specified metric.
    
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
        from .column_utils import detect_flow_columns
        flow_cols = detect_flow_columns(df)
        if flow_cols['frequencies']:
            metric = flow_cols['frequencies'][0]
        elif flow_cols['medians']:
            metric = flow_cols['medians'][0]
        else:
            metric = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Ensure consistent sizing
    if 'width' not in kwargs:
        kwargs['width'] = 1200
    if 'height' not in kwargs:
        kwargs['height'] = 500
    
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