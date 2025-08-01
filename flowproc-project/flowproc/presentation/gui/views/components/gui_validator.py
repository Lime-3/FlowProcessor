"""
GUI-specific input validation component.

This module now uses the unified input validation service to eliminate code duplication
and provide consistent validation behavior across the application.
"""

from typing import List, Optional, Tuple
import logging
from flowproc.domain.validation import validate_gui_inputs, InputValidationConfig

logger = logging.getLogger(__name__)


class GUIValidator:
    """GUI-specific input validation using the unified validation service."""
    
    def __init__(self, config: Optional[InputValidationConfig] = None):
        """
        Initialize the GUI validator.
        
        Args:
            config: Validation configuration. If None, uses default configuration.
        """
        self.config = config
    
    def validate_inputs(
        self,
        input_paths: List[str],
        output_dir: str,
        groups: Optional[List[int]] = None,
        replicates: Optional[List[int]] = None,
        time_course_mode: bool = False,
        **kwargs
    ) -> Tuple[bool, List[str]]:
        """
        Validate GUI inputs using the unified validation service.
        
        Args:
            input_paths: List of input file paths
            output_dir: Output directory path
            groups: List of group numbers
            replicates: List of replicate numbers
            time_course_mode: Whether time course mode is enabled
            **kwargs: Additional validation parameters
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        result = validate_gui_inputs(
            input_paths=input_paths,
            output_dir=output_dir,
            groups=groups,
            replicates=replicates,
            time_course_mode=time_course_mode,
            config=self.config,
            **kwargs
        )
        
        if not result.is_valid:
            logger.warning(f"Input validation failed: {result.errors}")
        
        return result.is_valid, result.errors


# Create a singleton instance for easy use
gui_validator = GUIValidator()


def validate_inputs(
    input_paths: List[str],
    output_dir: str,
    groups: Optional[List[int]] = None,
    replicates: Optional[List[int]] = None,
    time_course_mode: bool = False,
    **kwargs
) -> Tuple[bool, List[str]]:
    """
    Validate GUI inputs using the singleton validator.
    
    Args:
        input_paths: List of input file paths
        output_dir: Output directory path
        groups: List of group numbers
        replicates: List of replicate numbers
        time_course_mode: Whether time course mode is enabled
        **kwargs: Additional validation parameters
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return gui_validator.validate_inputs(
        input_paths, output_dir, groups, replicates, time_course_mode, **kwargs
    ) 