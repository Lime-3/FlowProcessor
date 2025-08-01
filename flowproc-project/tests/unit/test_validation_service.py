"""
Unit tests for the consolidated validation service.

These tests verify that the new validation service correctly consolidates
the validation logic from multiple locations and maintains backward compatibility.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from flowproc.domain.parsing.validation_service import (
    validate_parsed_data,
    validate_parsing_output,
    validate_persistence_input,
    validate_with_result,
    ValidationConfig,
    ValidationResult
)


class TestValidationService:
    """Test the consolidated validation service."""
    
    def test_validate_dataframe_structure_valid(self):
        """Test validation with valid DataFrame."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [1, 2],
            'Animal': [1, 2]
        })
        
        # Should not raise any exceptions
        validate_parsed_data(df, 'SampleID')
    
    def test_validate_dataframe_structure_invalid_type(self):
        """Test validation with invalid input type."""
        with pytest.raises(ValueError, match="Expected DataFrame"):
            validate_parsed_data("not a dataframe", 'SampleID')
    
    def test_validate_dataframe_structure_empty(self):
        """Test validation with empty DataFrame."""
        df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="Parsed DataFrame is empty"):
            validate_parsed_data(df, 'SampleID')
    
    def test_validate_required_columns_missing(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [1, 2]
            # Missing 'Animal' column
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_parsed_data(df, 'SampleID')
    
    def test_validate_required_columns_empty(self):
        """Test validation with empty required columns."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [1, 2],
            'Animal': [np.nan, np.nan]  # All NaN values
        })
        
        with pytest.raises(ValueError, match="Required columns are empty"):
            validate_parsed_data(df, 'SampleID')
    
    def test_validate_numeric_values_negative(self):
        """Test validation with negative values."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [-1, 2],
            'Animal': [1, -2]
        })
        
        with pytest.raises(ValueError, match="Invalid group values"):
            validate_parsed_data(df, 'SampleID')
    
    def test_validate_numeric_values_non_numeric(self):
        """Test validation with non-numeric values."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': ['invalid', 2],
            'Animal': [1, 'invalid']
        })
        
        with pytest.raises(ValueError, match="Non-numeric Group values"):
            validate_parsed_data(df, 'SampleID')
    
    def test_validate_time_values_negative(self):
        """Test validation with negative time values."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [1, 2],
            'Animal': [1, 2],
            'Time': [-1.0, 2.0]
        })
        
        with pytest.raises(ValueError, match="Negative time values"):
            validate_parsed_data(df, 'SampleID')
    
    def test_validate_duplicate_samples(self):
        """Test validation with duplicate sample IDs."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [1, 2],
            'Animal': [1, 2],
            'SampleID': ['same_id', 'same_id']
        })
        
        with pytest.raises(ValueError, match="Duplicate sample IDs"):
            validate_parsed_data(df, 'SampleID')
    
    def test_validate_duplicate_samples_with_replicates(self):
        """Test validation with duplicate sample IDs but different replicates."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [1, 2],
            'Animal': [1, 2],
            'SampleID': ['same_id', 'same_id'],
            'Replicate': [1, 2]
        })
        
        # Should pass - duplicates with different replicates are allowed
        validate_parsed_data(df, 'SampleID')
    
    def test_validate_parsing_output_strict(self):
        """Test the strict validation for parsing output."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [1, 2],
            'Animal': [1, 2]
        })
        
        # Should pass with strict settings
        validate_parsing_output(df, 'SampleID')
    
    def test_validate_persistence_input_relaxed(self):
        """Test the relaxed validation for persistence input."""
        df = pd.DataFrame({
            'Group': [1, 2],
            'Animal': [1, 2],
            'SampleID': ['same_id', 'same_id']  # Duplicates allowed
        })
        
        # Should pass with relaxed settings
        validate_persistence_input(df, 'SampleID')
    
    def test_validate_with_result_no_exception(self):
        """Test validation that returns result instead of raising exceptions."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [-1, 2],  # Invalid negative value
            'Animal': [1, 2]
        })
        
        result = validate_with_result(df, 'SampleID')
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "Invalid group values" in result.errors[0]
    
    def test_validation_config_customization(self):
        """Test validation with custom configuration."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [-1, 2],  # Negative values
            'Animal': [1, 2]
        })
        
        # Custom config that allows negative values
        config = ValidationConfig(
            allow_negative_values=True,
            raise_on_error=False
        )
        
        result = validate_parsed_data(df, 'SampleID', config)
        assert result.is_valid
    
    def test_validation_config_required_columns(self):
        """Test validation with custom required columns."""
        df = pd.DataFrame({
            'Group': [1, 2],
            'Animal': [1, 2]
            # Missing 'Well' column
        })
        
        # Custom config that doesn't require 'Well' column
        config = ValidationConfig(
            required_columns=['Group', 'Animal'],
            raise_on_error=False
        )
        
        result = validate_parsed_data(df, 'SampleID', config)
        assert result.is_valid
    
    def test_validation_result_methods(self):
        """Test ValidationResult methods."""
        result = ValidationResult(is_valid=True)
        
        # Test adding error
        result.add_error("Test error")
        assert not result.is_valid
        assert "Test error" in result.errors
        
        # Test adding warning
        result.add_warning("Test warning")
        assert "Test warning" in result.warnings
        
        # Test boolean conversion
        assert not bool(result)
        
        # Test valid result
        valid_result = ValidationResult(is_valid=True)
        assert bool(valid_result)


class TestBackwardCompatibility:
    """Test that the new validation service maintains backward compatibility."""
    
    def test_parsing_utils_compatibility(self):
        """Test that the new service matches the original parsing_utils behavior."""
        # Test case that would have passed in original parsing_utils
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': [1, 2],
            'Animal': [1, 2],
            'Time': [1.0, 2.0]
        })
        
        # Should pass with same behavior as original
        validate_parsing_output(df, 'SampleID')
    
    def test_data_io_compatibility(self):
        """Test that the new service matches the original data_io behavior."""
        # Test case that would have passed in original data_io
        df = pd.DataFrame({
            'Group': [1, 2],
            'Animal': [1, 2]
        })
        
        # Should pass with same behavior as original
        validate_persistence_input(df, 'SampleID')
    
    def test_error_messages_consistent(self):
        """Test that error messages are consistent with original implementations."""
        df = pd.DataFrame({
            'Well': ['A1', 'A2'],
            'Group': ['invalid', 2],
            'Animal': [1, 2]
        })
        
        with pytest.raises(ValueError, match="Non-numeric Group values"):
            validate_parsing_output(df, 'SampleID')


class TestValidationConfig:
    """Test ValidationConfig functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ValidationConfig()
        
        assert config.required_columns == ['Well', 'Group', 'Animal']
        assert not config.allow_empty_dataframe
        assert not config.allow_negative_values
        assert not config.allow_duplicate_samples
        assert config.allow_duplicates_with_different_replicates
        assert config.raise_on_error
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ValidationConfig(
            required_columns=['Group', 'Animal'],
            allow_negative_values=True,
            allow_duplicate_samples=True,
            raise_on_error=False
        )
        
        assert config.required_columns == ['Group', 'Animal']
        assert config.allow_negative_values
        assert config.allow_duplicate_samples
        assert not config.raise_on_error 