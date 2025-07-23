# flowproc/__main__.py
"""
Entry point for the flowproc application, launching the GUI.
Ensures logging is configured and handles exceptions gracefully.
Note: Requires 'logging' module for debug/info/error messages.
"""

import sys
import os
import logging  # Added to resolve NameError

from .logging_config import setup_logging
from .gui import create_gui
from .resource_utils import get_package_root

if __name__ == "__main__":
    # Configure logging once at the start, appending to log file
    setup_logging(filemode='a')
    logging.debug("Entering flowproc.__main__")
    logging.debug(f"sys.path before adjustment: {sys.path}")  # Debug path

    # Ensure package is recognized by verifying directory structure
    # Use PyInstaller-compatible path resolution
    package_root = get_package_root()
    logging.debug(f"Package root: {package_root}")
    
    # Only adjust sys.path in development mode (not needed in PyInstaller)
    if not hasattr(sys, '_MEIPASS'):
        flowproc_dir = package_root
        if not (flowproc_dir / '__init__.py').exists():
            raise ImportError("flowproc package requires an __init__.py file in the flowproc directory")
        parent_dir = package_root.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        logging.debug(f"sys.path after adjustment: {sys.path}")  # Debug path

    try:
        logging.debug("Running PySide6 app from __main__")
        logging.info("Testing pre-loop log write")
        create_gui()  # Launches the GUI application
        logging.debug("PySide6 app execution completed")
    except Exception as e:
        logging.error(f"Failed in flowproc.__main__: {str(e)}", exc_info=True)
        raise