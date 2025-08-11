"""
Shared configuration constants for flow cytometry visualization plots.
"""

# Default dimensions and spacing
DEFAULT_WIDTH = 1000
DEFAULT_HEIGHT = 600
MARGIN = {'l': 50, 'r': 200, 't': 50, 'b': 50}
VERTICAL_SPACING = 0.12
HORIZONTAL_SPACING = 0.05

# Legend configuration
LEGEND_X_POSITION = 1.05
LEGEND_BG_COLOR = 'rgba(255,255,255,0.9)'
LEGEND_FONT_SIZE = 11
LEGEND_ITEM_WIDTH = 30
LEGEND_TRACE_GROUP_GAP = 6

# Plot limits and sizing
MAX_CELL_TYPES = 8
SUBPLOT_HEIGHT_PER_ROW = 200

# Aspect ratio configuration
TARGET_ASPECT_RATIO = 2.0  # Width:Height ratio (2:1 = wide and short)
ASPECT_TOLERANCE = 0.2  # Allow 20% variation from target ratio

# Trace styling defaults
DEFAULT_TRACE_CONFIG = {
    'line': {'width': 2},
    'marker': {'size': 6}
}

# Title formatting constants
TIME_THRESHOLDS = {
    'DAYS': 24,  # hours
    'HOURS': 1,  # hours
    'MINUTES': 1/60  # hours
} 