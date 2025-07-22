# flowproc/gui/processor.py
"""
Validation utilities for GUI input processing.
Actual processing is now handled by async_processor module.
"""
from pathlib import Path
from typing import List
import logging
import os
from PySide6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def validate_inputs(
    input_paths: List[Path],
    output_dir: Path,
    auto_parse: bool,
    groups: List[int],
    replicates: List[int]
) -> bool:
    """
    Validate input paths and configurations.

    Args:
        input_paths: List of input file or directory paths.
        output_dir: Output directory path.
        auto_parse: Flag for auto-parsing groups.
        groups: List of user-defined groups.
        replicates: List of user-defined replicates.

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        if not input_paths:
            raise ValueError("No input files or folders selected.")
            
        invalid_paths = [p for p in input_paths if not p.exists()]
        if invalid_paths:
            raise ValueError(f"Invalid paths: {invalid_paths}")
            
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            
        if not output_dir.is_dir() or not os.access(output_dir, os.W_OK):
            raise ValueError("Output directory is not writable.")
            
        if not auto_parse and (not groups or not replicates):
            raise ValueError("Groups and replicates must be defined when manual mode is enabled.")
            
        logger.debug("Inputs validated successfully.")
        return True
        
    except ValueError as e:
        logger.error(f"Validation failed: {str(e)}")
        QMessageBox.critical(None, "Input Error", str(e))
        return False
    except Exception as e:
        logger.error(f"Unexpected validation error: {str(e)}")
        QMessageBox.critical(None, "Validation Error", f"Unexpected error: {str(e)}")
        return False