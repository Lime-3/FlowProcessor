"""
Legend configuration and styling functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, List, Dict, Any

from .plot_config import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, MARGIN, LEGEND_X_POSITION, 
    LEGEND_BG_COLOR, LEGEND_FONT_SIZE, LEGEND_ITEM_WIDTH, LEGEND_TRACE_GROUP_GAP
)

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame
Figure = go.Figure


def configure_legend(
    fig: Figure, 
    df: Optional[DataFrame] = None,
    color_col: Optional[str] = None,
    subplot_groups: Optional[List[str]] = None,
    subplot_traces: Optional[List[go.Scatter]] = None,
    is_subplot: bool = False,
    legend_x: float = LEGEND_X_POSITION,
    legend_y: float = 0.5,
    width: int = DEFAULT_WIDTH,
    height: Optional[int] = None,
    font_size: int = LEGEND_FONT_SIZE,
    bg_color: str = LEGEND_BG_COLOR,
    legend_width: Optional[int] = None
) -> Figure:
    """
    Configure legend for both global and subplot legends.
    
    This function consolidates legend configuration logic and supports both
    global legends (via color_col) and subplot legends (via subplot_groups, subplot_traces).
    
    Args:
        fig: Plotly figure to configure
        df: DataFrame containing the data (required for global legends)
        color_col: Column name used for color coding (for global legends)
        subplot_groups: List of group names (for subplot legends)
        subplot_traces: List of corresponding traces (for subplot legends)
        is_subplot: Whether this is a subplot legend (True) or global legend (False)
        legend_x: X position for legend (paper coordinates)
        legend_y: Y position for legend (paper coordinates)
        width: Figure width
        height: Figure height (optional, uses default if not provided)
        font_size: Legend font size
        bg_color: Legend background color
        legend_width: Explicit legend width (calculated automatically if not provided)
        
    Returns:
        Updated figure with configured legend
        
    Raises:
        ValueError: If required parameters are missing for the legend type
    """
    if is_subplot:
        return _configure_subplot_legend(
            fig, subplot_groups, subplot_traces, legend_x, legend_y, 
            width, height, font_size, bg_color
        )
    else:
        return _configure_global_legend(
            fig, df, color_col, width, height, font_size, bg_color, legend_width
        )


def _configure_global_legend(
    fig: Figure,
    df: DataFrame,
    color_col: Optional[str],
    width: Optional[int] = DEFAULT_WIDTH,
    height: Optional[int] = None,
    font_size: int = LEGEND_FONT_SIZE,
    bg_color: str = LEGEND_BG_COLOR,
    legend_width: Optional[int] = None
) -> Figure:
    """
    Configure global legend for the entire figure.
    
    Args:
        fig: Plotly figure to configure
        df: DataFrame containing the data
        color_col: Column name used for color coding
        width: Figure width
        height: Figure height
        font_size: Legend font size
        bg_color: Legend background color
        legend_width: Explicit legend width
        
    Returns:
        Updated figure with global legend configuration
    """
    # Determine legend items and whether to show legend
    legend_items = 0
    show_legend = False
    
    if color_col and color_col in df.columns:
        legend_items = len(df[color_col].unique())
        show_legend = legend_items > 1  # Only show legend if there are multiple items
    else:
        # Check if the figure has traces with names (for single metric plots)
        named_traces = [trace for trace in fig.data if trace.name and trace.name.strip()]
        legend_items = len(named_traces)
        show_legend = legend_items > 1  # Only show legend if there are multiple named traces
        
        # For single metric plots, check if there's a legend title set (like "Mean ± SEM")
        if legend_items <= 1 and hasattr(fig.layout, 'legend') and fig.layout.legend and hasattr(fig.layout.legend, 'title'):
            show_legend = True  # Show legend if there's a meaningful title
    
    # Calculate legend width
    if legend_width is None:
        legend_width = max(legend_items * LEGEND_ITEM_WIDTH + 50, 100)
    
    # Calculate total width with defaults - ensure enough space for legend at x=1.05
    plot_width = width if width is not None else DEFAULT_WIDTH
    legend_width = legend_width if legend_width is not None else 150
    total_width = plot_width + legend_width + 50  # Extra space for legend positioned at x=1.05
    
    # Preserve existing legend title if set
    existing_legend_title = None
    if hasattr(fig.layout, 'legend') and fig.layout.legend and hasattr(fig.layout.legend, 'title'):
        existing_legend_title = fig.layout.legend.title
    
    # Apply layout with legend
    layout_updates = {
        'width': total_width,
        'showlegend': show_legend,
        'margin': MARGIN
    }
    
    # Only configure legend if we're showing it
    if show_legend:
        layout_updates['legend'] = dict(
            x=1.05,
            y=0.5,
            yanchor="middle",
            xanchor="left",
            font_size=font_size,
            bordercolor='black',
            borderwidth=0.5,
            bgcolor=bg_color,
            orientation="v",
            itemwidth=LEGEND_ITEM_WIDTH,
            itemsizing="constant",
            tracegroupgap=LEGEND_TRACE_GROUP_GAP,
            entrywidth=LEGEND_ITEM_WIDTH,
            entrywidthmode="pixels",
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        )
    
    # Restore legend title if it existed and we're showing legend
    if existing_legend_title and show_legend and 'legend' in layout_updates:
        layout_updates['legend']['title'] = existing_legend_title
    
    if height is not None:
        layout_updates['height'] = height
    
    fig.update_layout(**layout_updates)
    
    return fig


def _configure_subplot_legend(
    fig: Figure,
    subplot_groups: List[str],
    subplot_traces: List[go.Scatter],
    legend_x: float,
    legend_y: float,
    width: int,
    height: Optional[int],
    font_size: int,
    bg_color: str
) -> Figure:
    """
    Configure subplot legend using annotations.
    
    Args:
        fig: Plotly figure to configure
        subplot_groups: List of group names
        subplot_traces: List of corresponding traces
        legend_x: X position for legend
        legend_y: Y position for legend
        width: Figure width
        height: Figure height
        font_size: Legend font size
        bg_color: Legend background color
        
    Returns:
        Updated figure with subplot legend annotation
    """
    if not subplot_groups or not subplot_traces:
        logger.warning("No subplot groups or traces provided for legend")
        return fig
    
    # Create legend annotation
    annotation = _create_subplot_legend_annotation(
        subplot_groups, subplot_traces, legend_x, legend_y, font_size, bg_color
    )
    
    if annotation:
        # Preserve existing annotations and add new legend annotation
        existing_annotations = fig.layout.annotations if hasattr(fig.layout, 'annotations') else []
        # Filter out any existing legend annotations (those with x=1.05)
        subplot_title_annotations = [
            ann for ann in existing_annotations 
            if not (hasattr(ann, 'x') and ann.x == LEGEND_X_POSITION)
        ]
        all_annotations = subplot_title_annotations + [annotation]
        
        layout_updates = {
            'annotations': all_annotations,
            'width': width,
            'margin': MARGIN
        }
        
        if height is not None:
            layout_updates['height'] = height
        
        fig.update_layout(**layout_updates)
    
    return fig


def _create_subplot_legend_annotation(
    subplot_groups: List[str], 
    subplot_traces: List[go.Scatter],
    legend_x: float = LEGEND_X_POSITION, 
    legend_y: float = 0.5,
    font_size: int = LEGEND_FONT_SIZE,
    bg_color: str = LEGEND_BG_COLOR
) -> Dict[str, Any]:
    """
    Create a legend annotation for subplots with colored symbols.
    
    Args:
        subplot_groups: List of group names
        subplot_traces: List of corresponding traces
        legend_x: X position for legend (paper coordinates)
        legend_y: Y position for legend (paper coordinates)
        font_size: Font size for legend text
        bg_color: Background color for legend
        
    Returns:
        Dictionary containing annotation configuration
    """
    if not subplot_groups:
        return {}
    
    # Create legend text with colored symbols
    legend_items = []
    for j, (group, trace) in enumerate(zip(subplot_groups, subplot_traces)):
        color = (
            trace.line.color 
            if hasattr(trace.line, 'color') and trace.line.color 
            else f"hsl({j * 360 // len(subplot_groups)}, 70%, 50%)"
        )
        legend_items.append(f'<span style="color: {color};">●</span> {group}')
    legend_text = "<br>".join(legend_items)
    
    return dict(
        text=legend_text,
        xref="paper",
        yref="paper",
        x=legend_x,
        y=legend_y,
        xanchor="left",
        yanchor="middle",
        showarrow=False,
        bgcolor=bg_color,
        bordercolor='rgba(0,0,0,0.3)',
        borderwidth=1,
        font=dict(size=font_size, color="black"),
        align="left"
    )


def apply_default_layout(
    fig: Figure, 
    width: int = DEFAULT_WIDTH, 
    height: int = DEFAULT_HEIGHT,
    margin: Optional[Dict[str, int]] = None
) -> Figure:
    """
    Apply default layout settings to a figure.
    
    Args:
        fig: Plotly figure to configure
        width: Figure width
        height: Figure height
        margin: Custom margin settings (uses default if not provided)
        
    Returns:
        Updated figure with default layout
    """
    layout_updates = {
        'width': width,
        'height': height,
        'margin': margin or MARGIN
    }
    
    fig.update_layout(**layout_updates)
    return fig 