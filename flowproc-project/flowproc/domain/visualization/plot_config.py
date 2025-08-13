"""
Shared configuration constants for flow cytometry visualization plots.
"""

from typing import Dict, Final

# Default dimensions and spacing
DEFAULT_WIDTH: Final[int] = 900  # Standardized default width
DEFAULT_HEIGHT: Final[int] = 400  # Standardized default height
MARGIN: Final[Dict[str, int]] = {'l': 50, 'r': 300, 't': 50, 'b': 50}  # Increased right margin for legend
VERTICAL_SPACING: Final[float] = 0.08  # Reduced from 0.12 to allow more subplots without bunching
HORIZONTAL_SPACING: Final[float] = 0.05

# Legend configuration (default: right-side vertical legend)
LEGEND_X_POSITION: Final[float] = 1.05  # Position legend to the right of the plot
LEGEND_Y_POSITION: Final[float] = 0.5   # Vertically centered
LEGEND_BG_COLOR: Final[str] = 'rgba(255,255,255,0.9)'
LEGEND_FONT_SIZE: Final[int] = 11
LEGEND_ITEM_WIDTH: Final[int] = 30
LEGEND_TRACE_GROUP_GAP: Final[int] = 6

# Plot limits and sizing
MAX_CELL_TYPES: Final[int] = 8
SUBPLOT_HEIGHT_PER_ROW: Final[int] = 250  # Increased from 200 for better legend visibility
MAX_SUBPLOTS_PER_ROW: Final[int] = 2  # Allow up to 2 subplots per row to reduce bunching

# Aspect ratio configuration
TARGET_ASPECT_RATIO: Final[float] = 1.7  # Reduced from 2.0 to accommodate legend better
ASPECT_TOLERANCE: Final[float] = 0.2  # Allow 20% variation from target ratio

# Trace styling defaults
DEFAULT_TRACE_CONFIG: Final[Dict[str, Dict[str, int]]] = {
    'line': {'width': 2},
    'marker': {'size': 6}
}

# Title formatting constants
TIME_THRESHOLDS: Final[Dict[str, float]] = {
    'DAYS': 24,  # hours
    'HOURS': 1,  # hours
    'MINUTES': 1/60  # hours
}

__all__ = [
    'DEFAULT_WIDTH',
    'DEFAULT_HEIGHT',
    'MARGIN',
    'VERTICAL_SPACING',
    'HORIZONTAL_SPACING',
    'LEGEND_X_POSITION',
    'LEGEND_Y_POSITION',
    'LEGEND_BG_COLOR',
    'LEGEND_FONT_SIZE',
    'LEGEND_ITEM_WIDTH',
    'LEGEND_TRACE_GROUP_GAP',
    'MAX_CELL_TYPES',
    'SUBPLOT_HEIGHT_PER_ROW',
    'MAX_SUBPLOTS_PER_ROW',
    'TARGET_ASPECT_RATIO',
    'ASPECT_TOLERANCE',
    'DEFAULT_TRACE_CONFIG',
    'TIME_THRESHOLDS',
]