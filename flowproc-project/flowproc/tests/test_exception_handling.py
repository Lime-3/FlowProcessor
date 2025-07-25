#!/usr/bin/env python3
"""
Test script to verify exception handling improvements.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the modules with our improvements
from flowproc.core.exceptions import ProcessingError, DataError as DataProcessingError
from flowproc.domain.parsing import load_and_parse_df
from flowproc.domain.parsing.parsing_utils import validate_parsed_data
from flowproc import DataProcessor
from flowproc import VectorizedAggregator


def test_processing_error_import():
    """Test that ProcessingError can be imported and used."""
    print("🧪 Testing ProcessingError import...")
    try:
        error = ProcessingError("Test error message")
        assert str(error) == "Test error message"
        print("✅ ProcessingError import and usage successful")
        return True
    except Exception as e:
        print(f"❌ ProcessingError test failed: {e}")
        return False


def test_type_validation():
    """Test type validation in DataFrame functions."""
    print("\n🧪 Testing type validation...")
    
    # Test with valid DataFrame (with required columns)
    try:
        df = pd.DataFrame({
            'Well': ['A1', 'A2', 'A3'],
            'Group': [1, 2, 3],
            'Animal': [1, 2, 3],
            'SampleID': ['SP_1.1', 'SP_2.1', 'SP_3.1']
        })
        validate_parsed_data(df, 'SampleID')
        print("✅ Type validation passed with valid DataFrame")
    except Exception as e:
        print(f"❌ Type validation failed with valid DataFrame: {e}")
        return False
    
    # Test with invalid type
    try:
        validate_parsed_data("not a dataframe", 'A')
        print("❌ Type validation should have failed with invalid type")
        return False
    except TypeError as e:
        print(f"✅ Type validation correctly caught TypeError: {e}")
    except Exception as e:
        print(f"❌ Type validation failed with unexpected error: {e}")
        return False
    
    return True


def test_csv_reading_exceptions():
    """Test improved CSV reading exception handling."""
    print("\n🧪 Testing CSV reading exception handling...")
    
    # Test with non-existent file
    try:
        load_and_parse_df(Path("/nonexistent/file.csv"))
        print("❌ Should have raised ProcessingError for non-existent file")
        return False
    except FileNotFoundError as e:
        print(f"✅ Correctly raised FileNotFoundError for non-existent file: {e}")
    except ProcessingError as e:
        print(f"✅ Correctly raised ProcessingError for non-existent file: {e}")
    except Exception as e:
        print(f"❌ Unexpected error for non-existent file: {e}")
        return False
    
    # Test with empty CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("")  # Empty file
        temp_path = Path(f.name)
    
    try:
        result_df, sid_col = load_and_parse_df(temp_path)
        print(f"✅ Empty CSV handled gracefully: {len(result_df)} rows")
    except ProcessingError as e:
        print(f"✅ Empty CSV correctly raised ProcessingError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error for empty CSV: {e}")
        return False
    finally:
        os.unlink(temp_path)
    
    return True


def test_specific_exception_handling():
    """Test specific exception handling in data processing."""
    print("\n🧪 Testing specific exception handling...")
    
    # Test sample ID parsing with invalid input
    from flowproc.domain.parsing import extract_group_animal, extract_tissue

    # Test with None input
    try:
        result = extract_tissue(None)
        assert result == "Unknown"
        print("✅ extract_tissue handled None input correctly")
    except Exception as e:
        print(f"❌ extract_tissue failed with None input: {e}")
        return False
    
    # Test with empty string input
    try:
        result = extract_tissue("")
        assert result == "Unknown"
        print("✅ extract_tissue handled empty string correctly")
    except Exception as e:
        print(f"❌ extract_tissue failed with empty string: {e}")
        return False
    
    # Test with invalid sample ID
    try:
        result = extract_group_animal("invalid_sample_id")
        print(f"Result: {result}")
        assert len(result) == 4
        print("✅ extract_group_animal handled invalid input correctly")
    except Exception as e:
        print(f"❌ extract_group_animal failed with invalid input: {e}")
        return False
    
    return True


def test_vectorized_aggregator_type_validation():
    """Test type validation in VectorizedAggregator."""
    print("\n🧪 Testing VectorizedAggregator type validation...")
    
    # Test with valid DataFrame
    try:
        df = pd.DataFrame({'Group': [1, 2], 'Animal': [1, 2], 'Value': [10, 20]})
        aggregator = VectorizedAggregator(df, 'Group')
        print("✅ VectorizedAggregator created successfully with valid DataFrame")
    except Exception as e:
        print(f"❌ VectorizedAggregator failed with valid DataFrame: {e}")
        return False
    
    # Test optimize_dataframe with invalid type
    try:
        VectorizedAggregator.optimize_dataframe("not a dataframe")
        print("❌ optimize_dataframe should have failed with invalid type")
        return False
    except TypeError as e:
        print(f"✅ optimize_dataframe correctly caught TypeError: {e}")
    except Exception as e:
        print(f"❌ optimize_dataframe failed with unexpected error: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("🚀 Testing Exception Handling Improvements")
    print("=" * 50)
    
    tests = [
        test_processing_error_import,
        test_type_validation,
        test_csv_reading_exceptions,
        test_specific_exception_handling,
        test_vectorized_aggregator_type_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"❌ Test {test.__name__} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Exception handling improvements are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 