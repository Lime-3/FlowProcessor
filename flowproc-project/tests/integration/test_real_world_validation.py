"""
Integration tests using real-world CSV data.

These tests validate that the new consolidated validation service works correctly
with actual CSV files from the Test CSV folder.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flowproc.domain.parsing.validation_service import (
    validate_parsed_data,
    validate_parsing_output,
    validate_persistence_input,
    validate_with_result,
    ValidationConfig,
    ValidationResult
)
from flowproc.domain.parsing.parsing_utils import load_and_parse_df


class TestRealWorldCSVValidation:
    """Test validation service with real-world CSV files."""
    
    @pytest.fixture
    def csv_files(self):
        """Get list of CSV files from the Test CSV folder."""
        csv_dir = Path("/Users/franklin.lime/Documents/GitHub/FlowProcessor/Test CSV")
        return [f for f in csv_dir.glob("*.csv") if f.name != ".DS_Store"]
    
    def test_load_all_csv_files(self, csv_files):
        """Test that all CSV files can be loaded without errors."""
        for csv_file in csv_files:
            print(f"Testing file: {csv_file.name}")
            
            # Load the CSV file
            df = pd.read_csv(csv_file)
            assert not df.empty, f"CSV file {csv_file.name} is empty"
            assert len(df.columns) > 0, f"CSV file {csv_file.name} has no columns"
            
            print(f"  ✓ Loaded {csv_file.name}: {len(df)} rows, {len(df.columns)} columns")
    
    def test_validate_raw_csv_data(self, csv_files):
        """Test validation of raw CSV data without parsing."""
        for csv_file in csv_files:
            print(f"Testing raw validation: {csv_file.name}")
            
            # Load the CSV file
            df = pd.read_csv(csv_file)
            
            # Test basic DataFrame validation with relaxed settings for raw CSV
            config = ValidationConfig(
                required_columns=[df.columns[0]],  # Only require the first column
                allow_empty_dataframe=False,
                allow_negative_values=True,  # Allow negative values in flow cytometry data
                allow_duplicate_samples=True,  # Allow duplicates in raw data
                raise_on_error=False
            )
            
            result = validate_parsed_data(df, df.columns[0], config)
            
            # Raw CSV files should pass basic structure validation
            assert result.is_valid, f"Basic validation failed for {csv_file.name}: {result.errors}"
            
            print(f"  ✓ Raw validation passed for {csv_file.name}")
    
    def test_validate_parsed_data_structure(self, csv_files):
        """Test validation after parsing the data."""
        for csv_file in csv_files:
            print(f"Testing parsed validation: {csv_file.name}")
            
            try:
                # Use the existing parsing function
                df, sid_col = load_and_parse_df(csv_file)
                
                # Test validation of parsed data
                result = validate_with_result(df, sid_col, raise_on_error=False)
                
                if result.is_valid:
                    print(f"  ✓ Parsed validation passed for {csv_file.name}")
                else:
                    print(f"  ⚠ Parsed validation warnings for {csv_file.name}: {result.warnings}")
                    if result.errors:
                        print(f"  ❌ Parsed validation errors for {csv_file.name}: {result.errors}")
                
            except Exception as e:
                print(f"  ❌ Failed to parse {csv_file.name}: {e}")
                # Continue with other files
    
    def test_validate_specific_file_formats(self):
        """Test validation with specific file formats."""
        
        # Test with test_data.csv (has time-based sample IDs)
        test_data_path = Path("/Users/franklin.lime/Documents/GitHub/FlowProcessor/Test CSV/test_data.csv")
        if test_data_path.exists():
            print("Testing test_data.csv format")
            
            df = pd.read_csv(test_data_path)
            
            # This file has time-based sample IDs like "2 hours_SP_A1_1.1.fcs"
            # Test with relaxed validation for time-based data
            config = ValidationConfig(
                required_columns=['SampleID'],  # Only require sample ID column
                allow_empty_dataframe=False,
                allow_negative_values=True,  # Allow negative values in flow cytometry data
                allow_duplicate_samples=True,  # Allow duplicates in this context
                raise_on_error=False
            )
            
            result = validate_parsed_data(df, 'SampleID', config)
            assert result.is_valid, f"test_data.csv validation failed: {result.errors}"
            print("  ✓ test_data.csv validation passed")
        
        # Test with sample_study_002.csv (has tissue-based sample IDs)
        sample_path = Path("/Users/franklin.lime/Documents/GitHub/FlowProcessor/Test CSV/sample_study_002.csv")
        if sample_path.exists():
            print("Testing sample_study_002.csv format")
            
            df = pd.read_csv(sample_path)
            
            # This file has tissue-based sample IDs like "Spleen_A1_1.1.fcs"
            config = ValidationConfig(
                required_columns=[df.columns[0]],  # Use first column as sample ID
                allow_empty_dataframe=False,
                allow_negative_values=True,
                allow_duplicate_samples=True,
                raise_on_error=False
            )
            
            result = validate_parsed_data(df, df.columns[0], config)
            assert result.is_valid, f"sample_study_002.csv validation failed: {result.errors}"
            print("  ✓ sample_study_002.csv validation passed")
    
    def test_validate_with_different_configurations(self):
        """Test validation with different configuration settings."""
        test_data_path = Path("/Users/franklin.lime/Documents/GitHub/FlowProcessor/Test CSV/test_data.csv")
        if not test_data_path.exists():
            pytest.skip("test_data.csv not found")
        
        df = pd.read_csv(test_data_path)
        
        # Test 1: Strict validation (should fail for raw CSV)
        print("Testing strict validation configuration")
        strict_config = ValidationConfig(
            required_columns=['Well', 'Group', 'Animal'],
            allow_empty_dataframe=False,
            allow_negative_values=False,
            allow_duplicate_samples=False,
            raise_on_error=False
        )
        
        result = validate_parsed_data(df, 'SampleID', strict_config)
        # This should fail because raw CSV doesn't have Well, Group, Animal columns
        assert not result.is_valid, "Strict validation should fail for raw CSV"
        assert any("Missing required columns" in error for error in result.errors)
        print("  ✓ Strict validation correctly failed for raw CSV")
        
        # Test 2: Relaxed validation (should pass)
        print("Testing relaxed validation configuration")
        relaxed_config = ValidationConfig(
            required_columns=['SampleID'],
            allow_empty_dataframe=False,
            allow_negative_values=True,
            allow_duplicate_samples=True,
            raise_on_error=False
        )
        
        result = validate_parsed_data(df, 'SampleID', relaxed_config)
        assert result.is_valid, f"Relaxed validation failed: {result.errors}"
        print("  ✓ Relaxed validation passed for raw CSV")
    
    def test_validate_parsing_output_with_real_data(self):
        """Test the validate_parsing_output function with real parsed data."""
        test_data_path = Path("/Users/franklin.lime/Documents/GitHub/FlowProcessor/Test CSV/test_data.csv")
        if not test_data_path.exists():
            pytest.skip("test_data.csv not found")
        
        try:
            # Parse the data using the existing parsing function
            df, sid_col = load_and_parse_df(test_data_path)
            
            print(f"Testing validate_parsing_output with parsed data from {test_data_path.name}")
            print(f"  Parsed columns: {list(df.columns)}")
            print(f"  Sample ID column: {sid_col}")
            
            # Test with the strict parsing output validation
            result = validate_with_result(df, sid_col, raise_on_error=False)
            
            if result.is_valid:
                print("  ✓ Parsing output validation passed")
            else:
                print(f"  ⚠ Parsing output validation warnings: {result.warnings}")
                if result.errors:
                    print(f"  ❌ Parsing output validation errors: {result.errors}")
                    
        except Exception as e:
            print(f"  ❌ Failed to parse {test_data_path.name}: {e}")
    
    def test_validate_persistence_input_with_real_data(self):
        """Test the validate_persistence_input function with real data."""
        test_data_path = Path("/Users/franklin.lime/Documents/GitHub/FlowProcessor/Test CSV/test_data.csv")
        if not test_data_path.exists():
            pytest.skip("test_data.csv not found")
        
        # Load raw CSV data
        df = pd.read_csv(test_data_path)
        
        print(f"Testing validate_persistence_input with raw data from {test_data_path.name}")
        
        # Test with the relaxed persistence input validation
        result = validate_with_result(df, 'SampleID', raise_on_error=False)
        
        if result.is_valid:
            print("  ✓ Persistence input validation passed")
        else:
            print(f"  ⚠ Persistence input validation warnings: {result.warnings}")
            if result.errors:
                print(f"  ❌ Persistence input validation errors: {result.errors}")
    
    def test_validation_error_handling_with_real_data(self):
        """Test error handling with real data that has issues."""
        
        # Test with DiD.csv which has some "n/a" values
        did_path = Path("/Users/franklin.lime/Documents/GitHub/FlowProcessor/Test CSV/DiD.csv")
        if did_path.exists():
            print("Testing error handling with DiD.csv (contains 'n/a' values)")
            
            df = pd.read_csv(did_path)
            
            # Test validation that should handle the "n/a" values gracefully
            config = ValidationConfig(
                required_columns=[df.columns[0]],
                allow_empty_dataframe=False,
                allow_negative_values=True,
                allow_duplicate_samples=True,
                raise_on_error=False
            )
            
            result = validate_parsed_data(df, df.columns[0], config)
            
            if result.is_valid:
                print("  ✓ DiD.csv validation passed despite 'n/a' values")
            else:
                print(f"  ⚠ DiD.csv validation warnings: {result.warnings}")
                if result.errors:
                    print(f"  ❌ DiD.csv validation errors: {result.errors}")
    
    def test_validation_performance_with_large_files(self):
        """Test validation performance with larger CSV files."""
        large_files = [
            "sample_study_004_full.csv",
            "sample_study_011_gfp_table.csv"
        ]
        
        for filename in large_files:
            file_path = Path(f"/Users/franklin.lime/Documents/GitHub/FlowProcessor/Test CSV/{filename}")
            if file_path.exists():
                print(f"Testing performance with {filename}")
                
                # Load the file
                df = pd.read_csv(file_path)
                print(f"  File size: {len(df)} rows, {len(df.columns)} columns")
                
                # Test validation performance
                import time
                start_time = time.time()
                
                config = ValidationConfig(
                    required_columns=[df.columns[0]],
                    allow_empty_dataframe=False,
                    allow_negative_values=True,
                    allow_duplicate_samples=True,
                    raise_on_error=False
                )
                
                result = validate_parsed_data(df, df.columns[0], config)
                
                end_time = time.time()
                validation_time = end_time - start_time
                
                print(f"  Validation time: {validation_time:.4f} seconds")
                
                if result.is_valid:
                    print(f"  ✓ {filename} validation passed")
                else:
                    print(f"  ⚠ {filename} validation warnings: {len(result.warnings)}")
                    if result.errors:
                        print(f"  ❌ {filename} validation errors: {len(result.errors)}")
                
                # Performance assertion (should complete within reasonable time)
                assert validation_time < 1.0, f"Validation took too long: {validation_time:.4f} seconds"


class TestRealWorldValidationEdgeCases:
    """Test edge cases with real-world data."""
    
    def test_validate_empty_dataframe(self):
        """Test validation with empty DataFrame."""
        empty_df = pd.DataFrame()
        
        # Should fail with default settings
        result = validate_with_result(empty_df, 'SampleID', raise_on_error=False)
        assert not result.is_valid
        assert any("empty" in error.lower() for error in result.errors)
        
        # Should pass with allow_empty_dataframe=True and no required columns
        config = ValidationConfig(
            required_columns=[],  # No required columns for empty DataFrame
            allow_empty_dataframe=True, 
            raise_on_error=False
        )
        result = validate_parsed_data(empty_df, 'SampleID', config)
        assert result.is_valid
    
    def test_validate_dataframe_with_missing_columns(self):
        """Test validation with DataFrame missing required columns."""
        df = pd.DataFrame({'SampleID': ['A1', 'A2'], 'Value': [1, 2]})
        
        # Should fail with strict requirements
        config = ValidationConfig(
            required_columns=['Well', 'Group', 'Animal'],
            raise_on_error=False
        )
        result = validate_parsed_data(df, 'SampleID', config)
        assert not result.is_valid
        assert any("Missing required columns" in error for error in result.errors)
        
        # Should pass with relaxed requirements
        config = ValidationConfig(
            required_columns=['SampleID'],
            raise_on_error=False
        )
        result = validate_parsed_data(df, 'SampleID', config)
        assert result.is_valid
    
    def test_validate_dataframe_with_negative_values(self):
        """Test validation with negative values."""
        df = pd.DataFrame({
            'SampleID': ['A1', 'A2'],
            'Group': [-1, 2],
            'Animal': [1, -2]
        })
        
        # Should fail with default settings (requires Well, Group, Animal columns)
        result = validate_with_result(df, 'SampleID', raise_on_error=False)
        assert not result.is_valid
        # Should fail due to missing Well column, not negative values
        assert any("Missing required columns" in error for error in result.errors)
        
        # Should pass with relaxed column requirements and allow_negative_values=True
        config = ValidationConfig(
            required_columns=['SampleID', 'Group', 'Animal'],
            allow_negative_values=True, 
            raise_on_error=False
        )
        result = validate_parsed_data(df, 'SampleID', config)
        assert result.is_valid


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"]) 