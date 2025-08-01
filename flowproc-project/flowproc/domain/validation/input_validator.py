"""
Unified input validation service for GUI inputs.

This module consolidates all input validation logic from the GUI layer into a single,
maintainable service that eliminates code duplication and provides consistent validation.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InputValidationResult:
    """Result of input validation operations."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    file_count: int = 0
    total_size: int = 0
    valid_paths: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def __bool__(self) -> bool:
        return self.is_valid


@dataclass
class InputValidationConfig:
    """Configuration for input validation operations."""
    # File validation settings
    allowed_extensions: List[str] = field(default_factory=lambda: ['.csv'])
    max_file_size_mb: int = 500
    min_file_size_bytes: int = 1
    
    # Directory validation settings
    allow_empty_directories: bool = False
    max_files_per_directory: int = 1000
    
    # Processing options validation
    require_groups_for_time_course: bool = True
    require_replicates_for_time_course: bool = True
    max_groups: int = 100
    max_replicates: int = 100
    
    # Error handling
    raise_on_error: bool = False
    log_warnings: bool = True
    
    # Performance settings
    check_disk_space: bool = True
    min_disk_space_mb: int = 100


class InputValidator:
    """
    Unified input validator for GUI inputs.
    
    This class consolidates all input validation logic from the GUI layer,
    eliminating code duplication and providing consistent validation behavior.
    """
    
    def __init__(self, config: Optional[InputValidationConfig] = None):
        """
        Initialize the input validator.
        
        Args:
            config: Validation configuration. If None, uses default configuration.
        """
        self.config = config or InputValidationConfig()
    
    def validate_gui_inputs(
        self,
        input_paths: List[str],
        output_dir: str,
        groups: Optional[List[int]] = None,
        replicates: Optional[List[int]] = None,
        time_course_mode: bool = False,
        **kwargs
    ) -> InputValidationResult:
        """
        Comprehensive validation of GUI inputs.
        
        Args:
            input_paths: List of input file/directory paths
            output_dir: Output directory path
            groups: List of group numbers
            replicates: List of replicate numbers
            time_course_mode: Whether time course mode is enabled
            **kwargs: Additional validation parameters
            
        Returns:
            InputValidationResult containing validation results
        """
        result = InputValidationResult(is_valid=True)
        
        # Step 1: Validate input paths
        paths_result = self.validate_input_paths(input_paths)
        result.errors.extend(paths_result.errors)
        result.warnings.extend(paths_result.warnings)
        result.file_count = paths_result.file_count
        result.total_size = paths_result.total_size
        result.valid_paths = paths_result.valid_paths
        
        if not paths_result.is_valid:
            result.is_valid = False
        
        # Step 2: Validate output directory
        output_result = self.validate_output_directory(output_dir)
        result.errors.extend(output_result.errors)
        result.warnings.extend(output_result.warnings)
        
        if not output_result.is_valid:
            result.is_valid = False
        
        # Step 3: Validate processing options
        options_result = self.validate_processing_options(
            groups=groups,
            replicates=replicates,
            time_course_mode=time_course_mode,
            **kwargs
        )
        result.errors.extend(options_result.errors)
        result.warnings.extend(options_result.warnings)
        
        if not options_result.is_valid:
            result.is_valid = False
        
        # Log warnings if enabled
        if self.config.log_warnings and result.warnings:
            for warning in result.warnings:
                logger.warning(warning)
        
        # Handle errors based on configuration
        if not result.is_valid and self.config.raise_on_error:
            error_msg = "; ".join(result.errors)
            raise ValueError(f"Input validation failed: {error_msg}")
        
        return result
    
    def validate_input_paths(self, paths: List[str]) -> InputValidationResult:
        """
        Validate input file/directory paths.
        
        Args:
            paths: List of paths to validate
            
        Returns:
            InputValidationResult containing validation results
        """
        result = InputValidationResult(is_valid=True)
        
        if not paths:
            result.add_error("No input files or directories specified")
            return result
        
        for path_str in paths:
            if not path_str.strip():
                result.add_error("Empty path specified")
                continue
            
            path = Path(path_str)
            
            # Check if path exists
            if not path.exists():
                result.add_error(f"Path does not exist: {path_str}")
                continue
            
            # Validate based on path type
            if path.is_file():
                file_result = self._validate_file(path)
                if file_result.is_valid:
                    result.file_count += 1
                    result.total_size += path.stat().st_size
                    result.valid_paths.append(path_str)
                else:
                    result.errors.extend(file_result.errors)
                result.warnings.extend(file_result.warnings)
                
            elif path.is_dir():
                dir_result = self._validate_directory(path)
                if dir_result.is_valid:
                    result.file_count += dir_result.file_count
                    result.total_size += dir_result.total_size
                    result.valid_paths.extend(dir_result.valid_paths)
                else:
                    result.errors.extend(dir_result.errors)
                result.warnings.extend(dir_result.warnings)
                
            else:
                result.add_error(f"Path is neither file nor directory: {path_str}")
        
        # Check if any valid files were found
        if result.file_count == 0:
            result.add_error("No valid input files found")
        
        # Check for potential issues
        if result.total_size > self.config.max_file_size_mb * 1024 * 1024:
            result.add_warning(
                f"Large dataset detected ({result.total_size / 1024 / 1024:.1f} MB). "
                "Processing may take a while."
            )
        
        if len(paths) > 50:
            result.add_warning(
                f"Many input files detected ({len(paths)}). "
                "Consider processing in batches."
            )
        
        return result
    
    def validate_output_directory(self, output_dir: str) -> InputValidationResult:
        """
        Validate output directory.
        
        Args:
            output_dir: Output directory path
            
        Returns:
            InputValidationResult containing validation results
        """
        result = InputValidationResult(is_valid=True)
        
        if not output_dir.strip():
            result.add_error("Output directory path is empty")
            return result
        
        path = Path(output_dir)
        
        try:
            if path.exists():
                if not path.is_dir():
                    result.add_error(f"Output path exists but is not a directory: {output_dir}")
                else:
                    # Check if directory is writable
                    test_file = path / ".test_write"
                    try:
                        test_file.touch()
                        test_file.unlink()
                    except OSError:
                        result.add_error(f"Output directory is not writable: {output_dir}")
                    
                    # Check available space if enabled
                    if self.config.check_disk_space:
                        self._check_disk_space(path, result)
            else:
                # Try to create directory
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    result.add_error(f"Cannot create output directory {output_dir}: {e}")
                    
        except Exception as e:
            result.add_error(f"Error validating output directory {output_dir}: {e}")
        
        return result
    
    def validate_processing_options(
        self,
        groups: Optional[List[int]] = None,
        replicates: Optional[List[int]] = None,
        time_course_mode: bool = False,
        **kwargs
    ) -> InputValidationResult:
        """
        Validate processing options.
        
        Args:
            groups: List of group numbers
            replicates: List of replicate numbers
            time_course_mode: Whether time course mode is enabled
            **kwargs: Additional processing options
            
        Returns:
            InputValidationResult containing validation results
        """
        result = InputValidationResult(is_valid=True)
        
        # Validate groups
        if groups is not None:
            if not isinstance(groups, list):
                result.add_error("Groups must be a list")
            elif len(groups) == 0:
                result.add_error("Groups list cannot be empty")
            elif len(groups) > self.config.max_groups:
                result.add_warning(f"Large number of groups specified ({len(groups)})")
            else:
                for g in groups:
                    if not isinstance(g, int) or g <= 0:
                        result.add_error("All group numbers must be positive integers")
                        break
        
        # Validate replicates
        if replicates is not None:
            if not isinstance(replicates, list):
                result.add_error("Replicates must be a list")
            elif len(replicates) == 0:
                result.add_error("Replicates list cannot be empty")
            elif len(replicates) > self.config.max_replicates:
                result.add_warning(f"Large number of replicates specified ({len(replicates)})")
            else:
                for r in replicates:
                    if not isinstance(r, int) or r <= 0:
                        result.add_error("All replicate numbers must be positive integers")
                        break
        
        # Validate time course mode requirements
        if time_course_mode:
            if self.config.require_groups_for_time_course and not groups:
                result.add_error("Time course mode requires groups to be specified")
            if self.config.require_replicates_for_time_course and not replicates:
                result.add_error("Time course mode requires replicates to be specified")
        
        return result
    
    def _validate_file(self, file_path: Path) -> InputValidationResult:
        """Validate a single file."""
        result = InputValidationResult(is_valid=True)
        
        # Check file extension
        if file_path.suffix.lower() not in self.config.allowed_extensions:
            result.add_error(f"Unsupported file format: {file_path.suffix}")
            return result
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size < self.config.min_file_size_bytes:
                result.add_error(f"File is too small: {file_path}")
            elif file_size > self.config.max_file_size_mb * 1024 * 1024:
                result.add_warning(
                    f"Large file detected ({file_size / 1024 / 1024:.1f} MB): {file_path}"
                )
        except OSError as e:
            result.add_error(f"Cannot access file {file_path}: {e}")
        
        return result
    
    def _validate_directory(self, dir_path: Path) -> InputValidationResult:
        """Validate a directory and its contents."""
        result = InputValidationResult(is_valid=True)
        
        try:
            # Find files with allowed extensions
            valid_files = []
            for ext in self.config.allowed_extensions:
                valid_files.extend(dir_path.glob(f"*{ext}"))
            
            if not valid_files and not self.config.allow_empty_directories:
                result.add_error(f"No valid files found in directory: {dir_path}")
                return result
            
            if len(valid_files) > self.config.max_files_per_directory:
                result.add_warning(
                    f"Many files in directory ({len(valid_files)}): {dir_path}"
                )
            
            # Validate each file
            for file_path in valid_files:
                file_result = self._validate_file(file_path)
                if file_result.is_valid:
                    result.file_count += 1
                    result.total_size += file_path.stat().st_size
                    result.valid_paths.append(str(file_path))
                else:
                    result.errors.extend(file_result.errors)
                result.warnings.extend(file_result.warnings)
                
        except PermissionError:
            result.add_error(f"Permission denied accessing directory: {dir_path}")
        except Exception as e:
            result.add_error(f"Error validating directory {dir_path}: {e}")
        
        return result
    
    def _check_disk_space(self, path: Path, result: InputValidationResult) -> None:
        """Check available disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            if free < self.config.min_disk_space_mb * 1024 * 1024:
                result.add_warning(
                    f"Low disk space available ({free / 1024 / 1024:.1f} MB)"
                )
        except OSError:
            result.add_warning("Cannot determine available disk space")


# Convenience functions for backward compatibility
def validate_input_paths(paths: List[str], config: Optional[InputValidationConfig] = None) -> InputValidationResult:
    """Validate input paths using the unified validator."""
    validator = InputValidator(config)
    return validator.validate_input_paths(paths)


def validate_output_directory(output_dir: str, config: Optional[InputValidationConfig] = None) -> InputValidationResult:
    """Validate output directory using the unified validator."""
    validator = InputValidator(config)
    return validator.validate_output_directory(output_dir)


def validate_processing_options(
    groups: Optional[List[int]] = None,
    replicates: Optional[List[int]] = None,
    time_course_mode: bool = False,
    config: Optional[InputValidationConfig] = None,
    **kwargs
) -> InputValidationResult:
    """Validate processing options using the unified validator."""
    validator = InputValidator(config)
    return validator.validate_processing_options(groups, replicates, time_course_mode, **kwargs)


def validate_gui_inputs(
    input_paths: List[str],
    output_dir: str,
    groups: Optional[List[int]] = None,
    replicates: Optional[List[int]] = None,
    time_course_mode: bool = False,
    config: Optional[InputValidationConfig] = None,
    **kwargs
) -> InputValidationResult:
    """Validate all GUI inputs using the unified validator."""
    validator = InputValidator(config)
    return validator.validate_gui_inputs(
        input_paths, output_dir, groups, replicates, time_course_mode, **kwargs
    ) 