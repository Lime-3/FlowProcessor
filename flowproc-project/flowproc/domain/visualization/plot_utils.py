"""
Utility functions for flow cytometry visualization plots.
"""

import logging
from typing import List, Union, Optional, Dict, Any
import pandas as pd
import numpy as np

from .plot_config import TIME_THRESHOLDS, DEFAULT_WIDTH, DEFAULT_HEIGHT, MARGIN

logger = logging.getLogger(__name__)

# Type aliases
DataFrame = pd.DataFrame
def get_group_label_map(
    df: DataFrame,
    user_group_labels: Optional[List[str]] = None
) -> Dict[Union[int, float, str], str]:
    """
    Build a mapping from group numeric codes to display labels.

    Industry-standard approach: keep numeric codes for data/positions and
    supply human-friendly labels for display (ticks/legend). This avoids
    mutating data and preserves sorting.

    Args:
        df: DataFrame that may contain a 'Group' column
        user_group_labels: Optional list of custom labels provided by the user

    Returns:
        Dict mapping group code -> display label
    """
    groups: List[Any] = []
    if df is not None and 'Group' in df.columns:
        try:
            # Preserve numeric identity where possible for stable ordering
            groups = sorted(pd.unique(df['Group']))
        except Exception:
            groups = list(pd.unique(df['Group']))

    # Fallback: if no groups detected, return empty map
    if not groups:
        return {}

    # Only apply mapping when custom labels are explicitly provided and cover all groups
    if user_group_labels and len(user_group_labels) >= len(groups):
        return {groups[i]: user_group_labels[i] for i in range(len(groups))}

    # No mapping if custom labels not provided; preserve original numeric labels
    return {}



def format_time_title(time_values: Union[List[Union[int, float, str]], np.ndarray]) -> str:
    """
    Format time values into a readable title string.
    
    Args:
        time_values: List or numpy array of time values to format
        
    Returns:
        Formatted time string for title
    """
    # Convert numpy array to list if needed
    if isinstance(time_values, np.ndarray):
        time_values = time_values.tolist()
    
    if not time_values:
        return ""
    
    time_strs = []
    for time_val in sorted(time_values):
        if isinstance(time_val, (int, float)):
            if time_val >= TIME_THRESHOLDS['DAYS']:  # Convert to days if >= 24 hours
                days = time_val / 24
                if days.is_integer():
                    time_strs.append(f"Day {int(days)}")
                else:
                    time_strs.append(f"Day {days:.1f}")
            elif time_val >= TIME_THRESHOLDS['HOURS']:  # Show as hours
                if time_val.is_integer():
                    time_strs.append(f"{int(time_val)}h")
                else:
                    time_strs.append(f"{time_val:.1f}h")
            else:  # Convert to minutes
                minutes = time_val * 60
                if minutes.is_integer():
                    time_strs.append(f"{int(minutes)}min")
                else:
                    time_strs.append(f"{minutes:.1f}min")
        else:
            time_strs.append(str(time_val))
    
    if len(time_strs) == 1:
        return f" ({time_strs[0]})"
    elif len(time_strs) <= 3:
        return f" ({', '.join(time_strs)})"
    else:
        return f" ({time_strs[0]}-{time_strs[-1]})"


