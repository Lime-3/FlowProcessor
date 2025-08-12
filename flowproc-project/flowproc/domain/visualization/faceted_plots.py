"""
Faceted plot creation functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional, Callable, Dict, Any


from .plot_config import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, MARGIN, VERTICAL_SPACING, HORIZONTAL_SPACING,
    MAX_CELL_TYPES, SUBPLOT_HEIGHT_PER_ROW, DEFAULT_TRACE_CONFIG
)
from .plot_utils import (
    format_time_title, validate_plot_data, limit_cell_types, calculate_subplot_dimensions, calculate_aspect_ratio_dimensions
)
from .column_utils import create_enhanced_title, extract_cell_type_name, get_base_columns, create_comprehensive_plot_title, create_timecourse_plot_title, extract_metric_name
from .data_aggregation import prepare_data_for_plotting

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
        subplot_titles = [create_enhanced_title(df, col, time_col) for col in value_cols]
    
    # Calculate appropriate vertical spacing based on number of rows
    if rows > 1:
        # Ensure vertical spacing doesn't exceed Plotly's limit
        max_spacing = 1.0 / (rows - 1) - 0.01  # Leave a small margin
        adjusted_vertical_spacing = min(vertical_spacing, max_spacing)
    else:
        adjusted_vertical_spacing = vertical_spacing
    
    # Create subplots
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=adjusted_vertical_spacing,
        horizontal_spacing=horizontal_spacing
    )
    
    # Add traces
    for i in range(rows):
        row = i + 1
        col_idx = 1
        
        if facet_by:
            # Facet by groups/tissues
            facet_val = facet_values[i]
            facet_data = df[df[facet_by] == facet_val]
            
            for col in value_cols:
                base_columns = get_base_columns(df, time_col)
                plot_df = prepare_data_for_plotting(facet_data, base_columns, col)
                
                if not plot_df.empty:
                    # Apply aggregation if requested
                    if aggregation == "mean_sem" and group_col and group_col in plot_df.columns:
                        # Aggregate by both group and time
                        agg_df = plot_df.groupby([group_col, time_col])[col].agg(['mean', 'std', 'count']).reset_index()
                        agg_df['sem'] = agg_df['std'] / np.sqrt(agg_df['count'])
                        
                        # Add traces for each group with error bars
                        for group in agg_df[group_col].unique():
                            group_data = agg_df[agg_df[group_col] == group]
                            trace_name = f"{trace_name_fn(col) if trace_name_fn else extract_cell_type_name(col)} - {group}"
                            
                            # Add error bars
                            error_y_data = dict(
                                type='data',
                                array=group_data['sem'],
                                visible=True
                            )
                            
                            fig.add_trace(
                                go.Scatter(
                                    x=group_data[time_col],
                                    y=group_data['mean'],
                                    mode='lines+markers',
                                    name=trace_name,
                                    showlegend=False,  # Disable individual trace legend
                                    legendgroup=f"subplot_{row}",
                                    error_y=error_y_data,
                                    **DEFAULT_TRACE_CONFIG
                                ),
                                row=row, col=col_idx
                            )
                    else:
                        # Use raw data without error bars
                        trace_name = trace_name_fn(col) if trace_name_fn else extract_cell_type_name(col)
                        fig.add_trace(
                            go.Scatter(
                                x=plot_df[time_col],
                                y=plot_df[col],
                                mode='lines+markers',
                                name=trace_name,
                                showlegend=False,  # Disable individual trace legend
                                legendgroup=f"subplot_{row}",
                                **DEFAULT_TRACE_CONFIG
                            ),
                            row=row, col=col_idx
                        )
        else:
            # Facet by cell types - each cell type gets its own subplot
            logger.info(f"Processing {len(value_cols)} cell types for faceted plot")
            for i in range(len(value_cols)):  # Loop through ALL cell types
                col = value_cols[i]
                logger.info(f"Processing cell type {i+1}/{len(value_cols)}: {col}")
                
                base_columns = get_base_columns(df, time_col)
                plot_df = prepare_data_for_plotting(df, base_columns, col)
                
                # Calculate which subplot this cell type should go in
                subplot_row = (i // cols) + 1
                subplot_col = (i % cols) + 1
                
                logger.info(f"Adding cell type '{col}' to subplot ({subplot_row}, {subplot_col})")
                
                for group in plot_df['Group'].unique():
                    group_data = plot_df[plot_df['Group'] == group]
                    if not group_data.empty:
                        # Apply aggregation if requested
                        if aggregation == "mean_sem" and group_col and group_col in plot_df.columns:
                            # Aggregate by time for this group
                            time_agg = group_data.groupby(time_col)[col].agg(['mean', 'std', 'count']).reset_index()
                            time_agg['sem'] = time_agg['std'] / np.sqrt(time_agg['count'])
                            
                            # Add error bars
                            error_y_data = dict(
                                type='data',
                                array=time_agg['sem'],
                                visible=True
                            )
                            
                            # Make trace names unique by including cell type information
                            trace_name = f"{extract_cell_type_name(col)} (Group {group})"
                            logger.info(f"Adding trace '{trace_name}' for group {group} with SEM error bars")
                            fig.add_trace(
                                go.Scatter(
                                    x=time_agg[time_col],
                                    y=time_agg['mean'],
                                    mode='lines+markers',
                                    name=trace_name,
                                    showlegend=False,  # Disable individual trace legend
                                    legendgroup=f"subplot_{subplot_row}",  # Group by row for bottom legend
                                    error_y=error_y_data,
                                    **DEFAULT_TRACE_CONFIG
                                ),
                                row=subplot_row, col=subplot_col
                            )
                        else:
                            # Use raw data without error bars
                            # Make trace names unique by including cell type information
                            trace_name = f"{extract_cell_type_name(col)} (Group {group})"
                            logger.info(f"Adding trace '{trace_name}' for group {group}")
                            fig.add_trace(
                                go.Scatter(
                                    x=group_data[time_col],
                                    y=group_data[col],
                                    mode='lines+markers',
                                    name=trace_name,
                                    showlegend=False,  # Disable individual trace legend
                                    legendgroup=f"subplot_{subplot_row}",  # Group by row for bottom legend
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
    
    # Enable legend for faceted plots - use the first value column as reference for color grouping
    color_col = 'Group' if 'Group' in df.columns else None
    
    # Determine appropriate legend title based on plot type
    if facet_by:
        legend_title = "Groups"
    else:
        legend_title = "Cell Types"
    
    fig = configure_legend(
        fig, df, color_col, is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
    
    # Update layout with enhanced title
    if not title or title in ["Time Course by Cell Type", "Time Course by Group", "Time Course by Tissue"]:
        # Create timecourse-specific title if using default timecourse titles
        if facet_by:
            metric_name = extract_metric_name(value_cols[0]) if value_cols else "Frequency"
            logger.debug(f"Faceted plot - Creating title for facet_by mode with metric: {metric_name}")
            enhanced_title = create_timecourse_plot_title(df, metric_name, value_cols, filter_options=filter_options)
            logger.debug(f"Faceted plot - Enhanced title created: {enhanced_title}")
        else:
            metric_name = extract_metric_name(value_cols[0]) if value_cols else "Frequency"
            logger.debug(f"Faceted plot - Creating title for cell type mode with metric: {metric_name}")
            enhanced_title = create_timecourse_plot_title(df, metric_name, value_cols, filter_options=filter_options)
            logger.debug(f"Faceted plot - Enhanced title created: {enhanced_title}")
        title = enhanced_title
    
    logger.debug(f"Faceted plot - Final title: {title}")
    
    # Debug: Log the title before applying it to the plot
    logger.info(f"Applying title to faceted plot: '{title}'")
    
    fig.update_layout(
        title=title,
        margin=dict(l=50, r=300, t=80, b=50),  # Increased top margin for timecourse title spacing
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
    
    # Create individual legends for each subplot
    # Instead of individual legends, create a unified bottom legend with row distribution
    all_traces = []
    all_names = []
    
    # Collect all traces and names
    for trace in fig.data:
        if trace.name not in all_names:
            all_traces.append(trace)
            all_names.append(trace.name)
    
    if all_traces:
        # Create a bottom legend with row distribution
        # Group traces by their subplot position for better organization
        legend_items = []
        
        # Debug: Show all traces and their legend groups
        logger.info(f"All traces: {[trace.name for trace in all_traces]}")
        for trace in all_traces:
            logger.info(f"Trace '{trace.name}' has legendgroup: {getattr(trace, 'legendgroup', 'None')}")
        
        # First, add row headers
        for row in range(1, rows + 1):
            row_traces = [trace for trace in all_traces if hasattr(trace, 'legendgroup') and f"subplot_{row}" in trace.legendgroup]
            logger.info(f"Row {row} traces: {[trace.name for trace in row_traces]}")
            
            if row_traces:
                # Add row header
                legend_items.append(f"<b>Row {row}:</b>")
                
                # Add traces for this row
                for trace in row_traces:
                    # Get the actual color from the trace
                    color = "black"  # default
                    if hasattr(trace, 'line') and hasattr(trace.line, 'color') and trace.line.color:
                        color = trace.line.color
                    elif hasattr(trace, 'marker') and hasattr(trace.marker, 'color') and trace.marker.color:
                        color = trace.marker.color
                    else:
                        # Generate a color if none is set
                        color = f"hsl({len(legend_items) * 360 // max(len(all_traces), 1)}, 70%, 50%)"
                    
                    legend_items.append(f'<span style="color: {color};">●</span> {trace.name}')
                
                # Add spacing between rows
                if row < rows:
                    legend_items.append("")  # Empty line for spacing
        
        logger.info(f"Legend items: {legend_items}")
        
        legend_text = "<br>".join(legend_items)
        
        # Add bottom legend annotation
        fig.add_annotation(
            text=legend_text,
            xref="paper",
            yref="paper",
            x=0.5,  # Center horizontally
            y=-0.15,  # Below the plots
            xanchor="center",
            yanchor="top",
            showarrow=False,
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='rgba(0,0,0,0.3)',
            borderwidth=1,
            font=dict(size=11, color="black"),
            align="center"
        )
    
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