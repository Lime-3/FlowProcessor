"""
Shared configuration constants for flow cytometry visualization plots.
"""

# Default dimensions and spacing
DEFAULT_WIDTH = 900  # Increased from 1000 to accommodate legend
DEFAULT_HEIGHT = 480  # Reduced from 700 for better standard mode aspect ratio (groups on x-axis, populations in legend)
MARGIN = {'l': 50, 'r': 300, 't': 50, 'b': 50}  # Increased right margin for legend
VERTICAL_SPACING = 0.08  # Reduced from 0.12 to allow more subplots without bunching
HORIZONTAL_SPACING = 0.05

# Legend configuration
LEGEND_X_POSITION = 0.5  # Center horizontally for bottom legend
LEGEND_Y_POSITION = -0.15  # Below the plots for bottom legend
LEGEND_BG_COLOR = 'rgba(255,255,255,0.9)'
LEGEND_FONT_SIZE = 11
LEGEND_ITEM_WIDTH = 30
LEGEND_TRACE_GROUP_GAP = 6

# Plot limits and sizing
MAX_CELL_TYPES = 8
SUBPLOT_HEIGHT_PER_ROW = 250  # Increased from 200 for better legend visibility
MAX_SUBPLOTS_PER_ROW = 2  # Allow up to 2 subplots per row to reduce bunching

# Aspect ratio configuration
TARGET_ASPECT_RATIO = 1.7  # Reduced from 2.0 to accommodate legend better
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