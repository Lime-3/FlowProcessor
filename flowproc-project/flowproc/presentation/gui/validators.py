"""
Input validation for the GUI.
"""

from typing import List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def validate_inputs(
    input_paths: List[str],
    output_dir: str,
    groups: Optional[List[int]] = None,
    replicates: Optional[List[int]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate GUI inputs.
    
    Args:
        input_paths: List of input file paths
        output_dir: Output directory path
        groups: List of group numbers
        replicates: List of replicate numbers
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate input paths
    if not input_paths:
        errors.append("No input files selected")
    else:
        for path in input_paths:
            if not Path(path).exists():
                errors.append(f"Input file does not exist: {path}")
            elif not Path(path).suffix.lower() in ['.csv', '.txt']:
                errors.append(f"Unsupported file format: {path}")
    
    # Validate output directory
    if not output_dir:
        errors.append("No output directory specified")
    else:
        output_path = Path(output_dir)
        if output_path.exists() and not output_path.is_dir():
            errors.append(f"Output path is not a directory: {output_dir}")
    
    # Validate groups and replicates if provided
    if groups is not None:
        if not isinstance(groups, list):
            errors.append("Groups must be a list")
        elif any(not isinstance(g, int) or g <= 0 for g in groups):
            errors.append("All group numbers must be positive integers")
    
    if replicates is not None:
        if not isinstance(replicates, list):
            errors.append("Replicates must be a list")
        elif any(not isinstance(r, int) or r <= 0 for r in replicates):
            errors.append("All replicate numbers must be positive integers")
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        logger.warning(f"Input validation failed: {errors}")
    
    return is_valid, errors


def validate_file_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a single file path.
    
    Args:
        path: File path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path is empty"
    
    file_path = Path(path)
    
    if not file_path.exists():
        return False, f"File does not exist: {path}"
    
    if not file_path.is_file():
        return False, f"Path is not a file: {path}"
    
    if not file_path.suffix.lower() in ['.csv', '.txt']:
        return False, f"Unsupported file format: {path}"
    
    return True, None


def validate_directory_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a directory path.
    
    Args:
        path: Directory path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path is empty"
    
    dir_path = Path(path)
    
    if dir_path.exists() and not dir_path.is_dir():
        return False, f"Path exists but is not a directory: {path}"
    
    return True, None 