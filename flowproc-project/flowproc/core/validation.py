"""
Configuration Validation Service - Gold Standard Implementation

This module provides a centralized, industry-standard solution for configuration validation
that eliminates code duplication and provides consistent validation across all domains.

Key Features:
- Centralized validation logic
- Domain-specific validators
- Consistent error handling
- Extensible validation rules
- Type-safe validation results
- Comprehensive validation coverage
"""

from typing import Dict, List, Any, Optional, Union, Callable, Type
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
from functools import wraps
import re

from .exceptions import ConfigurationError, ValidationError
from .constants import ProcessingMode, ExportFormat, VisualizationType, ValidationLevel

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    field: str
    message: str
    severity: ValidationSeverity
    value: Any = None
    expected_type: Optional[Type] = None
    allowed_values: Optional[List[Any]] = None
    
    def __str__(self) -> str:
        return f"{self.severity.value.upper()}: {self.field} - {self.message}"


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_config: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get all error-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get all warning-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]
    
    @property
    def info(self) -> List[ValidationIssue]:
        """Get all info-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.INFO]
    
    def add_issue(self, field: str, message: str, severity: ValidationSeverity = ValidationSeverity.ERROR,
                  value: Any = None, expected_type: Optional[Type] = None, 
                  allowed_values: Optional[List[Any]] = None) -> None:
        """Add a validation issue."""
        issue = ValidationIssue(
            field=field,
            message=message,
            severity=severity,
            value=value,
            expected_type=expected_type,
            allowed_values=allowed_values
        )
        self.issues.append(issue)
        if severity == ValidationSeverity.ERROR:
            self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for backward compatibility."""
        return {
            'valid': self.is_valid,
            'errors': [str(issue) for issue in self.errors],
            'warnings': [str(issue) for issue in self.warnings],
            'info': [str(issue) for issue in self.info],
            'validated_config': self.validated_config
        }


