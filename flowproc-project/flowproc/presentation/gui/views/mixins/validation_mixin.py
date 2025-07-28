# File: flowproc/presentation/gui/views/mixins/validation_mixin.py
"""
Validation mixin for input validation.
"""

from pathlib import Path
from typing import List


class ValidationMixin:
    """
    Mixin for input validation functionality.
    
    Provides reusable validation methods.
    """

    def validate_inputs(self, input_paths: List[str], output_dir: str) -> tuple[bool, List[str]]:
        """
        Validate input paths and output directory.
        
        Args:
            input_paths: List of input file paths
            output_dir: Output directory path
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate input paths
        if not input_paths:
            errors.append("No input files selected")
        else:
            valid_paths = self.validate_file_paths(input_paths)
            if not valid_paths:
                errors.append("No valid CSV files found in selected paths")
        
        # Validate output directory
        if not self.validate_output_directory(output_dir):
            errors.append("Invalid output directory")
        
        return len(errors) == 0, errors

    def validate_file_paths(self, paths: List[str]) -> List[str]:
        """
        Validate and filter file paths.
        
        Args:
            paths: List of file paths to validate
            
        Returns:
            List of valid file paths
        """
        valid_paths = []
        for path_str in paths:
            path = Path(path_str)
            if path.exists():
                if path.is_file() and path.suffix.lower() == '.csv':
                    valid_paths.append(path_str)
                elif path.is_dir():
                    # Find CSV files in directory
                    csv_files = list(path.glob("*.csv"))
                    valid_paths.extend(str(f) for f in csv_files)
                    
        return valid_paths

    def validate_output_directory(self, output_dir: str) -> bool:
        """
        Validate output directory.
        
        Args:
            output_dir: Output directory path
            
        Returns:
            True if valid, False otherwise
        """
        if not output_dir.strip():
            return False
            
        path = Path(output_dir)
        try:
            # Try to create directory if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)
            return path.is_dir()
        except (OSError, PermissionError):
            return False