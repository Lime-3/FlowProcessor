"""
Unit tests for Configuration Validation Service.

This module tests the gold standard configuration validation implementation
to ensure it properly validates configurations across all domains.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from flowproc.core.validation import (
    ConfigurationValidator, ValidationResult, ValidationIssue, ValidationSeverity,
    TypeValidator, RequiredValidator, EnumValidator, RangeValidator, ListValidator,
    PathValidator, validate_config, get_configuration_validator
)
from flowproc.core.constants import ProcessingMode, ExportFormat, VisualizationType
from flowproc.core.exceptions import ValidationError, ConfigurationError


class TestValidationIssue:
    """Test ValidationIssue dataclass."""
    
    def test_validation_issue_creation(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            field="test_field",
            message="Test message",
            severity=ValidationSeverity.ERROR,
            value="test_value"
        )
        
        assert issue.field == "test_field"
        assert issue.message == "Test message"
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.value == "test_value"
    
    def test_validation_issue_string_representation(self):
        """Test string representation of validation issue."""
        issue = ValidationIssue(
            field="test_field",
            message="Test message",
            severity=ValidationSeverity.WARNING
        )
        
        assert str(issue) == "WARNING: test_field - Test message"


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_creation(self):
        """Test creating a validation result."""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validation_result_with_issues(self):
        """Test validation result with issues."""
        result = ValidationResult(is_valid=True)
        
        result.add_issue("field1", "Error message", ValidationSeverity.ERROR)
        result.add_issue("field2", "Warning message", ValidationSeverity.WARNING)
        result.add_issue("field3", "Info message", ValidationSeverity.INFO)
        
        assert len(result.issues) == 3
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.info) == 1
        assert result.is_valid is False  # Should be False due to error
    
    def test_validation_result_to_dict(self):
        """Test converting validation result to dictionary."""
        result = ValidationResult(is_valid=True)
        result.add_issue("field1", "Error message", ValidationSeverity.ERROR)
        result.add_issue("field2", "Warning message", ValidationSeverity.WARNING)
        
        result_dict = result.to_dict()
        
        assert result_dict['valid'] is False
        assert len(result_dict['errors']) == 1
        assert len(result_dict['warnings']) == 1
        assert len(result_dict['info']) == 0


class TestBaseValidators:
    """Test base validator classes."""
    
    def test_type_validator_success(self):
        """Test TypeValidator with valid type."""
        validator = TypeValidator(str)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate("test", "field", result) is True
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_type_validator_failure(self):
        """Test TypeValidator with invalid type."""
        validator = TypeValidator(str)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(123, "field", result) is False
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Expected str" in result.errors[0].message
    
    def test_required_validator_success(self):
        """Test RequiredValidator with valid value."""
        validator = RequiredValidator()
        result = ValidationResult(is_valid=True)
        
        assert validator.validate("test", "field", result) is True
        assert result.is_valid is True
    
    def test_required_validator_failure(self):
        """Test RequiredValidator with None value."""
        validator = RequiredValidator()
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(None, "field", result) is False
        assert result.is_valid is False
        assert len(result.errors) == 1
    
    def test_enum_validator_success(self):
        """Test EnumValidator with valid value."""
        validator = EnumValidator(ProcessingMode)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(ProcessingMode.SINGLE_FILE.value, "field", result) is True
        assert result.is_valid is True
    
    def test_enum_validator_failure(self):
        """Test EnumValidator with invalid value."""
        validator = EnumValidator(ProcessingMode)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate("invalid", "field", result) is False
        assert result.is_valid is False
        assert len(result.errors) == 1
    
    def test_range_validator_success(self):
        """Test RangeValidator with valid value."""
        validator = RangeValidator(min_value=0, max_value=100)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(50, "field", result) is True
        assert result.is_valid is True
    
    def test_range_validator_failure_below_min(self):
        """Test RangeValidator with value below minimum."""
        validator = RangeValidator(min_value=0, max_value=100)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(-10, "field", result) is False
        assert result.is_valid is False
        assert len(result.errors) == 1
    
    def test_range_validator_failure_above_max(self):
        """Test RangeValidator with value above maximum."""
        validator = RangeValidator(min_value=0, max_value=100)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(150, "field", result) is False
        assert result.is_valid is False
        assert len(result.errors) == 1
    
    def test_list_validator_success(self):
        """Test ListValidator with valid list."""
        validator = ListValidator(min_length=1, max_length=5)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(["item1", "item2"], "field", result) is True
        assert result.is_valid is True
    
    def test_list_validator_failure_too_short(self):
        """Test ListValidator with list too short."""
        validator = ListValidator(min_length=2)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(["item1"], "field", result) is False
        assert result.is_valid is False
        assert len(result.errors) == 1
    
    def test_path_validator_success(self, tmp_path):
        """Test PathValidator with valid path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        validator = PathValidator(must_exist=True, must_be_file=True)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate(str(test_file), "field", result) is True
        assert result.is_valid is True
    
    def test_path_validator_failure_nonexistent(self):
        """Test PathValidator with nonexistent path."""
        validator = PathValidator(must_exist=True)
        result = ValidationResult(is_valid=True)
        
        assert validator.validate("/nonexistent/path", "field", result) is False
        assert result.is_valid is False
        assert len(result.errors) == 1


