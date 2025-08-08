"""
Utility functions for flow cytometry visualization plots.
"""

import logging
from typing import List, Union, Optional, Dict, Any
import pandas as pd
import numpy as np

from .plot_config import TIME_THRESHOLDS, DEFAULT_WIDTH, DEFAULT_HEIGHT, MARGIN, LEGEND_X_POSITION

logger = logging.getLogger(__name__)

# Type aliases
DataFrame = pd.DataFrame


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


def calculate_subplot_dimensions(num_items: int, max_items_per_row: int = 1) -> tuple:
    """
    Calculate subplot dimensions for a given number of items.
    
    Args:
        num_items: Number of items to display
        max_items_per_row: Maximum items per row (default 1 for single column)
        
    Returns:
        Tuple of (rows, cols)
    """
    if max_items_per_row == 1:
        return num_items, 1
    else:
        rows = (num_items + max_items_per_row - 1) // max_items_per_row
        cols = min(num_items, max_items_per_row)
        return rows, cols


def calculate_layout_for_long_labels(
    labels: List[str], 
    legend_items: int, 
    title: str, 
    legend_labels: List[str], 
    default_width: int, 
    default_height: int
) -> Dict[str, Any]:
    """
    Calculate layout adjustments for plots with long labels.
    
    Args:
        labels: List of x-axis labels
        legend_items: Number of legend items
        title: Plot title
        legend_labels: List of legend labels
        default_width: Default plot width
        default_height: Default plot height
        
    Returns:
        Dictionary with layout adjustments
    """
    # Calculate maximum label length
    max_label_length = max(len(str(label)) for label in labels) if labels else 0
    max_legend_length = max(len(str(label)) for label in legend_labels) if legend_labels else 0
    
    # Adjust width based on label length
    width_adjustment = max(0, (max_label_length - 10) * 8)  # 8px per character over 10
    adjusted_width = default_width + width_adjustment
    
    # Adjust height for legend if needed
    height_adjustment = 0
    if legend_items > 0:
        height_adjustment = max(0, (legend_items - 3) * 20)  # 20px per legend item over 3
    
    adjusted_height = default_height + height_adjustment
    
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
    
    # Legend configuration
    legend_config = {
        'x': LEGEND_X_POSITION,
        'y': 0.5,
        'yanchor': 'middle',
        'xanchor': 'left',
        'orientation': 'v',
        'itemwidth': 30,
        'itemsizing': 'constant',
        'tracegroupgap': 6,
        'entrywidth': 30,
        'entrywidthmode': 'pixels',
        'itemclick': 'toggle',
        'itemdoubleclick': 'toggleothers',
        'bgcolor': 'rgba(255,255,255,0.9)',
        'bordercolor': 'black',
        'borderwidth': 0.5,
        'font': {'size': 11}
    }
    
    return {
        'width': adjusted_width,
        'height': adjusted_height,
        'margin': margin,
        'legend': legend_config,
        'xaxis_title_standoff': xaxis_title_standoff,
        'xaxis_tickangle': xaxis_tickangle
    }


def calculate_optimal_legend_position(
    legend_items: int,
    legend_labels: List[str],
    plot_width: int,
    plot_height: int
) -> Dict[str, Any]:
    """
    Calculate optimal legend positioning and layout adjustments.
    
    Args:
        legend_items: Number of legend items
        legend_labels: List of legend labels
        plot_width: Plot width
        plot_height: Plot height
        
    Returns:
        Dictionary with legend configuration and layout adjustments
    """
    # Calculate legend width based on longest label
    max_legend_length = max(len(str(label)) for label in legend_labels) if legend_labels else 0
    legend_width = max(max_legend_length * 8 + 50, 100)  # 8px per character + padding
    
    # Calculate total width including legend
    total_width = plot_width + legend_width + 50  # 50px spacing
    
    # Adjust margins to accommodate legend
    margin = MARGIN.copy()
    margin['r'] = legend_width + 50  # Right margin for legend
    
    # Legend configuration
    legend_config = {
        'x': LEGEND_X_POSITION,
        'y': 0.5,
        'yanchor': 'middle',
        'xanchor': 'left',
        'orientation': 'v',
        'itemwidth': 30,
        'itemsizing': 'constant',
        'tracegroupgap': 6,
        'entrywidth': 30,
        'entrywidthmode': 'pixels',
        'itemclick': 'toggle',
        'itemdoubleclick': 'toggleothers',
        'bgcolor': 'rgba(255,255,255,0.9)',
        'bordercolor': 'black',
        'borderwidth': 0.5,
        'font': {'size': 11}
    }
    
    return {
        'width': total_width,
        'margin': margin,
        'legend': legend_config
    } 