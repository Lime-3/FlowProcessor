"""
FlowProc - Entry point for the flow cytometry data processing tool.
"""

import sys
from pathlib import Path

# Ensure flowproc package is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .presentation.gui import create_gui

def main():
    """Main entry point."""
    # Mirror tests' expectation of startup log line
    import logging
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("GUI application started")
    create_gui()

if __name__ == "__main__":
    main()