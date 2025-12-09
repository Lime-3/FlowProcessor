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
from .column_utils import extract_cell_type_name, extract_metric_name, create_comprehensive_plot_title, resolve_metric_selection
from .plot_config import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, MARGIN, VERTICAL_SPACING, HORIZONTAL_SPACING,
    MAX_CELL_TYPES
)
from .plot_utils import (
    format_time_title, validate_plot_data, limit_cell_types, calculate_subplot_dimensions, 
    calculate_aspect_ratio_dimensions, select_legend_title, apply_common_layout, apply_group_tick_labels
)
from ..aggregation import timecourse_group_stats, timecourse_group_stats_multi

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
            show_individual_points: bool - Whether to overlay individual data points (can be combined with error_bars)
            error_bars: bool - Whether to show error bars (can be combined with show_individual_points)
        
    Returns:
        Plotly Figure object
    """
    # Extract internal-only option so it isn't passed to Plotly
    user_group_labels = kwargs.pop('user_group_labels', None)
    kwargs.pop('fixed_layout', None)
    
    # Extract display options (can be enabled independently)
    show_individual_points = kwargs.pop('show_individual_points', False)
    error_bars = kwargs.pop('error_bars', True)

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
        # Determine error_y parameter based on error_bars flag
        error_y_col = 'sem' if error_bars else None
        
        # Bar charts: vertical orientation; populations grouped side-by-side when color is used
        if plot_type == "bar":
            fig = build_plot_from_df("bar", agg_df, x='Group', y='mean', error_y=error_y_col, **kwargs)
        else:
            fig = build_plot_from_df(plot_type, agg_df, x='Group', y='mean', error_y=error_y_col, **kwargs)
        
        # Overlay individual points if requested
        if show_individual_points and plot_type in ("bar", "scatter", "line"):
            _add_individual_points_overlay(fig, df, y_col, plot_type)
    
    # Apply standardized legend configuration to ALL plot types
    color_col = kwargs.get('color')
    width = kwargs.get('width', DEFAULT_WIDTH)
    height = kwargs.get('height', DEFAULT_HEIGHT)

    legend_title = select_legend_title(color_col=color_col, context='single')

    fig = apply_common_layout(
        fig=fig,
        df=df,
        color_col=color_col,
        width=width,
        height=height,
        legend_title=legend_title,
        show_mean_sem_label=True
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
    
    # Ensure all x-axis ticks are shown with customized labels if available
    fig = apply_group_tick_labels(fig, df, user_group_labels, width, height)
    
    return fig


def _add_individual_points_overlay(fig: Figure, df: DataFrame, y_col: str, plot_type: str):
    """
    Add individual data points as an overlay on an existing figure.
    Points match the color of their group with a black outline.
    
    Args:
        fig: Plotly Figure to add points to
        df: Original DataFrame with raw data
        y_col: Column name for y values
        plot_type: Type of plot ('bar', 'scatter', 'line')
    """
    if 'Group' not in df.columns:
        return
    
    # Build mapping from group to trace color
    group_to_color = {}
    groups_list = sorted(df['Group'].unique())
    
    # First, try to match traces by name
    for trace in fig.data:
        if hasattr(trace, 'name') and trace.name:
            trace_name = str(trace.name).lower()
            for group in groups_list:
                group_str = str(group).lower()
                # Match various patterns: "Group 1", "1", etc.
                if (group_str in trace_name or trace_name in group_str or 
                    f"group {group_str}" in trace_name or trace_name == group_str):
                    # Extract color from trace
                    color = None
                    if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                        color = trace.marker.color
                        if isinstance(color, (list, tuple)) and len(color) > 0:
                            color = color[0]
                    elif hasattr(trace, 'line') and trace.line and hasattr(trace.line, 'color'):
                        color = trace.line.color
                    
                    if color:
                        group_to_color[group] = color
                    break
    
    # If we didn't match all groups, try matching by trace order
    if len(group_to_color) < len(groups_list):
        trace_index = 0
        for group in groups_list:
            if group not in group_to_color and trace_index < len(fig.data):
                trace = fig.data[trace_index]
                color = None
                if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                    color = trace.marker.color
                    if isinstance(color, (list, tuple)) and len(color) > 0:
                        color = color[0]
                elif hasattr(trace, 'line') and trace.line and hasattr(trace.line, 'color'):
                    color = trace.line.color
                
                if color:
                    group_to_color[group] = color
                trace_index += 1
    
    # Add scatter points for each group - match group color with black outline
    for group in df['Group'].unique():
        group_data = df[df['Group'] == group]
        if group_data.empty:
            continue
        
        # Get color for this group, fallback to black if not found
        point_color = group_to_color.get(group, 'black')
        
        # For bar plots, use group as x directly (centered on bar)
        # For scatter/line plots, also use group as x
        x_positions = [group] * len(group_data)
        
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=group_data[y_col],
            mode='markers',
            marker=dict(
                size=4,
                color=point_color,
                opacity=0.7,
                line=dict(width=1, color='black')
            ),
            showlegend=False,
            hoverinfo='y',
            name=f'Individual Points (Group {group})'
        ))


def create_cell_type_comparison_plot(df: DataFrame, freq_cols: List[str], plot_type: str, filter_options=None, **kwargs):
    """
    Create a plot comparing all cell types with cell types in legend.
    
    Args:
        df: DataFrame containing the data
        freq_cols: List of frequency columns to compare
        plot_type: Type of plot ('scatter', 'bar', 'box', 'line', 'histogram')
        **kwargs: Additional keyword arguments
            show_individual_points: bool - Whether to overlay individual data points (can be combined with error_bars)
            error_bars: bool - Whether to show error bars (can be combined with show_individual_points)
        
    Returns:
        Plotly Figure object
    """
    logger.debug(f"Creating cell type comparison plot with {len(freq_cols)} columns: {freq_cols}")
    logger.debug(f"Input DataFrame shape: {df.shape}")
    logger.debug(f"Input DataFrame columns: {list(df.columns)}")
    
    # Extract internal-only option so it isn't passed to Plotly
    user_group_labels = kwargs.pop('user_group_labels', None)
    kwargs.pop('fixed_layout', None)
    
    # Extract display options (can be enabled independently)
    show_individual_points = kwargs.pop('show_individual_points', False)
    error_bars = kwargs.pop('error_bars', True)

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
        # Determine error_y parameter based on error_bars flag
        error_y_col = 'sem' if error_bars else None
        
        # scatter, bar, line → use aggregated df with SEM
        if plot_type == "bar":
            # Vertical grouped bars: populations next to one another
            kwargs.setdefault('barmode', 'group')
            fig = build_plot_from_df("bar", combined_df, x='Group', y='mean', color='Cell Type', error_y=error_y_col, **kwargs)
        else:
            fig = build_plot_from_df(plot_type, combined_df, x='Group', y='mean', color='Cell Type', error_y=error_y_col, **kwargs)
        logger.debug(f"Created {plot_type} plot with {len(fig.data)} traces")
        
        # Overlay individual points if requested
        if show_individual_points and plot_type in ("bar", "scatter", "line"):
            _add_cell_type_individual_points_overlay(fig, df, freq_cols, plot_type)

    logger.debug("Figure created successfully, applying legend configuration")
    
    # Apply standardized legend configuration to ALL plot types
    width = kwargs.get('width', DEFAULT_WIDTH)
    height = kwargs.get('height', DEFAULT_HEIGHT)

    legend_title = select_legend_title(context='comparison')

    fig = apply_common_layout(
        fig=fig,
        df=combined_df,
        color_col='Cell Type',
        width=width,
        height=height,
        legend_title=legend_title,
        show_mean_sem_label=True
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
    
    # Ensure all x-axis ticks are shown with customized labels if available
    fig = apply_group_tick_labels(fig, combined_df, user_group_labels, width, height)
    
    logger.debug(f"Final figure layout: width={fig.layout.width}, height={fig.layout.height}")
    logger.debug(f"Final figure has {len(fig.data)} traces")
    
    return fig


def _add_timecourse_individual_points_overlay(fig: Figure, df: DataFrame, time_col: str, value_col: str, group_col: Optional[str]):
    """
    Add individual data points as an overlay on timecourse plots.
    Points match the color of their group with a black outline.
    
    Args:
        fig: Plotly Figure to add points to
        df: Original DataFrame with raw data
        time_col: Time column name
        value_col: Value column name
        group_col: Group column name (optional)
    """
    if time_col not in df.columns or value_col not in df.columns:
        return
    
    if group_col and group_col in df.columns:
        # Build mapping from group to trace color
        group_to_color = {}
        groups_list = sorted(df[group_col].unique())
        
        # First, try to match traces by name
        for trace in fig.data:
            if hasattr(trace, 'name') and trace.name:
                trace_name = str(trace.name).lower()
                for group in groups_list:
                    group_str = str(group).lower()
                    # Match various patterns: "Group 1", "1", etc.
                    if (group_str in trace_name or trace_name in group_str or 
                        f"group {group_str}" in trace_name or trace_name == group_str):
                        # Extract color from trace
                        color = None
                        if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                            color = trace.marker.color
                            if isinstance(color, (list, tuple)) and len(color) > 0:
                                color = color[0]
                        elif hasattr(trace, 'line') and trace.line and hasattr(trace.line, 'color'):
                            color = trace.line.color
                        
                        if color:
                            group_to_color[group] = color
                        break
        
        # If we didn't match all groups, try matching by trace order
        if len(group_to_color) < len(groups_list):
            trace_index = 0
            for group in groups_list:
                if group not in group_to_color and trace_index < len(fig.data):
                    trace = fig.data[trace_index]
                    color = None
                    if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                        color = trace.marker.color
                        if isinstance(color, (list, tuple)) and len(color) > 0:
                            color = color[0]
                    elif hasattr(trace, 'line') and trace.line and hasattr(trace.line, 'color'):
                        color = trace.line.color
                    
                    if color:
                        group_to_color[group] = color
                    trace_index += 1
        
        # Add points for each group - match group color with black outline
        for group in df[group_col].unique():
            group_data = df[df[group_col] == group]
            if group_data.empty:
                continue
            
            # Get color for this group, fallback to black if not found
            point_color = group_to_color.get(group, 'black')
            
            fig.add_trace(go.Scatter(
                x=group_data[time_col],
                y=group_data[value_col],
                mode='markers',
                marker=dict(
                    size=4,
                    color=point_color,
                    opacity=0.7,
                    line=dict(width=1, color='black')
                ),
                showlegend=False,
                hoverinfo='x+y',
                name=f'Individual Points (Group {group})'
            ))
    else:
        # No group column, add all points with default color
        # Try to get color from first trace if available
        point_color = 'black'
        if len(fig.data) > 0:
            trace = fig.data[0]
            if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                color = trace.marker.color
                if isinstance(color, (list, tuple)) and len(color) > 0:
                    color = color[0]
                point_color = color
            elif hasattr(trace, 'line') and trace.line and hasattr(trace.line, 'color'):
                point_color = trace.line.color
        
        fig.add_trace(go.Scatter(
            x=df[time_col],
            y=df[value_col],
            mode='markers',
            marker=dict(
                size=4,
                color=point_color,
                opacity=0.7,
                line=dict(width=1, color='black')
            ),
            showlegend=False,
            hoverinfo='x+y',
            name='Individual Points'
        ))


def _add_cell_type_individual_points_overlay(fig: Figure, df: DataFrame, freq_cols: List[str], plot_type: str):
    """
    Add individual data points as an overlay for cell type comparison plots.
    Points match the color of their cell type with a black outline.
    
    Args:
        fig: Plotly Figure to add points to
        df: Original DataFrame with raw data
        freq_cols: List of frequency column names
        plot_type: Type of plot ('bar', 'scatter', 'line')
    """
    if 'Group' not in df.columns:
        return
    
    # Get cell type order from figure traces (to match bar positions)
    from .column_utils import build_unique_cell_type_labels, enhance_cell_type_name
    label_map = build_unique_cell_type_labels(freq_cols)
    
    # Build mapping from cell type label to trace index and color
    # Trace names use enhanced labels (from aggregate_multiple_metrics_by_group),
    # so we need to enhance our labels for proper matching
    cell_type_to_index = {}
    cell_type_to_color = {}
    trace_names = []
    for i, trace in enumerate(fig.data):
        if hasattr(trace, 'name') and trace.name:
            trace_names.append(trace.name)
            # Try to match trace name to cell type label
            # Trace names are enhanced labels, so enhance our labels for comparison
            for freq_col, label in label_map.items():
                # Enhance the label to match what's in the trace name
                enhanced_label = enhance_cell_type_name(label, freq_col)
                # Match using enhanced label, or fallback to basic label or column name
                if enhanced_label == trace.name or label == trace.name or freq_col in trace.name:
                    cell_type_to_index[freq_col] = i
                    # Extract color from trace
                    if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                        color = trace.marker.color
                        if isinstance(color, (list, tuple)) and len(color) > 0:
                            color = color[0]
                        cell_type_to_color[freq_col] = color
                    elif hasattr(trace, 'line') and trace.line and hasattr(trace.line, 'color'):
                        color = trace.line.color
                        cell_type_to_color[freq_col] = color
                    break
    
    # If we couldn't match by name, try to match by comparing enhanced labels with trace names
    # This handles cases where exact matching failed
    if len(cell_type_to_index) < len(freq_cols):
        from .column_utils import enhance_cell_type_name
        # Build a reverse map from enhanced labels to freq_cols
        enhanced_to_freq_col = {}
        for freq_col, label in label_map.items():
            enhanced_label = enhance_cell_type_name(label, freq_col)
            enhanced_to_freq_col[enhanced_label] = freq_col
        
        # Try matching remaining traces
        for i, trace in enumerate(fig.data):
            if hasattr(trace, 'name') and trace.name:
                trace_name = trace.name
                # Check if this trace name matches any enhanced label
                if trace_name in enhanced_to_freq_col:
                    freq_col = enhanced_to_freq_col[trace_name]
                    if freq_col not in cell_type_to_index:
                        cell_type_to_index[freq_col] = i
                        # Extract color from trace
                        if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                            color = trace.marker.color
                            if isinstance(color, (list, tuple)) and len(color) > 0:
                                color = color[0]
                            cell_type_to_color[freq_col] = color
                        elif hasattr(trace, 'line') and trace.line and hasattr(trace.line, 'color'):
                            cell_type_to_color[freq_col] = trace.line.color
    
    # Final fallback: use order in freq_cols if still unmatched
    if len(cell_type_to_index) < len(freq_cols):
        logger.warning(f"Could not match all cell types to traces. Matched {len(cell_type_to_index)}/{len(freq_cols)}")
        for i, freq_col in enumerate(freq_cols):
            if freq_col not in cell_type_to_index:
                # Use the index in freq_cols as a fallback, but try to find an available trace
                trace_idx = min(i, len(fig.data) - 1) if fig.data else 0
                cell_type_to_index[freq_col] = trace_idx
                # Try to get color from trace at this index
                if trace_idx < len(fig.data):
                    trace = fig.data[trace_idx]
                    if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                        color = trace.marker.color
                        if isinstance(color, (list, tuple)) and len(color) > 0:
                            color = color[0]
                        cell_type_to_color[freq_col] = color
                    elif hasattr(trace, 'line') and trace.line and hasattr(trace.line, 'color'):
                        cell_type_to_color[freq_col] = trace.line.color
    
    num_cell_types = len(freq_cols)
    
    # For grouped bars, Plotly distributes bars within a narrower range
    # Default bargap=0.2 means group width is ~0.8
    # Each bar within group gets 0.8/num_cell_types width
    total_group_width = 0.8  # 1 - default bargap
    individual_bar_width = total_group_width / num_cell_types
    
    # Add points for each cell type and group combination
    for freq_col in freq_cols:
        cell_type_label = label_map.get(freq_col, freq_col)
        cell_type_index = cell_type_to_index.get(freq_col, freq_cols.index(freq_col))
        
        # Get color for this cell type, fallback to black if not found
        point_color = cell_type_to_color.get(freq_col, 'black')
        
        # Calculate x offset for this cell type's bar position
        # Center the bars: first bar starts at -total_group_width/2 + individual_bar_width/2
        offset = -total_group_width/2 + individual_bar_width/2 + (cell_type_index * individual_bar_width)
        
        for group in df['Group'].unique():
            group_data = df[df['Group'] == group]
            if group_data.empty or freq_col not in group_data.columns:
                continue
            
            # Calculate x positions: group value + offset for this cell type
            try:
                # Convert group to numeric if possible for positioning
                group_numeric = float(group) if isinstance(group, (int, float, str)) and str(group).replace('.', '').isdigit() else group
                x_positions = [group_numeric + offset] * len(group_data)
            except (ValueError, TypeError):
                # Fallback: use group as-is (may not position correctly for non-numeric groups)
                x_positions = [group] * len(group_data)
            
            fig.add_trace(go.Scatter(
                x=x_positions,
                y=group_data[freq_col],
                mode='markers',
                marker=dict(
                    size=4,
                    color=point_color,
                    opacity=0.7,
                    line=dict(width=1, color='black')
                ),
                showlegend=False,
                hoverinfo='y',
                name=f'Individual Points ({cell_type_label})'
            ))


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
    width = kwargs.get('width', DEFAULT_WIDTH)
    height = kwargs.get('height', DEFAULT_HEIGHT)

    legend_title = select_legend_title(color_col=color_col, context='single')

    fig = apply_common_layout(
        fig=fig,
        df=df,
        color_col=color_col,
        width=width,
        height=height,
        legend_title=legend_title,
        show_mean_sem_label=True
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
    
    # Map group tick labels if plotting by Group on x-axis
    if x == 'Group' and 'Group' in df.columns:
        fig = apply_group_tick_labels(fig, df, user_group_labels, width, height)
    
    return fig


# Export available functions
__all__ = [
    'create_single_metric_plot',
    'create_cell_type_comparison_plot', 
    'create_basic_plot',
    'create_timecourse_visualization',
    'plot',
    'compare_groups',
    'scatter',
    'bar',
    'box',
    'histogram'
]











 


def create_timecourse_visualization(
    data: Union[str, DataFrame],
    time_column: Optional[str] = None,
    metric: Optional[str] = None,
    group_by: Optional[str] = None,
    plot_type: str = "line",
    aggregation: str = "mean_sem",
    max_cell_types: int = 10,
    sample_size: Optional[int] = None,
    filter_options: Optional[Dict] = None,
    population_filter: Optional[str] = None,
    save_html: Optional[str] = None,
    show_individual_points: bool = False,
    error_bars: bool = True,
    **kwargs
) -> Figure:
    """
    Unified timecourse visualization function - single entry point for all timecourse plots.
    
    Args:
        data: CSV file path or DataFrame
        time_column: Time column name (auto-detected if None)
        metric: Metric type (e.g., "Freq. of Parent") or specific column name
        group_by: Column to group data by (e.g., "Group", "Treatment")
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
    
    # Pass display options to plot creation functions
    kwargs['show_individual_points'] = show_individual_points
    kwargs['error_bars'] = error_bars
    
    # Determine visualization strategy
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
    # Extract display options (can be enabled independently)
    show_individual_points = kwargs.pop('show_individual_points', False)
    error_bars = kwargs.pop('error_bars', True)
    
    # Debug logging
    logger.info(f"Creating single metric timecourse for column: {value_col}")
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Time column: {time_col}, unique values: {df[time_col].dropna().unique()}")
    logger.info(f"Value column: {value_col}, range: {df[value_col].min():.3f} to {df[value_col].max():.3f}")
    if group_col:
        logger.info(f"Group column: {group_col}, unique values: {df[group_col].dropna().unique()}")
    
    # Store original data for individual points overlay
    original_df = df.copy()
    
    # Apply aggregation if requested
    if aggregation == "mean_sem" and group_col:
        # Centralized timecourse aggregation
        plot_df = timecourse_group_stats(df, value_col, time_col=time_col, group_col=group_col)
        y_col = 'mean'
        error_y = 'sem' if error_bars else None
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
        
        # Overlay individual points if requested and data was aggregated
        if show_individual_points and aggregation == "mean_sem" and group_col:
            _add_timecourse_individual_points_overlay(fig, original_df, time_col, value_col, group_col)
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
    width = kwargs.get('width', DEFAULT_WIDTH)
    height = kwargs.get('height', DEFAULT_HEIGHT)
    
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
    # Extract display options (can be enabled independently)
    show_individual_points = kwargs.pop('show_individual_points', False)
    error_bars = kwargs.pop('error_bars', True)
    
    fig = go.Figure()
    
    # Store original data for individual points overlay
    original_df = df.copy()
    
    # Apply aggregation if requested
    if aggregation == "mean_sem" and group_col:
        # Centralized multi-column timecourse aggregation
        plot_df = timecourse_group_stats_multi(
            df,
            value_cols=value_cols,
            time_col=time_col,
            group_col=group_col,
            long_name='value_col',
        )
        y_col = 'mean'
        error_y = 'sem' if error_bars else None
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
                    
                    # Add error bars if available and enabled
                    error_y_data = None
                    if error_y and error_y in group_data.columns:
                        error_y_data = dict(
                            type='data',
                            array=group_data[error_y],
                            visible=True
                        )
                    
                    # Use just "Group" prefix for legend
                    trace_name = f"Group {group}"
                    
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
    width = kwargs.get('width', DEFAULT_WIDTH)
    height = kwargs.get('height', DEFAULT_HEIGHT)
    
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
    
    # Overlay individual points if requested and data was aggregated
    if show_individual_points and aggregation == "mean_sem" and group_col:
        for value_col in value_cols:
            _add_timecourse_individual_points_overlay(fig, original_df, time_col, value_col, group_col)
    
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
    
    # Handle case where y is a metric type (like "Freq. of Parent").
    if y and y not in df.columns:
        single_col, multi_cols = resolve_metric_selection(df, y)
        logger.debug(f"Resolved metric selection for y='{y}': single={single_col}, multi={multi_cols}")
        if multi_cols:
            result_fig = create_cell_type_comparison_plot(df, multi_cols, plot_type, filter_options=filter_options, **kwargs)
            if save_html:
                from .plotly_renderer import PlotlyRenderer
                renderer = PlotlyRenderer()
                renderer.export_to_html_optimized(result_fig, save_html, 'minimal')
                logger.info(f"Saved cell type comparison plot to {save_html}")
            return result_fig
        if single_col:
            y = single_col
        else:
            raise ValueError(f"Column '{y}' not found in data and not recognized as a metric type")
    
    # Ensure consistent sizing
    if 'width' not in kwargs:
        kwargs['width'] = DEFAULT_WIDTH
    if 'height' not in kwargs:
        kwargs['height'] = DEFAULT_HEIGHT
    
    # Create plot (display options like show_individual_points and error_bars are passed through kwargs)
    if plot_type == "histogram":
        fig = create_basic_plot(df, x, x, "histogram", filter_options=filter_options, **kwargs)
    elif x == 'Group' and y in df.columns:
        # Use single metric plot for Group-based plots to get aggregation and overlay support
        fig = create_single_metric_plot(df, y, plot_type, filter_options=filter_options, **kwargs)
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
        kwargs['width'] = DEFAULT_WIDTH
    if 'height' not in kwargs:
        kwargs['height'] = DEFAULT_HEIGHT
    
    # Resolve metric selection using unified helper
    single_col, multi_cols = resolve_metric_selection(df, metric)
    if multi_cols:
        # Use cell type comparison with multiple columns; choose box by default for distributions
        result_fig = create_cell_type_comparison_plot(df, multi_cols, plot_type, filter_options=filter_options, **kwargs)
        if save_html:
            from .plotly_renderer import PlotlyRenderer
            renderer = PlotlyRenderer()
            renderer.export_to_html_optimized(result_fig, save_html, 'minimal')
            logger.info(f"Saved group comparison plot to {save_html}")
        return result_fig
    if single_col:
        metric = single_col
    else:
        raise ValueError(f"No columns found for metric '{metric}' and no fallback columns available")
    
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
        comprehensive_title = create_comprehensive_plot_title(df, metric_name, [metric], filter_options=filter_options)
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