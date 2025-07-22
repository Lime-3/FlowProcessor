# flowproc/__init__.py
"""
FlowProc - Flow Cytometry Data Processing Package

High-performance flow cytometry data processing with async GUI support.
Features vectorized data aggregation for 5-10x performance improvements.
"""

__version__ = "2.0.0"  # Major version bump for async and vectorized features

# Core modules
from .parsing import load_and_parse_df, extract_tissue, extract_group_animal
from .transform import map_replicates, reshape_pair
from .writer import process_csv, process_directory, KEYWORDS
from .vectorized_aggregator import VectorizedAggregator, AggregationConfig

# GUI components (optional - requires PySide6)
try:
    from .gui import main as gui_main
    from .gui import ProcessingManager, ProcessingState
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    gui_main = None
    ProcessingManager = None
    ProcessingState = None

__all__ = [
    # Version
    '__version__',
    
    # Core functions
    'load_and_parse_df',
    'extract_tissue',
    'extract_group_animal',
    'map_replicates',
    'reshape_pair',
    'process_csv',
    'process_directory',
    'KEYWORDS',
    
    # New vectorized features
    'VectorizedAggregator',
    'AggregationConfig',
    
    # GUI (if available)
    'GUI_AVAILABLE',
    'gui_main',
    'ProcessingManager',
    'ProcessingState',
]