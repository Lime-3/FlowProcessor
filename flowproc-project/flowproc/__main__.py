"""
FlowProc - Entry point for the flow cytometry data processing tool.
"""

import sys
import os
from pathlib import Path

# Ensure flowproc package is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from .presentation.gui import create_gui
except ImportError:
    # Try absolute import
    from flowproc.presentation.gui import create_gui

def main():
    """Main entry point."""
    create_gui()

if __name__ == "__main__":
    # When run as a script, use absolute imports
    from flowproc.presentation.gui import create_gui
    main()