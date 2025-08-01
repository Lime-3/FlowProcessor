"""
Unit tests for the unified input validation service.

These tests verify that the new unified input validation service correctly consolidates
all validation logic from the GUI layer and provides consistent validation behavior.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from flowproc.domain.validation import (
    InputValidator,
    InputValidationResult,
    InputValidationConfig,
    validate_input_paths,
    validate_output_directory,
    validate_processing_options,
    validate_gui_inputs
)


class TestInputValidationService:
    """Test the unified input validation service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_file = Path(self.temp_dir) / "test.csv"
        self.test_csv_file.write_text("Well,Group,Animal\nA1,1,1\nA2,1,2")
        
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_input_paths_valid_files(self):
        """Test validation with valid input files."""
        result = validate_input_paths([str(self.test_csv_file)])
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.file_count == 1
        assert result.total_size > 0
        assert str(self.test_csv_file) in result.valid_paths
    
    def test_validate_input_paths_empty_list(self):
        """Test validation with empty input paths."""
        result = validate_input_paths([])
        
        assert not result.is_valid
        assert "No input files or directories specified" in result.errors[0]
    
    def test_validate_input_paths_nonexistent_file(self):
        """Test validation with nonexistent file."""
        result = validate_input_paths(["/nonexistent/file.csv"])
        
        assert not result.is_valid
        assert "Path does not exist" in result.errors[0]
    
    def test_validate_input_paths_invalid_extension(self):
        """Test validation with invalid file extension."""
        invalid_file = Path(self.temp_dir) / "test.txt"
        invalid_file.write_text("test")
        
        result = validate_input_paths([str(invalid_file)])
        
        assert not result.is_valid
        assert "Unsupported file format" in result.errors[0]
    
    def test_validate_input_paths_directory(self):
        """Test validation with directory containing CSV files."""
        csv_dir = Path(self.temp_dir) / "csv_dir"
        csv_dir.mkdir()
        csv_file = csv_dir / "test.csv"
        csv_file.write_text("Well,Group,Animal\nA1,1,1")
        
        result = validate_input_paths([str(csv_dir)])
        
        assert result.is_valid
        assert result.file_count == 1
        assert str(csv_file) in result.valid_paths
    
    def test_validate_input_paths_empty_directory(self):
        """Test validation with empty directory."""
        empty_dir = Path(self.temp_dir) / "empty_dir"
        empty_dir.mkdir()
        
        result = validate_input_paths([str(empty_dir)])
        
        assert not result.is_valid
        assert "No valid files found in directory" in result.errors[0]
    
    def test_validate_output_directory_valid(self):
        """Test validation with valid output directory."""
        result = validate_output_directory(self.temp_dir)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_output_directory_empty_path(self):
        """Test validation with empty output directory path."""
        result = validate_output_directory("")
        
        assert not result.is_valid
        assert "Output directory path is empty" in result.errors[0]
    
    def test_validate_output_directory_nonexistent(self):
        """Test validation with nonexistent output directory."""
        nonexistent_dir = Path(self.temp_dir) / "new_dir"
        
        result = validate_output_directory(str(nonexistent_dir))
        
        assert result.is_valid  # Should create the directory
        assert nonexistent_dir.exists()
    
    def test_validate_output_directory_file_exists(self):
        """Test validation when a file exists at the output path."""
        file_path = Path(self.temp_dir) / "output_file"
        file_path.write_text("test")
        
        result = validate_output_directory(str(file_path))
        
        assert not result.is_valid
        assert "Output path exists but is not a directory" in result.errors[0]
    
    @patch('shutil.disk_usage')
    def test_validate_output_directory_low_disk_space(self, mock_disk_usage):
        """Test validation with low disk space."""
        mock_disk_usage.return_value = (1000000, 900000, 50000000)  # 50MB free
        
        config = InputValidationConfig(min_disk_space_mb=100)
        result = validate_output_directory(self.temp_dir, config)
        
        assert result.is_valid
        assert len(result.warnings) > 0
        assert "Low disk space available" in result.warnings[0]
    
    def test_validate_processing_options_valid(self):
        """Test validation with valid processing options."""
        result = validate_processing_options(
            groups=[1, 2, 3],
            replicates=[1, 2],
            time_course_mode=False
        )
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_processing_options_invalid_groups_type(self):
        """Test validation with invalid groups type."""
        result = validate_processing_options(groups="not a list")
        
        assert not result.is_valid
        assert "Groups must be a list" in result.errors[0]
    
    def test_validate_processing_options_invalid_group_values(self):
        """Test validation with invalid group values."""
        result = validate_processing_options(groups=[1, -1, 0])
        
        assert not result.is_valid
        assert "All group numbers must be positive integers" in result.errors[0]
    
    def test_validate_processing_options_empty_groups(self):
        """Test validation with empty groups list."""
        result = validate_processing_options(groups=[])
        
        assert not result.is_valid
        assert "Groups list cannot be empty" in result.errors[0]
    
    def test_validate_processing_options_time_course_missing_groups(self):
        """Test validation for time course mode with missing groups."""
        config = InputValidationConfig(require_groups_for_time_course=True)
        result = validate_processing_options(
            time_course_mode=True,
            config=config
        )
        
        assert not result.is_valid
        assert "Time course mode requires groups to be specified" in result.errors[0]
    
    def test_validate_processing_options_time_course_missing_replicates(self):
        """Test validation for time course mode with missing replicates."""
        config = InputValidationConfig(require_replicates_for_time_course=True)
        result = validate_processing_options(
            time_course_mode=True,
            config=config
        )
        
        assert not result.is_valid
        # Check that the error is in the errors list (not necessarily first)
        assert any("Time course mode requires replicates to be specified" in error for error in result.errors)
    
    def test_validate_gui_inputs_comprehensive(self):
        """Test comprehensive GUI input validation."""
        result = validate_gui_inputs(
            input_paths=[str(self.test_csv_file)],
            output_dir=self.temp_dir,
            groups=[1, 2],
            replicates=[1],
            time_course_mode=False
        )
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.file_count == 1
        assert result.total_size > 0
    
    def test_validate_gui_inputs_with_warnings(self):
        """Test GUI input validation that generates warnings."""
        # Create a large file to trigger size warning
        large_file = Path(self.temp_dir) / "large.csv"
        large_content = "Well,Group,Animal\n" + "\n".join([f"A{i},1,{i}" for i in range(10000)])
        large_file.write_text(large_content)
        
        config = InputValidationConfig(max_file_size_mb=0.1)  # 100KB limit
        result = validate_gui_inputs(
            input_paths=[str(large_file)],
            output_dir=self.temp_dir,
            config=config
        )
        
        assert result.is_valid
        assert len(result.warnings) > 0
        assert "Large file detected" in result.warnings[0]
    
    def test_input_validator_class(self):
        """Test the InputValidator class."""
        validator = InputValidator()
        
        result = validator.validate_gui_inputs(
            input_paths=[str(self.test_csv_file)],
            output_dir=self.temp_dir
        )
        
        assert result.is_valid
        assert result.file_count == 1
    
    def test_input_validator_with_custom_config(self):
        """Test InputValidator with custom configuration."""
        config = InputValidationConfig(
            allowed_extensions=['.csv', '.txt'],
            max_file_size_mb=1
        )
        validator = InputValidator(config)
        
        # Create a text file
        text_file = Path(self.temp_dir) / "test.txt"
        text_file.write_text("test")
        
        result = validator.validate_gui_inputs(
            input_paths=[str(text_file)],
            output_dir=self.temp_dir
        )
        
        assert result.is_valid
        assert result.file_count == 1
    
    def test_validation_result_methods(self):
        """Test ValidationResult methods."""
        result = InputValidationResult(is_valid=True)
        
        result.add_error("Test error")
        assert not result.is_valid
        assert "Test error" in result.errors
        
        result.add_warning("Test warning")
        assert "Test warning" in result.warnings
        
        assert bool(result) == result.is_valid
    
    def test_backward_compatibility_gui_validator(self):
        """Test backward compatibility with GUI validator interface."""
        from flowproc.presentation.gui.views.components.gui_validator import validate_inputs
        
        is_valid, errors = validate_inputs(
            input_paths=[str(self.test_csv_file)],
            output_dir=self.temp_dir,
            groups=[1, 2],
            replicates=[1]
        )
        
        assert is_valid
        assert len(errors) == 0
    
    def test_backward_compatibility_validation_mixin(self):
        """Test backward compatibility with validation mixin interface."""
        from flowproc.presentation.gui.views.mixins.validation_mixin import ValidationMixin
        
        mixin = ValidationMixin()
        is_valid, errors = mixin.validate_inputs(
            input_paths=[str(self.test_csv_file)],
            output_dir=self.temp_dir
        )
        
        assert is_valid
        assert len(errors) == 0
    
    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with patch('pathlib.Path.stat', side_effect=PermissionError("Permission denied")):
                    result = validate_input_paths(["/protected/file.csv"])
                    
                    assert not result.is_valid
                    assert "Permission denied" in result.errors[0]
    
    def test_large_dataset_warning(self):
        """Test warning for large datasets."""
        # Create multiple files to trigger dataset size warning
        files = []
        for i in range(100):
            file_path = Path(self.temp_dir) / f"file_{i}.csv"
            file_path.write_text("Well,Group,Animal\nA1,1,1")
            files.append(str(file_path))
        
        result = validate_input_paths(files)
        
        assert result.is_valid
        assert len(result.warnings) > 0
        assert "Many input files detected" in result.warnings[0] 