class BaseValidator:
    """Base class for all validators."""
    
    def __init__(self, severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.severity = severity
    
    def validate(self, value: Any, field_name: str, result: ValidationResult) -> bool:
        """Validate a value and add issues to the result."""
        raise NotImplementedError("Subclasses must implement validate method")


class TypeValidator(BaseValidator):
    """Validates that a value is of the expected type."""
    
    def __init__(self, expected_type: Type, severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(severity)
        self.expected_type = expected_type
    
    def validate(self, value: Any, field_name: str, result: ValidationResult) -> bool:
        if not isinstance(value, self.expected_type):
            result.add_issue(
                field=field_name,
                message=f"Expected {self.expected_type.__name__}, got {type(value).__name__}",
                severity=self.severity,
                value=value,
                expected_type=self.expected_type
            )
            return False
        return True


class RequiredValidator(BaseValidator):
    """Validates that a required field is present and not None."""
    
    def validate(self, value: Any, field_name: str, result: ValidationResult) -> bool:
        if value is None:
            result.add_issue(
                field=field_name,
                message="Field is required but value is None",
                severity=self.severity,
                value=value
            )
            return False
        return True


class EnumValidator(BaseValidator):
    """Validates that a value is one of the allowed enum values."""
    
    def __init__(self, enum_class: Type[Enum], severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(severity)
        self.enum_class = enum_class
        # Handle both enum classes and enum instances
        if hasattr(enum_class, '__iter__'):
            self.allowed_values = [e.value for e in enum_class]
        else:
            # For single enum values, create a list
            self.allowed_values = [enum_class.value] if hasattr(enum_class, 'value') else [enum_class]
    
    def validate(self, value: Any, field_name: str, result: ValidationResult) -> bool:
        if value not in self.allowed_values:
            result.add_issue(
                field=field_name,
                message=f"Value must be one of {self.allowed_values}",
                severity=self.severity,
                value=value,
                allowed_values=self.allowed_values
            )
            return False
        return True


class RangeValidator(BaseValidator):
    """Validates that a numeric value is within a specified range."""
    
    def __init__(self, min_value: Optional[Union[int, float]] = None, 
                 max_value: Optional[Union[int, float]] = None,
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(severity)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any, field_name: str, result: ValidationResult) -> bool:
        if not isinstance(value, (int, float)):
            result.add_issue(
                field=field_name,
                message="Value must be numeric",
                severity=self.severity,
                value=value,
                expected_type=(int, float)
            )
            return False
        
        if self.min_value is not None and value < self.min_value:
            result.add_issue(
                field=field_name,
                message=f"Value must be >= {self.min_value}",
                severity=self.severity,
                value=value
            )
            return False
        
        if self.max_value is not None and value > self.max_value:
            result.add_issue(
                field=field_name,
                message=f"Value must be <= {self.max_value}",
                severity=self.severity,
                value=value
            )
            return False
        
        return True


class ListValidator(BaseValidator):
    """Validates that a value is a list with specific constraints."""
    
    def __init__(self, min_length: Optional[int] = None, max_length: Optional[int] = None,
                 item_validator: Optional[BaseValidator] = None,
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(severity)
        self.min_length = min_length
        self.max_length = max_length
        self.item_validator = item_validator
    
    def validate(self, value: Any, field_name: str, result: ValidationResult) -> bool:
        if not isinstance(value, list):
            result.add_issue(
                field=field_name,
                message="Value must be a list",
                severity=self.severity,
                value=value,
                expected_type=list
            )
            return False
        
        if self.min_length is not None and len(value) < self.min_length:
            result.add_issue(
                field=field_name,
                message=f"List must have at least {self.min_length} items",
                severity=self.severity,
                value=value
            )
            return False
        
        if self.max_length is not None and len(value) > self.max_length:
            result.add_issue(
                field=field_name,
                message=f"List must have at most {self.max_length} items",
                severity=self.severity,
                value=value
            )
            return False
        
        if self.item_validator:
            for i, item in enumerate(value):
                item_field = f"{field_name}[{i}]"
                self.item_validator.validate(item, item_field, result)
        
        return True


class PathValidator(BaseValidator):
    """Validates file paths."""
    
    def __init__(self, must_exist: bool = False, must_be_file: bool = False,
                 must_be_directory: bool = False, allowed_extensions: Optional[List[str]] = None,
                 severity: ValidationSeverity = ValidationSeverity.ERROR):
        super().__init__(severity)
        self.must_exist = must_exist
        self.must_be_file = must_be_file
        self.must_be_directory = must_be_directory
        self.allowed_extensions = allowed_extensions
    
    def validate(self, value: Any, field_name: str, result: ValidationResult) -> bool:
        if not isinstance(value, (str, Path)):
            result.add_issue(
                field=field_name,
                message="Value must be a string or Path",
                severity=self.severity,
                value=value,
                expected_type=(str, Path)
            )
            return False
        
        path = Path(value) if isinstance(value, str) else value
        
        if self.must_exist and not path.exists():
            result.add_issue(
                field=field_name,
                message="Path must exist",
                severity=self.severity,
                value=str(path)
            )
            return False
        
        if self.must_be_file and not path.is_file():
            result.add_issue(
                field=field_name,
                message="Path must be a file",
                severity=self.severity,
                value=str(path)
            )
            return False
        
        if self.must_be_directory and not path.is_dir():
            result.add_issue(
                field=field_name,
                message="Path must be a directory",
                severity=self.severity,
                value=str(path)
            )
            return False
        
        if self.allowed_extensions and path.suffix.lower() not in self.allowed_extensions:
            result.add_issue(
                field=field_name,
                message=f"File extension must be one of {self.allowed_extensions}",
                severity=self.severity,
                value=str(path)
            )
            return False
        
        return True


class ConfigurationValidator:
    """
    Centralized configuration validation service.
    
    This service provides a unified interface for validating configurations
    across all domains (processing, export, visualization, etc.).
    """
    
    def __init__(self):
        self._validators: Dict[str, Dict[str, BaseValidator]] = {}
        self._setup_default_validators()
    
    def _setup_default_validators(self) -> None:
        """Setup default validation rules for each domain."""
        
        # Processing validation rules
        self._validators['processing'] = {
            'mode': EnumValidator(ProcessingMode),
            'group_by': ListValidator(item_validator=TypeValidator(str)),
            'aggregation_methods': ListValidator(
                min_length=1,
                item_validator=TypeValidator(str)
            ),
            'chunk_size': RangeValidator(min_value=100, max_value=10000),
            'max_workers': RangeValidator(min_value=1, max_value=32),
            'memory_limit_gb': RangeValidator(min_value=0.1, max_value=100.0),
            'time_course': TypeValidator(bool),
            'auto_detect_columns': TypeValidator(bool),
            'validate_data': TypeValidator(bool)
        }
        
        # Export validation rules
        self._validators['export'] = {
            'format': EnumValidator(ExportFormat),
            'include_index': TypeValidator(bool),
            'include_headers': TypeValidator(bool),
            'auto_adjust_columns': TypeValidator(bool),
            'sheet_name': TypeValidator(str),
            'decimal_places': RangeValidator(min_value=0, max_value=10),
            'separator': TypeValidator(str),
            'orient': TypeValidator(str),
            'compression': TypeValidator(str),
            'engine': TypeValidator(str)
        }
        
        # Visualization validation rules
        self._validators['visualization'] = {
            'type': EnumValidator(VisualizationType),
            'theme': TypeValidator(str),
            'width': RangeValidator(min_value=300, max_value=3000),
            'height': RangeValidator(min_value=300, max_value=1500),
            'dpi': RangeValidator(min_value=72, max_value=1200),
            'show_legend': TypeValidator(bool),
            'show_grid': TypeValidator(bool),
            'title': TypeValidator(str),
            'x_label': TypeValidator(str),
            'y_label': TypeValidator(str),
            'color_palette': ListValidator(item_validator=TypeValidator(str))
        }
        
        # File path validation rules
        self._validators['paths'] = {
            'input_paths': ListValidator(
                min_length=1,
                item_validator=PathValidator(must_exist=True, must_be_file=True)
            ),
            'output_dir': PathValidator(must_exist=False, must_be_directory=True),
            'filepath': PathValidator(must_exist=False, must_be_file=False)
        }
    
    def validate_processing_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate processing configuration."""
        return self._validate_domain_config(config, 'processing')
    
    def validate_export_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate export configuration."""
        return self._validate_domain_config(config, 'export')
    
    def validate_visualization_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate visualization configuration."""
        return self._validate_domain_config(config, 'visualization')
    
    def validate_paths_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate file paths configuration."""
        return self._validate_domain_config(config, 'paths')
    
    def validate_workflow_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate complete workflow configuration."""
        result = ValidationResult(is_valid=True, validated_config=config.copy())
        
        # Validate each domain section
        if 'parsing' in config:
            # Basic parsing validation
            parsing_config = config['parsing']
            if 'strategy' in parsing_config:
                if not isinstance(parsing_config['strategy'], str):
                    result.add_issue('parsing.strategy', 'Strategy must be a string')
        
        if 'processing' in config:
            processing_result = self.validate_processing_config(config['processing'])
            result.issues.extend(processing_result.issues)
            result.is_valid = result.is_valid and processing_result.is_valid
        
        if 'visualization' in config:
            viz_config = config['visualization']
            if 'plots' in viz_config:
                if not isinstance(viz_config['plots'], list):
                    result.add_issue('visualization.plots', 'Plots must be a list')
                else:
                    for i, plot_config in enumerate(viz_config['plots']):
                        plot_result = self.validate_visualization_config(plot_config)
                        for issue in plot_result.issues:
                            issue.field = f"visualization.plots[{i}].{issue.field}"
                            result.issues.append(issue)
                        result.is_valid = result.is_valid and plot_result.is_valid
        
        if 'export' in config:
            export_result = self.validate_export_config(config['export'])
            result.issues.extend(export_result.issues)
            result.is_valid = result.is_valid and export_result.is_valid
        
        return result
    
    def _validate_domain_config(self, config: Dict[str, Any], domain: str) -> ValidationResult:
        """Validate configuration for a specific domain."""
        result = ValidationResult(is_valid=True, validated_config=config.copy())
        
        if domain not in self._validators:
            logger.warning(f"No validators defined for domain: {domain}")
            return result
        
        validators = self._validators[domain]
        
        for field_name, validator in validators.items():
            if field_name in config:
                validator.validate(config[field_name], field_name, result)
        
        return result
    
    def add_validator(self, domain: str, field_name: str, validator: BaseValidator) -> None:
        """Add a custom validator for a specific domain and field."""
        if domain not in self._validators:
            self._validators[domain] = {}
        self._validators[domain][field_name] = validator
    
    def remove_validator(self, domain: str, field_name: str) -> None:
        """Remove a validator for a specific domain and field."""
        if domain in self._validators and field_name in self._validators[domain]:
            del self._validators[domain][field_name]


# Global validator instance
_global_validator = None

def get_configuration_validator() -> ConfigurationValidator:
    """Get the global configuration validator instance."""
    global _global_validator
    if _global_validator is None:
        _global_validator = ConfigurationValidator()
    return _global_validator


def validate_config(config: Dict[str, Any], domain: str = 'workflow') -> ValidationResult:
    """
    Convenience function for validating configuration.
    
    Args:
        config: Configuration to validate
        domain: Domain to validate ('processing', 'export', 'visualization', 'workflow')
        
    Returns:
        ValidationResult with validation status and issues
    """
    validator = get_configuration_validator()
    
    if domain == 'workflow':
        return validator.validate_workflow_config(config)
    elif domain == 'processing':
        return validator.validate_processing_config(config)
    elif domain == 'export':
        return validator.validate_export_config(config)
    elif domain == 'visualization':
        return validator.validate_visualization_config(config)
    elif domain == 'paths':
        return validator.validate_paths_config(config)
    else:
        raise ValueError(f"Unknown validation domain: {domain}")


def validation_error_handler(func: Callable) -> Callable:
    """
    Decorator to handle validation errors consistently.
    
    This decorator catches ValidationError and ConfigurationError exceptions
    and converts them to a standardized format.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValidationError, ConfigurationError) as e:
            logger.error(f"Validation error in {func.__name__}: {e}")
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': [],
                'validated_config': {}
            }
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return {
                'valid': False,
                'errors': [f"Unexpected error: {str(e)}"],
                'warnings': [],
                'validated_config': {}
            }
    return wrapper 