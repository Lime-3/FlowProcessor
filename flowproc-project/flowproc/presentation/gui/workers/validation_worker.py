"""
Validation Worker for background input validation.

This worker now uses the unified input validation service to eliminate code duplication
and provide consistent validation behavior across the application.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal, QObject

from flowproc.domain.validation import validate_gui_inputs, InputValidationConfig, InputValidationResult
from ....core.models import ProcessingOptions

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    file_count: int = 0
    total_size: int = 0
    supported_formats: List[str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['.csv']


class ValidationWorker(QThread):
    """
    Worker thread for validating user inputs.
    
    This worker validates:
    - File existence and accessibility
    - File format compatibility
    - Directory structure
    - Processing options
    """
    
    # Signals
    validation_started = Signal()
    validation_progress = Signal(int, str)  # progress, message
    validation_completed = Signal(ValidationResult)
    validation_error = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._should_cancel = False
        self._validation_task = None
        
    def validate_inputs(
        self,
        input_paths: List[Path],
        output_dir: Path,
        options: ProcessingOptions
    ) -> None:
        """
        Start validation of inputs.
        
        Args:
            input_paths: List of input file/directory paths
            output_dir: Output directory path
            options: Processing options to validate
        """
        self._validation_task = {
            'input_paths': input_paths,
            'output_dir': output_dir,
            'options': options
        }
        self._should_cancel = False
        self.start()
        
    def cancel_validation(self) -> None:
        """Cancel the current validation operation."""
        self._should_cancel = True
        
    def run(self) -> None:
        """Execute the validation in the background thread."""
        if not self._validation_task:
            self.validation_error.emit("No validation task set")
            return
            
        try:
            self.validation_started.emit()
            
            input_paths = self._validation_task['input_paths']
            output_dir = self._validation_task['output_dir']
            options = self._validation_task['options']
            
            result = self._perform_validation(input_paths, output_dir, options)
            
            if not self._should_cancel:
                self.validation_completed.emit(result)
                
        except Exception as e:
            logger.error(f"Validation error: {e}")
            if not self._should_cancel:
                self.validation_error.emit(f"Validation failed: {str(e)}")
                
    def _perform_validation(
        self,
        input_paths: List[Path],
        output_dir: Path,
        options: ProcessingOptions
    ) -> ValidationResult:
        """
        Perform the actual validation using the unified validation service.
        
        Args:
            input_paths: List of input paths to validate
            output_dir: Output directory to validate
            options: Processing options to validate
            
        Returns:
            ValidationResult containing validation results
        """
        # Convert Path objects to strings for the unified validator
        input_path_strings = [str(path) for path in input_paths]
        output_dir_string = str(output_dir)
        
        # Validate using the unified service
        self.validation_progress.emit(10, "Validating inputs...")
        if self._should_cancel:
            return ValidationResult(False, ["Validation cancelled"], [])
        
        # Extract processing options for validation
        groups = getattr(options, 'user_groups', None)
        replicates = getattr(options, 'user_replicates', None)
        time_course_mode = getattr(options, 'time_course_mode', False)
        
        # Use the unified validation service
        result = validate_gui_inputs(
            input_paths=input_path_strings,
            output_dir=output_dir_string,
            groups=groups,
            replicates=replicates,
            time_course_mode=time_course_mode
        )
        
        if self._should_cancel:
            return ValidationResult(False, ["Validation cancelled"], [])
        
        self.validation_progress.emit(100, "Validation complete")
        
        # Convert to ValidationResult format
        return ValidationResult(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings,
            file_count=result.file_count,
            total_size=result.total_size,
            supported_formats=['.csv']
        )
        
    # Note: All validation logic has been moved to the unified validation service
    # The following methods are no longer needed as they are handled by the unified service 