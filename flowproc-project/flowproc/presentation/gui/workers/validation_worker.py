"""
Validation Worker for background input validation.

This worker handles validation of user inputs in a background thread
to keep the GUI responsive during validation operations.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal, QObject

from ....domain.parsing.validators import validate_csv_file, validate_directory
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
        Perform the actual validation.
        
        Args:
            input_paths: List of input paths to validate
            output_dir: Output directory to validate
            options: Processing options to validate
            
        Returns:
            ValidationResult containing validation results
        """
        errors = []
        warnings = []
        file_count = 0
        total_size = 0
        supported_formats = ['.csv']
        
        # Validate input paths
        self.validation_progress.emit(10, "Validating input paths...")
        if self._should_cancel:
            return ValidationResult(False, ["Validation cancelled"], [])
            
        for i, path in enumerate(input_paths):
            if self._should_cancel:
                return ValidationResult(False, ["Validation cancelled"], [])
                
            progress = 10 + (i * 30) // len(input_paths)
            self.validation_progress.emit(progress, f"Validating {path.name}...")
            
            # Check if path exists
            if not path.exists():
                errors.append(f"Path does not exist: {path}")
                continue
                
            # Validate based on path type
            if path.is_file():
                file_result = self._validate_file(path)
                if file_result.is_valid:
                    file_count += 1
                    total_size += path.stat().st_size
                else:
                    errors.extend(file_result.errors)
                warnings.extend(file_result.warnings)
                
            elif path.is_dir():
                dir_result = self._validate_directory(path)
                if dir_result.is_valid:
                    file_count += dir_result.file_count
                    total_size += dir_result.total_size
                else:
                    errors.extend(dir_result.errors)
                warnings.extend(dir_result.warnings)
                
            else:
                errors.append(f"Path is neither file nor directory: {path}")
                
        # Validate output directory
        self.validation_progress.emit(50, "Validating output directory...")
        if self._should_cancel:
            return ValidationResult(False, ["Validation cancelled"], [])
            
        output_result = self._validate_output_directory(output_dir)
        if not output_result.is_valid:
            errors.extend(output_result.errors)
        warnings.extend(output_result.warnings)
        
        # Validate processing options
        self.validation_progress.emit(70, "Validating processing options...")
        if self._should_cancel:
            return ValidationResult(False, ["Validation cancelled"], [])
            
        options_result = self._validate_processing_options(options)
        if not options_result.is_valid:
            errors.extend(options_result.errors)
        warnings.extend(options_result.warnings)
        
        # Final validation checks
        self.validation_progress.emit(90, "Performing final checks...")
        if self._should_cancel:
            return ValidationResult(False, ["Validation cancelled"], [])
            
        if file_count == 0:
            errors.append("No valid input files found")
            
        # Check for potential issues
        if total_size > 100 * 1024 * 1024:  # 100MB
            warnings.append(f"Large dataset detected ({total_size / 1024 / 1024:.1f} MB). Processing may take a while.")
            
        if len(input_paths) > 50:
            warnings.append(f"Many input files detected ({len(input_paths)}). Consider processing in batches.")
            
        self.validation_progress.emit(100, "Validation complete")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            file_count=file_count,
            total_size=total_size,
            supported_formats=supported_formats
        )
        
    def _validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a single file."""
        errors = []
        warnings = []
        
        # Check file extension
        if file_path.suffix.lower() not in ['.csv']:
            errors.append(f"Unsupported file format: {file_path.suffix}")
            return ValidationResult(False, errors, warnings)
            
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                errors.append(f"File is empty: {file_path}")
            elif file_size > 500 * 1024 * 1024:  # 500MB
                warnings.append(f"Large file detected ({file_size / 1024 / 1024:.1f} MB): {file_path}")
        except OSError as e:
            errors.append(f"Cannot access file {file_path}: {e}")
            
        # Validate CSV format
        try:
            csv_result = validate_csv_file(file_path)
            if not csv_result.is_valid:
                errors.extend(csv_result.errors)
            warnings.extend(csv_result.warnings)
        except Exception as e:
            errors.append(f"Failed to validate CSV file {file_path}: {e}")
            
        return ValidationResult(len(errors) == 0, errors, warnings)
        
    def _validate_directory(self, dir_path: Path) -> ValidationResult:
        """Validate a directory and its contents."""
        errors = []
        warnings = []
        file_count = 0
        total_size = 0
        
        try:
            # Check if directory is accessible
            if not dir_path.is_dir():
                errors.append(f"Path is not a directory: {dir_path}")
                return ValidationResult(False, errors, warnings)
                
            # Find CSV files in directory
            csv_files = list(dir_path.glob("*.csv"))
            if not csv_files:
                errors.append(f"No CSV files found in directory: {dir_path}")
                return ValidationResult(False, errors, warnings)
                
            # Validate each CSV file
            for csv_file in csv_files:
                file_result = self._validate_file(csv_file)
                if file_result.is_valid:
                    file_count += 1
                    total_size += csv_file.stat().st_size
                else:
                    errors.extend(file_result.errors)
                warnings.extend(file_result.warnings)
                
        except PermissionError:
            errors.append(f"Permission denied accessing directory: {dir_path}")
        except Exception as e:
            errors.append(f"Error validating directory {dir_path}: {e}")
            
        return ValidationResult(
            len(errors) == 0,
            errors,
            warnings,
            file_count,
            total_size
        )
        
    def _validate_output_directory(self, output_dir: Path) -> ValidationResult:
        """Validate the output directory."""
        errors = []
        warnings = []
        
        try:
            if output_dir.exists():
                if not output_dir.is_dir():
                    errors.append(f"Output path exists but is not a directory: {output_dir}")
                else:
                    # Check if directory is writable
                    test_file = output_dir / ".test_write"
                    try:
                        test_file.touch()
                        test_file.unlink()
                    except OSError:
                        errors.append(f"Output directory is not writable: {output_dir}")
                        
                    # Check available space
                    import shutil
                    try:
                        total, used, free = shutil.disk_usage(output_dir)
                        if free < 100 * 1024 * 1024:  # 100MB
                            warnings.append(f"Low disk space available ({free / 1024 / 1024:.1f} MB)")
                    except OSError:
                        warnings.append("Cannot determine available disk space")
            else:
                # Try to create directory
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    errors.append(f"Cannot create output directory {output_dir}: {e}")
                    
        except Exception as e:
            errors.append(f"Error validating output directory {output_dir}: {e}")
            
        return ValidationResult(len(errors) == 0, errors, warnings)
        
    def _validate_processing_options(self, options: ProcessingOptions) -> ValidationResult:
        """Validate processing options."""
        errors = []
        warnings = []
        
        # Validate time course mode options
        if options.time_course_mode:
            if not options.user_replicates:
                errors.append("Time course mode requires user replicates to be specified")
            if not options.user_groups:
                errors.append("Time course mode requires user groups to be specified")
                
        # Validate group options
        if options.user_groups and options.auto_parse_groups:
            warnings.append("Both manual groups and auto-parse groups are enabled. Manual groups will take precedence.")
            
        # Validate replicate options
        if options.user_replicates:
            if len(options.user_replicates) == 0:
                errors.append("User replicates list cannot be empty")
            elif len(options.user_replicates) > 100:
                warnings.append(f"Large number of replicates specified ({len(options.user_replicates)})")
                
        return ValidationResult(len(errors) == 0, errors, warnings) 