class TestConfigurationValidator:
    """Test ConfigurationValidator class."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = ConfigurationValidator()
        
        assert 'processing' in validator._validators
        assert 'export' in validator._validators
        assert 'visualization' in validator._validators
        assert 'paths' in validator._validators
    
    def test_validate_processing_config_success(self):
        """Test successful processing config validation."""
        validator = ConfigurationValidator()
        config = {
            'mode': ProcessingMode.SINGLE_FILE.value,
            'group_by': ['group', 'time'],
            'aggregation_methods': ['mean', 'std'],
            'chunk_size': 1000,
            'max_workers': 4,
            'memory_limit_gb': 4.0,
            'time_course': True,
            'auto_detect_columns': True,
            'validate_data': True
        }
        
        result = validator.validate_processing_config(config)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validate_processing_config_failure(self):
        """Test processing config validation with invalid values."""
        validator = ConfigurationValidator()
        config = {
            'mode': 'invalid_mode',
            'chunk_size': -100,  # Invalid negative value
            'max_workers': 0,    # Invalid zero value
            'aggregation_methods': 'not_a_list'  # Invalid type
        }
        
        result = validator.validate_processing_config(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 3  # Should have at least 3 errors
    
    def test_validate_export_config_success(self):
        """Test successful export config validation."""
        validator = ConfigurationValidator()
        config = {
            'format': ExportFormat.EXCEL.value,
            'include_index': False,
            'include_headers': True,
            'auto_adjust_columns': True,
            'sheet_name': 'Sheet1',
            'decimal_places': 2
        }
        
        result = validator.validate_export_config(config)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validate_export_config_failure(self):
        """Test export config validation with invalid values."""
        validator = ConfigurationValidator()
        config = {
            'format': 'invalid_format',
            'decimal_places': 15,  # Too high
            'include_index': 'not_boolean'  # Wrong type
        }
        
        result = validator.validate_export_config(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2
    
    def test_validate_visualization_config_success(self):
        """Test successful visualization config validation."""
        validator = ConfigurationValidator()
        config = {
            'type': VisualizationType.BAR_PLOT.value,
            'theme': 'plotly',
            'width': 600,
            'height': 400,
            'dpi': 300,
            'show_legend': True,
            'show_grid': False,
            'title': 'Test Plot',
            'color_palette': ['red', 'blue', 'green']
        }
        
        result = validator.validate_visualization_config(config)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validate_visualization_config_failure(self):
        """Test visualization config validation with invalid values."""
        validator = ConfigurationValidator()
        config = {
            'type': 'invalid_type',
            'width': 100,   # Too small
            'height': 5000, # Too large
            'dpi': 50       # Too low
        }
        
        result = validator.validate_visualization_config(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 3
    
    def test_validate_workflow_config_success(self):
        """Test successful workflow config validation."""
        validator = ConfigurationValidator()
        config = {
            'parsing': {
                'strategy': 'auto'
            },
            'processing': {
                'mode': ProcessingMode.SINGLE_FILE.value,
                'group_by': ['group'],
                'aggregation_methods': ['mean']
            },
            'visualization': {
                'plots': [
                    {
                        'type': VisualizationType.BAR_PLOT.value,
                        'width': 600,
                        'height': 400
                    }
                ]
            },
            'export': {
                'format': ExportFormat.EXCEL.value,
                'include_index': False
            }
        }
        
        result = validator.validate_workflow_config(config)
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validate_workflow_config_failure(self):
        """Test workflow config validation with invalid values."""
        validator = ConfigurationValidator()
        config = {
            'parsing': {
                'strategy': 123  # Wrong type
            },
            'processing': {
                'mode': 'invalid_mode',
                'chunk_size': -100
            },
            'visualization': {
                'plots': 'not_a_list'  # Wrong type
            }
        }
        
        result = validator.validate_workflow_config(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 3
    
    def test_add_custom_validator(self):
        """Test adding a custom validator."""
        validator = ConfigurationValidator()
        custom_validator = TypeValidator(int)
        
        validator.add_validator('custom_domain', 'custom_field', custom_validator)
        
        assert 'custom_domain' in validator._validators
        assert 'custom_field' in validator._validators['custom_domain']
        assert validator._validators['custom_domain']['custom_field'] == custom_validator
    
    def test_remove_validator(self):
        """Test removing a validator."""
        validator = ConfigurationValidator()
        
        # Add a custom validator
        custom_validator = TypeValidator(int)
        validator.add_validator('test_domain', 'test_field', custom_validator)
        
        # Verify it exists
        assert 'test_field' in validator._validators['test_domain']
        
        # Remove it
        validator.remove_validator('test_domain', 'test_field')
        
        # Verify it's gone
        assert 'test_field' not in validator._validators['test_domain']


class TestGlobalValidator:
    """Test global validator functionality."""
    
    def test_get_configuration_validator_singleton(self):
        """Test that get_configuration_validator returns a singleton."""
        validator1 = get_configuration_validator()
        validator2 = get_configuration_validator()
        
        assert validator1 is validator2
    
    def test_validate_config_convenience_function(self):
        """Test the validate_config convenience function."""
        config = {
            'mode': ProcessingMode.SINGLE_FILE.value,
            'group_by': ['group'],
            'aggregation_methods': ['mean']
        }
        
        result = validate_config(config, 'processing')
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validate_config_invalid_domain(self):
        """Test validate_config with invalid domain."""
        config = {'test': 'value'}
        
        with pytest.raises(ValueError, match="Unknown validation domain"):
            validate_config(config, 'invalid_domain')


class TestValidationErrorHandling:
    """Test validation error handling."""
    
    def test_validation_with_missing_required_fields(self):
        """Test validation when required fields are missing."""
        validator = ConfigurationValidator()
        config = {}  # Empty config
        
        result = validator.validate_processing_config(config)
        
        # Should be valid since no required fields are enforced at this level
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validation_with_partial_config(self):
        """Test validation with partial configuration."""
        validator = ConfigurationValidator()
        config = {
            'mode': ProcessingMode.SINGLE_FILE.value,
            # Missing other fields
        }
        
        result = validator.validate_processing_config(config)
        
        # Should be valid since only provided fields are validated
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_validation_with_nested_errors(self):
        """Test validation with nested configuration errors."""
        validator = ConfigurationValidator()
        config = {
            'visualization': {
                'plots': [
                    {
                        'type': 'invalid_type',
                        'width': 100  # Too small
                    },
                    {
                        'type': VisualizationType.BAR_PLOT,
                        'height': 5000  # Too large
                    }
                ]
            }
        }
        
        result = validator.validate_workflow_config(config)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2
        # Check that field names are properly nested
        error_fields = [error.field for error in result.errors]
        assert any('visualization.plots[0]' in field for field in error_fields)
        assert any('visualization.plots[1]' in field for field in error_fields)


class TestBackwardCompatibility:
    """Test backward compatibility with existing validation interfaces."""
    
    def test_validation_result_to_dict_format(self):
        """Test that ValidationResult.to_dict() returns the expected format."""
        result = ValidationResult(is_valid=False)
        result.add_issue("field1", "Error 1", ValidationSeverity.ERROR)
        result.add_issue("field2", "Warning 1", ValidationSeverity.WARNING)
        result.add_issue("field3", "Info 1", ValidationSeverity.INFO)
        
        result_dict = result.to_dict()
        
        # Check expected keys
        assert 'valid' in result_dict
        assert 'errors' in result_dict
        assert 'warnings' in result_dict
        assert 'info' in result_dict
        assert 'validated_config' in result_dict
        
        # Check values
        assert result_dict['valid'] is False
        assert len(result_dict['errors']) == 1
        assert len(result_dict['warnings']) == 1
        assert len(result_dict['info']) == 1
        assert isinstance(result_dict['validated_config'], dict)
    
    def test_validation_with_legacy_config_format(self):
        """Test validation with legacy configuration format."""
        validator = ConfigurationValidator()
        
        # Legacy format that might be used in existing code
        legacy_config = {
            'group_by': ['group', 'time'],
            'aggregation_methods': ['mean'],
            'chunk_size': 1000
        }
        
        result = validator.validate_processing_config(legacy_config)
        
        # Should still work with partial configs
        assert result.is_valid is True
        assert len(result.issues) == 0 