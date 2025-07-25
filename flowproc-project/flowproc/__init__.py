# flowproc/__init__.py
"""
FlowProc - Flow Cytometry Data Processing Package

High-performance flow cytometry data processing with async GUI support.
Features vectorized data aggregation for 5-10x performance improvements.
"""

__version__ = "2.0.0"  # Major version bump for async and vectorized features

# Import from new domain structure
from .domain.parsing import load_and_parse_df, extract_tissue, extract_group_animal
from .domain.export import process_csv, process_directory
from .domain.processing import map_replicates
from .domain.processing.vectorized_aggregator import VectorizedAggregator, AggregationConfig
from .domain.visualization.visualize import DataProcessor, Visualizer, visualize_data
from .core.constants import KEYWORDS

# Reshape pair is not implemented yet
reshape_pair = None

from .resource_utils import get_resource_path, get_data_path, get_package_root

# GUI components (optional - requires PySide6)
try:
    from .presentation.gui import main as gui_main
    from .presentation.gui import ProcessingManager, ProcessingState
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    gui_main = None
    ProcessingManager = None
    ProcessingState = None

# Expose all public APIs
__all__ = [
    '__version__',
    'load_and_parse_df',
    'extract_tissue', 
    'extract_group_animal',
    'process_csv',
    'process_directory',
    'map_replicates',
    'reshape_pair',
    'VectorizedAggregator',
    'AggregationConfig',
    'DataProcessor',
    'Visualizer',
    'visualize_data',
    'KEYWORDS',
    'get_resource_path',
    'get_data_path',
    'get_package_root',
    'gui_main',
    'ProcessingManager',
    'ProcessingState',
    'GUI_AVAILABLE'
]

# Support both async (GUI) and sync (CLI/script) workflows
def main():
    """Main entry point that launches the GUI."""
    if GUI_AVAILABLE and gui_main:
        gui_main()
    else:
        raise ImportError(
            "GUI components not available. Install PySide6: pip install PySide6"
        )

if __name__ == "__main__":
    main()