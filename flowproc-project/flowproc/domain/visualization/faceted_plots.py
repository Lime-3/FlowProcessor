"""
Faceted plot creation functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional, Callable


from .plot_config import (
    DEFAULT_WIDTH, VERTICAL_SPACING, HORIZONTAL_SPACING,
    MAX_CELL_TYPES, DEFAULT_TRACE_CONFIG
)
from .plot_utils import (
    format_time_title, validate_plot_data, limit_cell_types, calculate_aspect_ratio_dimensions
)
from .column_utils import create_enhanced_title, extract_cell_type_name, get_base_columns, create_timecourse_plot_title, extract_metric_name
from .data_aggregation import prepare_data_for_plotting
from ..aggregation import timecourse_group_stats

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame
Figure = go.Figure


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
    
    # Determine subplot structure: always a single horizontal row.
    if facet_by:
        facet_values = sorted(df[facet_by].unique())
        rows, cols = 1, len(facet_values)
    else:
        rows, cols = 1, len(value_cols)
    
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
        subplot_titles = [create_enhanced_title(df, col, time_col) for col in value_cols]
    
    # With a single row, use provided vertical spacing directly
    adjusted_vertical_spacing = vertical_spacing
    
    # Create subplots
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=adjusted_vertical_spacing,
        horizontal_spacing=horizontal_spacing
    )
    
    # Add traces
    if facet_by:
        # Each facet value becomes a column in a single horizontal row
        for j, facet_val in enumerate(facet_values):
            facet_data = df[df[facet_by] == facet_val]
            subplot_row = 1
            subplot_col = j + 1
            for col in value_cols:
                base_columns = get_base_columns(df, time_col)
                plot_df = prepare_data_for_plotting(facet_data, base_columns, col)
                if plot_df.empty:
                    continue
                if aggregation == "mean_sem" and group_col and group_col in plot_df.columns:
                    agg_df = timecourse_group_stats(plot_df, col, time_col=time_col, group_col=group_col)
                    for group in agg_df[group_col].unique():
                        group_data = agg_df[agg_df[group_col] == group]
                        trace_name = f"Group {group}"
                        error_y_data = dict(type='data', array=group_data['sem'], visible=True)
                        fig.add_trace(
                            go.Scatter(
                                x=group_data[time_col],
                                y=group_data['mean'],
                                mode='lines+markers',
                                name=trace_name,
                                showlegend=False,
                                legendgroup=f"subplot_{subplot_col}",
                                error_y=error_y_data,
                                **DEFAULT_TRACE_CONFIG
                            ),
                            row=subplot_row, col=subplot_col
                        )
                else:
                    trace_name = trace_name_fn(col) if trace_name_fn else extract_cell_type_name(col)
                    fig.add_trace(
                        go.Scatter(
                            x=plot_df[time_col],
                            y=plot_df[col],
                            mode='lines+markers',
                            name=trace_name,
                            showlegend=False,
                            legendgroup=f"subplot_{subplot_col}",
                            **DEFAULT_TRACE_CONFIG
                        ),
                        row=subplot_row, col=subplot_col
                    )
    else:
        # Each cell type becomes a column in a single horizontal row
        logger.info(f"Processing {len(value_cols)} cell types for faceted plot (horizontal)")
        for i in range(len(value_cols)):
            col = value_cols[i]
            base_columns = get_base_columns(df, time_col)
            plot_df = prepare_data_for_plotting(df, base_columns, col)
            subplot_row = 1
            subplot_col = i + 1
            for group in plot_df['Group'].unique():
                group_data = plot_df[plot_df['Group'] == group]
                if group_data.empty:
                    continue
                if aggregation == "mean_sem" and group_col and group_col in plot_df.columns:
                    time_agg = timecourse_group_stats(group_data, col, time_col=time_col, group_col=None)
                    error_y_data = dict(type='data', array=time_agg['sem'], visible=True)
                    trace_name = f"Group {group}"
                    fig.add_trace(
                        go.Scatter(
                            x=time_agg[time_col],
                            y=time_agg['mean'],
                            mode='lines+markers',
                            name=trace_name,
                            showlegend=False,
                            legendgroup=f"subplot_{subplot_col}",
                            error_y=error_y_data,
                            **DEFAULT_TRACE_CONFIG
                        ),
                        row=subplot_row, col=subplot_col
                    )
                else:
                    trace_name = f"Group {group}"
                    fig.add_trace(
                        go.Scatter(
                            x=group_data[time_col],
                            y=group_data[col],
                            mode='lines+markers',
                            name=trace_name,
                            showlegend=False,
                            legendgroup=f"subplot_{subplot_col}",
                            **DEFAULT_TRACE_CONFIG
                        ),
                        row=subplot_row, col=subplot_col
                    )
    
    # Calculate height maintaining aspect ratio if not provided
    if height is None:
        # Get labels for aspect ratio calculation
        if facet_by:
            labels = df[facet_by].unique().tolist()
            legend_items = len(value_cols)
        else:
            labels = value_cols
            legend_items = len(df['Group'].unique()) if 'Group' in df.columns else 0
        
        dimensions = calculate_aspect_ratio_dimensions(
            labels=labels,
            legend_items=legend_items,
            num_subplots=rows,
            base_width=width
        )
        height = dimensions['height']
    
    # Apply standardized legend configuration
    from .legend_config import configure_legend
    color_col = 'Group' if 'Group' in df.columns else None
    legend_title = "Groups" if facet_by else "Cell Types"
    fig = configure_legend(fig, df, color_col, is_subplot=False, width=width, height=height,
                           legend_title=legend_title, show_mean_sem_label=True)
    
    # Update layout with enhanced title when not provided by caller
    if not title:
        # Create timecourse-specific title if using default timecourse titles
        if facet_by:
            metric_name = extract_metric_name(value_cols[0]) if value_cols else "Frequency"
            logger.debug(f"Faceted plot - Creating title for facet_by mode with metric: {metric_name}")
            enhanced_title = create_timecourse_plot_title(df, metric_name, value_cols, filter_options=filter_options)
            logger.debug(f"Faceted plot - Enhanced title created: {enhanced_title}")
        else:
            # Keep legacy default title for tests when faceting by cell type list without explicit title
            title = "Time Course by Cell Type"
    
    logger.debug(f"Faceted plot - Final title: {title}")
    
    # Debug: Log the title before applying it to the plot
    logger.info(f"Applying title to faceted plot: '{title}'")
    
    fig.update_layout(
        title=title,
        margin=dict(l=50, r=300, t=80, b=50),
        width=width,
        height=height
    )
    
    # Debug: Verify the title was applied
    if hasattr(fig.layout, 'title') and hasattr(fig.layout.title, 'text'):
        logger.info(f"Title applied successfully: '{fig.layout.title.text}'")
    else:
        logger.warning("Title not found in figure layout after update")
    
    # Update axes labels
    for i in range(1, rows + 1):
        fig.update_xaxes(title_text=time_col, row=i, col=1)
        if facet_by:
            fig.update_yaxes(title_text="Frequency (%)", row=i, col=1)
        else:
            fig.update_yaxes(title_text="Frequency (%)", row=i, col=1)
    
    # Remove vertical bottom legend annotation; global legend configuration is applied above
    
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