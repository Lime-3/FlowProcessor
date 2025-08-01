# File: flowproc/presentation/gui/views/mixins/validation_mixin.py
"""
Validation mixin for input validation.

This mixin now uses the unified input validation service to eliminate code duplication
and provide consistent validation behavior across the application.
"""

from typing import List, Tuple
from flowproc.domain.validation import validate_input_paths, validate_output_directory, InputValidationConfig


class ValidationMixin:
    """
    Mixin for input validation functionality.
    
    Provides reusable validation methods using the unified validation service.
    """

    def __init__(self, config: InputValidationConfig = None):
        """
        Initialize the validation mixin.
        
        Args:
            config: Validation configuration. If None, uses default configuration.
        """
        self.validation_config = config

    def validate_inputs(self, input_paths: List[str], output_dir: str) -> Tuple[bool, List[str]]:
        """
        Validate input paths and output directory using the unified validation service.
        
        Args:
            input_paths: List of input file paths
            output_dir: Output directory path
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        # Validate input paths
        paths_result = validate_input_paths(input_paths, self.validation_config)
        
        # Validate output directory
        output_result = validate_output_directory(output_dir, self.validation_config)
        
        # Combine results
        errors = paths_result.errors + output_result.errors
        is_valid = len(errors) == 0
        
        return is_valid, errors

    def validate_file_paths(self, paths: List[str]) -> List[str]:
        """
        Validate and filter file paths using the unified validation service.
        
        Args:
            paths: List of file paths to validate
            
        Returns:
            List of valid file paths
        """
        result = validate_input_paths(paths, self.validation_config)
        return result.valid_paths

    def validate_output_directory(self, output_dir: str) -> bool:
        """
        Validate output directory using the unified validation service.
        
        Args:
            output_dir: Output directory path
            
        Returns:
            True if valid, False otherwise
        """
        result = validate_output_directory(output_dir, self.validation_config)
        return result.is_valid