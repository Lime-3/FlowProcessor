"""
Faceted plot creation functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional, Callable, Dict, Any

from .legend_config import configure_legend
from .plot_config import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, MARGIN, VERTICAL_SPACING, HORIZONTAL_SPACING,
    MAX_CELL_TYPES, SUBPLOT_HEIGHT_PER_ROW, DEFAULT_TRACE_CONFIG
)
from .plot_utils import (
    format_time_title, validate_plot_data, limit_cell_types, calculate_subplot_dimensions
)
from .column_utils import create_enhanced_title, extract_cell_type_name, get_base_columns
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
    max_cell_types: int = MAX_CELL_TYPES
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
    
    # Create subplots
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=vertical_spacing,
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
                    trace_name = trace_name_fn(col) if trace_name_fn else extract_cell_type_name(col)
                    fig.add_trace(
                        go.Scatter(
                            x=plot_df[time_col],
                            y=plot_df[col],
                            mode='lines+markers',
                            name=trace_name,
                            showlegend=False,
                            legendgroup=f"subplot_{row}",
                            **DEFAULT_TRACE_CONFIG
                        ),
                        row=row, col=col_idx
                    )
        else:
            # Facet by cell types
            col = value_cols[i]
            base_columns = get_base_columns(df, time_col)
            plot_df = prepare_data_for_plotting(df, base_columns, col)
            
            for group in plot_df['Group'].unique():
                group_data = plot_df[plot_df['Group'] == group]
                if not group_data.empty:
                    trace_name = trace_name_fn(group) if trace_name_fn else f"Group {group}"
                    fig.add_trace(
                        go.Scatter(
                            x=group_data[time_col],
                            y=group_data[col],
                            mode='lines+markers',
                            name=trace_name,
                            showlegend=False,
                            legendgroup=f"subplot_{row}",
                            **DEFAULT_TRACE_CONFIG
                        ),
                        row=row, col=col_idx
                    )
    
    # Calculate height if not provided
    if height is None:
        height = max(DEFAULT_HEIGHT, rows * SUBPLOT_HEIGHT_PER_ROW)
    
    # Update layout
    fig.update_layout(
        title=title,
        width=width,
        height=height,
        showlegend=False,
        margin=MARGIN
    )
    
    # Update axes labels
    for i in range(1, rows + 1):
        fig.update_xaxes(title_text=time_col, row=i, col=1)
        if facet_by:
            fig.update_yaxes(title_text="Frequency (%)", row=i, col=1)
        else:
            fig.update_yaxes(title_text="Frequency (%)", row=i, col=1)
    
    # Add subplot legends
    for i in range(1, rows + 1):
        subplot_groups = []
        subplot_traces = []
        for trace in fig.data:
            if hasattr(trace, 'legendgroup') and trace.legendgroup == f"subplot_{i}":
                if trace.name not in subplot_groups:
                    subplot_groups.append(trace.name)
                    subplot_traces.append(trace)
        
        if subplot_groups:
            legend_y = 1.0 - (i - 0.5) / rows
            fig = configure_legend(
                fig=fig,
                subplot_groups=subplot_groups,
                subplot_traces=subplot_traces,
                is_subplot=True,
                legend_x=1.05,
                legend_y=legend_y,
                width=width,
                height=height
            )
    
    return fig


def create_cell_type_faceted_plot(
    df: DataFrame, 
    time_col: str, 
    value_cols: List[str],
    width: int = DEFAULT_WIDTH,
    height: Optional[int] = None,
    max_cell_types: int = MAX_CELL_TYPES
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
        max_cell_types=max_cell_types
    )


def create_group_faceted_plot(
    df: DataFrame, 
    time_col: str, 
    value_cols: List[str], 
    facet_by: str,
    width: int = DEFAULT_WIDTH,
    height: Optional[int] = None,
    max_cell_types: int = MAX_CELL_TYPES
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
        max_cell_types=max_cell_types
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