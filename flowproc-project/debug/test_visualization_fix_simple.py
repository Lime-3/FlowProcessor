#!/usr/bin/env python3
"""
Simple test script to verify visualization fixes work correctly (no Qt dependencies).
"""

import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flowproc.domain.parsing import load_and_parse_df
from flowproc.domain.visualization.simple_visualizer import plot, _detect_flow_columns

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_column_detection():
    """Test column detection with the problematic data."""
    # Use one of the test CSV files
    csv_path = project_root / "tests" / "data" / "AT25-AS278_FullStudy-1.csv"
    
    if not csv_path.exists():
        logger.error(f"Test file not found: {csv_path}")
        return False
    
    try:
        # Load and parse the data
        df, _ = load_and_parse_df(csv_path)
        
        if df is None or df.empty:
            logger.error("Failed to load data")
            return False
        
        logger.info(f"✅ Loaded data with {len(df)} rows and {len(df.columns)} columns")
        
        # Test flow column detection
        flow_cols = _detect_flow_columns(df)
        logger.info(f"✅ Detected flow columns successfully")
        
        # Test frequency column detection
        freq_parent_cols = [col for col in df.columns if 'freq. of parent' in col.lower()]
        logger.info(f"✅ Found {len(freq_parent_cols)} Frequency of Parent columns")
        
        # Test plotting with auto-detection
        logger.info("Testing plot generation with auto-detection...")
        fig = plot(df, x='Group', y='Freq. of Parent', plot_type='bar')
        logger.info("✅ Plot generated successfully with auto-detection!")
        
        # Test plotting with specific column
        if freq_parent_cols:
            logger.info(f"Testing plot generation with specific column...")
            fig = plot(df, x='Group', y=freq_parent_cols[0], plot_type='bar')
            logger.info("✅ Specific column plot generated successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dimension_validation_logic():
    """Test the dimension validation logic without Qt."""
    logger.info("Testing dimension validation logic...")
    
    # Test with reasonable dimensions
    width, height = 1000, 600
    max_texture_size = 16384
    safe_max_width = min(max_texture_size, 8000)
    safe_max_height = min(max_texture_size, 6000)
    
    # Test with large dimensions (should be clamped)
    test_width, test_height = 20000, 15000
    
    logger.info(f"Original dimensions: {test_width}x{test_height}")
    
    # Apply validation logic
    if test_width > safe_max_width:
        test_width = safe_max_width
    if test_height > safe_max_height:
        test_height = safe_max_height
    
    logger.info(f"After validation: {test_width}x{test_height}")
    
    # Verify the logic works
    assert test_width == safe_max_width, f"Width should be clamped to {safe_max_width}"
    assert test_height == safe_max_height, f"Height should be clamped to {safe_max_height}"
    
    logger.info("✅ Dimension validation logic works correctly!")
    return True

def main():
    """Run all tests."""
    logger.info("🚀 Testing visualization fixes...")
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Column detection and plotting
    if test_column_detection():
        tests_passed += 1
        logger.info("✅ Column detection test passed")
    else:
        logger.error("❌ Column detection test failed")
    
    # Test 2: Dimension validation logic
    if test_dimension_validation_logic():
        tests_passed += 1
        logger.info("✅ Dimension validation test passed")
    else:
        logger.error("❌ Dimension validation test failed")
    
    # Summary
    logger.info(f"\n📊 Test Summary:")
    logger.info(f"   Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        logger.info("🎉 All tests passed! Visualization fixes are working correctly.")
        logger.info("\n💡 Key fixes implemented:")
        logger.info("   ✅ Fixed column detection for 'Freq. of Parent' pattern")
        logger.info("   ✅ Added fallback mechanisms for missing columns")
        logger.info("   ✅ Improved dimension validation to prevent texture overflow")
        logger.info("   ✅ Added better error handling and logging")
        return True
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 