def validate_plot_data(df: DataFrame, time_col: str, value_cols: List[str], facet_by: Optional[str] = None) -> None:
    """
    Validate data for plotting operations.
    
    Args:
        df: DataFrame to validate
        time_col: Time column name
        value_cols: List of value columns
        facet_by: Optional facet column name
        
    Raises:
        ValueError: If validation fails
    """
    if df.empty:
        raise ValueError("DataFrame is empty")
    
    if time_col not in df.columns:
        raise ValueError(f"Time column '{time_col}' not found in data")
    
    missing_cols = [col for col in value_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Value columns not found in data: {missing_cols}")
    
    if facet_by and facet_by not in df.columns:
        raise ValueError(f"Facet column '{facet_by}' not found in data")


def limit_cell_types(value_cols: List[str], max_types: int = 8) -> List[str]:
    """
    Limit the number of cell types for plotting clarity.
    
    Args:
        value_cols: List of value columns (cell types)
        max_types: Maximum number of cell types to include
        
    Returns:
        Limited list of cell types
    """
    if len(value_cols) > max_types:
        limited_cols = sorted(value_cols)[:max_types]
        logger.info(f"Limited to {max_types} cell types for faceted plot")
        return limited_cols
    return value_cols


def calculate_subplot_dimensions(num_items: int, max_items_per_row: Optional[int] = None) -> tuple:
    """
    Calculate subplot dimensions for a given number of items.
    
    Args:
        num_items: Number of items to display
        max_items_per_row: Maximum items per row (if None, uses config default)
        
    Returns:
        Tuple of (rows, cols)
    """
    from .plot_config import MAX_SUBPLOTS_PER_ROW

    # Modern default: when not specified, use configured MAX_SUBPLOTS_PER_ROW
    effective_max = max_items_per_row if max_items_per_row is not None else MAX_SUBPLOTS_PER_ROW
    rows = (num_items + effective_max - 1) // effective_max
    cols = min(num_items, effective_max)
    return rows, cols


def calculate_layout_for_long_labels(
    labels: List[str], 
    legend_items: int, 
    title: str, 
    legend_labels: List[str], 
    default_width: Optional[int] = None, 
    default_height: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calculate layout adjustments for plots with long labels.

    Note: Legend styling is centralized in `legend_config.configure_legend`.
    This function only determines size, margins, and x-axis label behavior.

    Args:
        labels: List of x-axis labels
        legend_items: Number of legend items (used for height heuristics only)
        title: Plot title
        legend_labels: List of legend labels (used to estimate space needs only)
        default_width: Default plot width
        default_height: Default plot height
        
    Returns:
        Dictionary with layout adjustments (width, height, margin, xaxis_* keys)
    """
    # Resolve width/height inputs using defaults when not provided
    resolved_width = default_width if default_width is not None else DEFAULT_WIDTH
    resolved_height = default_height if default_height is not None else DEFAULT_HEIGHT

    # Calculate maximum label length
    max_label_length = max(len(str(label)) for label in labels) if labels else 0
    # Keep computation for potential future heuristics; not used for styling here
    _ = max(len(str(label)) for label in legend_labels) if legend_labels else 0

    # Adjust width based on label length
    width_adjustment = max(0, (max_label_length - 10) * 8)  # 8px per character over 10
    adjusted_width = resolved_width + width_adjustment
    
    # Adjust height for legend if needed
    height_adjustment = 0
    if legend_items > 0:
        height_adjustment = max(0, (legend_items - 3) * 20)  # 20px per legend item over 3
    
    adjusted_height = resolved_height + height_adjustment
    
    # Calculate margin adjustments
    margin = MARGIN.copy()
    if max_label_length > 15:
        margin['b'] = 80  # Increase bottom margin for long labels
        margin['r'] = 250  # Increase right margin for legend
    
    # Calculate x-axis adjustments
    xaxis_title_standoff = 30
    xaxis_tickangle = 0
    if max_label_length > 12:
        xaxis_tickangle = -45
    
    return {
        'width': adjusted_width,
        'height': adjusted_height,
        'margin': margin,
        'xaxis_title_standoff': xaxis_title_standoff,
        'xaxis_tickangle': xaxis_tickangle
    }


def calculate_aspect_ratio_dimensions(
    labels: List[str], 
    legend_items: int, 
    num_subplots: int = 1,
    base_width: int = DEFAULT_WIDTH
) -> Dict[str, int]:
    """
    Calculate dimensions maintaining aspect ratio with content adjustments.
    
    Args:
        labels: List of x-axis labels
        legend_items: Number of legend items
        num_subplots: Number of subplots
        base_width: Base width to calculate height from
        
    Returns:
        Dictionary with width and height maintaining aspect ratio
    """
    from .plot_config import TARGET_ASPECT_RATIO
    
    # Start with target aspect ratio
    target_ratio = TARGET_ASPECT_RATIO
    
    # Adjust for content needs while maintaining aspect ratio
    content_adjustments = 0.0
    
    # Adjust for label length (longer labels need more height, so reduce ratio)
    max_label_length = max(len(str(label)) for label in labels) if labels else 0
    if max_label_length > 15:
        content_adjustments += 0.3  # Reduce ratio to 1.4:1 for long labels
    elif max_label_length > 10:
        content_adjustments += 0.1  # Reduce ratio to 1.6:1 for medium labels
    
    # Adjust for legend items (more items need more height, so reduce ratio)
    if legend_items > 5:
        content_adjustments += 0.3  # Reduce ratio for many legend items
    elif legend_items > 3:
        content_adjustments += 0.2  # Slight reduction for moderate legend items
    
    # Adjust for subplot count (more subplots need more height, so reduce ratio)
    if num_subplots > 3:
        content_adjustments += 0.5  # Reduce ratio significantly for many subplots
    elif num_subplots > 1:
        content_adjustments += 0.3  # Reduce ratio for multiple subplots
    
    # Calculate final aspect ratio with content adjustments
    final_ratio = max(1.0, target_ratio - content_adjustments)  # Don't go below 1:1
    
    # Calculate dimensions
    width = base_width
    height = int(width / final_ratio)
    
    # Ensure minimum dimensions and maximum height to fit in viewport
    width = max(width, 800)
    height = max(height, 400)
    height = min(height, 900)  # Cap height to prevent excessive scrolling
    
    return {
        'width': width,
        'height': height,
        'aspect_ratio': final_ratio,
        'content_adjustments': content_adjustments
    }


def calculate_optimal_legend_position(
    legend_items: int,
    legend_labels: List[str],
    plot_width: int,
    plot_height: int
) -> Dict[str, Any]:
    """
    Calculate space requirements to accommodate a right-side legend.

    Legend styling and placement are managed by `legend_config.configure_legend`.
    This helper returns layout adjustments (width/margins) only.
    
    Args:
        legend_items: Number of legend items
        legend_labels: List of legend labels (used to estimate width)
        plot_width: Plot width
        plot_height: Plot height
        
    Returns:
        Dictionary with width and margin adjustments only
    """
    # Estimate legend width based on longest label
    max_legend_length = max(len(str(label)) for label in legend_labels) if legend_labels else 0
    legend_width = max(max_legend_length * 8 + 50, 100)  # 8px per character + padding

    # Calculate total width including legend
    total_width = plot_width + legend_width + 50  # 50px spacing

    # Adjust margins to accommodate legend
    margin = MARGIN.copy()
    margin['r'] = legend_width + 50  # Right margin for legend

    return {
        'width': total_width,
        'margin': margin
    }


def select_legend_title(
    color_col: Optional[str] = None,
    group_col: Optional[str] = None,
    context: Optional[str] = None
) -> str:
    """
    Determine a consistent legend title.

    Args:
        color_col: Column used for color grouping in non-timecourse plots
        group_col: Group column used in timecourse plots
        context: Optional context hint: 'single', 'comparison', 'overlay', 'faceted_cell', 'faceted_group'

    Returns:
        Legend title string
    """
    # Explicit contexts override generic logic
    if context == 'faceted_cell':
        return "Cell Types"
    if context == 'faceted_group':
        return "Groups"
    if context == 'overlay':
        return "Groups" if group_col else "Metrics"

    # Generic fallbacks
    if group_col or (color_col and color_col.lower() in {"group", "treatment", "condition"}):
        return "Groups"
    if context == 'comparison':
        return "Cell Types"
    return "Populations"


def apply_common_layout(
    fig,
    df: DataFrame,
    color_col: Optional[str],
    width: int,
    height: int,
    legend_title: str,
    show_mean_sem_label: bool = True
):
    """
    Apply standardized legend configuration and fixed sizing.

    This consolidates repeated patterns across plot creators.
    """
    # Lazy import to avoid circular import during module load
    from .legend_config import configure_legend

    fig = configure_legend(
        fig, df, color_col, is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=show_mean_sem_label
    )

    fig.update_layout(
        width=width,
        height=height,
        autosize=False
    )

    return fig


def apply_group_tick_labels(
    fig,
    df: DataFrame,
    user_group_labels: Optional[list],
    width: int,
    height: int
):
    """
    Map x-axis ticks for 'Group' and adjust layout for long labels, preserving plot area.
    Mirrors the previously duplicated logic in multiple creators.
    """
    if 'Group' not in df.columns:
        return fig

    unique_groups = df['Group'].unique()
    try:
        numeric_groups = sorted([float(g) if isinstance(g, str) else g for g in unique_groups])
        tickvals = [int(g) if hasattr(g, 'is_integer') and g.is_integer() else g for g in numeric_groups]
    except Exception:
        tickvals = sorted(unique_groups)

    group_label_map = get_group_label_map(df, user_group_labels)
    ticktext = [group_label_map.get(g, g) for g in tickvals]
    fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=ticktext)

    # Adjust layout for long labels while preserving width and legend placement
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
            proposed_margin['r'] = max(
                proposed_margin.get('r', 0),
                current_margin.get('r', 0),
                MARGIN.get('r', 0)
            )
            new_bottom = max(proposed_margin.get('b', 0), current_margin.get('b', 0))
            delta_bottom = max(0, new_bottom - current_margin.get('b', 0))
            fig.update_layout(
                width=width,
                height=height + delta_bottom,
                margin=dict(
                    l=current_margin.get('l', 50),
                    r=proposed_margin['r'],
                    t=current_margin.get('t', 50),
                    b=new_bottom
                )
            )
            fig.update_xaxes(tickangle=layout_adj.get('xaxis_tickangle', 0))
    except Exception:
        pass

    return fig