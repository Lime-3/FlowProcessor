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
    legend_width: Optional[int] = None,
    legend_title: Optional[str] = None,
    show_mean_sem_label: bool = True
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
        legend_title: Title to display above the legend
        show_mean_sem_label: Whether to show "Mean ± SEM" label at bottom of legend
        
    Returns:
        Updated figure with configured legend
        
    Raises:
        ValueError: If required parameters are missing for the legend type
    """
    if is_subplot:
        return _configure_subplot_legend(
            fig, subplot_groups, subplot_traces, legend_x, legend_y, 
            width, height, font_size, bg_color, legend_title, show_mean_sem_label
        )
    else:
        return _configure_global_legend(
            fig, df, color_col, width, height, font_size, bg_color, 
            legend_width, legend_title, show_mean_sem_label
        )


def _configure_global_legend(
    fig: Figure,
    df: DataFrame,
    color_col: Optional[str],
    width: Optional[int] = DEFAULT_WIDTH,
    height: Optional[int] = None,
    font_size: int = LEGEND_FONT_SIZE,
    bg_color: str = LEGEND_BG_COLOR,
    legend_width: Optional[int] = None,
    legend_title: Optional[str] = None,
    show_mean_sem_label: bool = True
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
        legend_title: Title to display above the legend
        show_mean_sem_label: Whether to show "Mean ± SEM" label at bottom of legend
        
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
    
    # Calculate total width - ensure legend fits within the plot area
    plot_width = width if width is not None else DEFAULT_WIDTH
    legend_width = legend_width if legend_width is not None else 150
    
    # Position legend at x=1.02 (closer to plot) and ensure it fits
    # The legend should be positioned so it's visible without scrolling
    legend_x = 1.02
    legend_width_paper = legend_width / plot_width  # Convert to paper coordinates
    
    # Ensure legend doesn't extend beyond reasonable bounds
    if legend_x + legend_width_paper > 1.15:  # Don't go too far right
        legend_x = 1.15 - legend_width_paper
    
    # Preserve existing legend title if set
    existing_legend_title = None
    if hasattr(fig.layout, 'legend') and fig.layout.legend and hasattr(fig.layout.legend, 'title'):
        existing_legend_title = fig.layout.legend.title
    
    # Apply layout with legend
    layout_updates = {
        'width': plot_width,
        'showlegend': show_legend,
        'margin': MARGIN
    }
    
    # Only configure legend if we're showing it
    if show_legend:
        legend_config = dict(
            x=legend_x,
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
        
        # Add legend title if provided
        if legend_title:
            legend_config['title'] = dict(
                text=legend_title,
                font=dict(size=font_size + 1, color="black")
            )
        
        # Add mean +/- SEM label at bottom if requested
        if show_mean_sem_label:
            # Create a custom legend with mean +/- SEM label
            # We'll add this as an annotation below the legend
            # Calculate position below the legend based on legend height
            legend_height = legend_items * 20 + 40  # Approximate legend height in pixels
            legend_height_paper = legend_height / plot_width  # Convert to paper coordinates
            
            fig.add_annotation(
                text="Mean ± SEM",
                xref="paper",
                yref="paper",
                x=legend_x,  # Slightly to the right of legend
                y=0.5 - legend_height_paper - 0.05,  # Dynamic positioning below legend
                xanchor="left",
                yanchor="top",
                showarrow=False,
                font=dict(size=font_size - 1, color="gray"),
                align="left"
            )
        
        layout_updates['legend'] = legend_config
    
    # Restore legend title if it existed and we're showing legend
    # Only restore if we didn't set a new legend title
    if existing_legend_title and show_legend and 'legend' in layout_updates and not legend_title:
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
    bg_color: str,
    legend_title: Optional[str] = None,
    show_mean_sem_label: bool = True
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
        legend_title: Title to display above the legend
        show_mean_sem_label: Whether to show "Mean ± SEM" label at bottom of legend
        
    Returns:
        Updated figure with subplot legend annotation
    """
    if not subplot_groups or not subplot_traces:
        logger.warning("No subplot groups or traces provided for legend")
        return fig
    
    # Create legend annotation
    annotation = _create_subplot_legend_annotation(
        subplot_groups, subplot_traces, legend_x, legend_y, font_size, bg_color, legend_title, show_mean_sem_label
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
    bg_color: str = LEGEND_BG_COLOR,
    legend_title: Optional[str] = None,
    show_mean_sem_label: bool = True
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
        legend_title: Title to display above the legend
        show_mean_sem_label: Whether to show "Mean ± SEM" label at bottom of legend
        
    Returns:
        Dictionary containing annotation configuration
    """
    if not subplot_groups:
        return {}
    
    # Create legend text with colored symbols
    legend_items = []
    
    # Add legend title if provided
    if legend_title:
        legend_items.append(f"<b>{legend_title}</b>")
        legend_items.append("")  # Empty line for spacing
    
    for j, (group, trace) in enumerate(zip(subplot_groups, subplot_traces)):
        color = (
            trace.line.color 
            if hasattr(trace.line, 'color') and trace.line.color 
            else f"hsl({j * 360 // len(subplot_groups)}, 70%, 50%)"
        )
        legend_items.append(f'<span style="color: {color};">●</span> {group}')
    
    # Add mean +/- SEM label at bottom if requested
    if show_mean_sem_label:
        legend_items.append("")  # Empty line for spacing
        legend_items.append('<span style="color: gray; font-size: 0.9em;">Mean ± SEM</span>')
    
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