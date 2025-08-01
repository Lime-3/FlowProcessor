#!/usr/bin/env python3
"""
Diagnostic script to identify visualization loading issues.
"""

import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.parsing import load_and_parse_df
from flowproc.domain.visualization.data_processor import detect_data_characteristics
from flowproc.core.constants import KEYWORDS

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data_loading(csv_path: Path) -> bool:
    """Test if data loading works without hanging."""
    print(f"🔍 Testing data loading for: {csv_path}")
    
    try:
        start_time = time.time()
        df, sid_col = load_and_parse_df(csv_path)
        load_time = time.time() - start_time
        
        print(f"✅ Data loading completed in {load_time:.2f} seconds")
        print(f"   Sample ID column: {sid_col}")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        logger.error("Data loading error", exc_info=True)
        return False

def test_data_analysis(df, sid_col: str) -> bool:
    """Test if data analysis works without hanging."""
    print(f"\n🔍 Testing data analysis...")
    
    try:
        start_time = time.time()
        characteristics = detect_data_characteristics(df)
        analysis_time = time.time() - start_time
        
        print(f"✅ Data analysis completed in {analysis_time:.2f} seconds")
        print(f"   Has time data: {characteristics['has_time_data']}")
        print(f"   Has tissue data: {characteristics['has_tissue_data']}")
        print(f"   Number of groups: {characteristics['num_groups']}")
        print(f"   Number of tissues: {characteristics['num_tissues']}")
        print(f"   Time points: {characteristics['time_points']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data analysis failed: {e}")
        logger.error("Data analysis error", exc_info=True)
        return False

def test_metric_detection(df, sid_col: str) -> bool:
    """Test if metric detection works without hanging."""
    print(f"\n🔍 Testing metric detection...")
    
    try:
        start_time = time.time()
        
        # Get available metrics
        available_metrics = []
        for metric in KEYWORDS.keys():
            key_substring = KEYWORDS.get(metric, metric.lower())
            matching_cols = [
                col for col in df.columns
                if key_substring in col.lower()
                and col not in {sid_col, 'Well', 'Group', 'Animal', 
                              'Time', 'Replicate', 'Tissue'}
                and not df[col].isna().all()
            ]
            if matching_cols:
                available_metrics.append(metric)
        
        detection_time = time.time() - start_time
        
        print(f"✅ Metric detection completed in {detection_time:.2f} seconds")
        print(f"   Available metrics: {available_metrics}")
        
        return True
        
    except Exception as e:
        print(f"❌ Metric detection failed: {e}")
        logger.error("Metric detection error", exc_info=True)
        return False

def test_visualization_creation(csv_path: Path) -> bool:
    """Test if visualization creation works without hanging."""
    print(f"\n🔍 Testing visualization creation...")
    
    try:
        from flowproc.domain.visualization.facade import create_visualization
        import tempfile
        
        start_time = time.time()
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            output_html = Path(tmp_file.name)
        
        # Create visualization
        fig = create_visualization(
            data_source=csv_path,
            metric="Freq. of Parent",
            output_html=output_html,
            time_course_mode=False,
            theme="default",
            width=600,
            height=400
        )
        
        creation_time = time.time() - start_time
        
        print(f"✅ Visualization creation completed in {creation_time:.2f} seconds")
        print(f"   Output file: {output_html}")
        print(f"   File exists: {output_html.exists()}")
        
        # Clean up
        if output_html.exists():
            output_html.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Visualization creation failed: {e}")
        logger.error("Visualization creation error", exc_info=True)
        return False

def main():
    """Run the diagnostic tests."""
    print("🚀 Starting visualization diagnostic...")
    
    # Find a test CSV file
    test_csv_dir = Path("../Test CSV")
    if not test_csv_dir.exists():
        test_csv_dir = Path("../../Test CSV")
    
    if not test_csv_dir.exists():
        print("❌ Could not find Test CSV directory")
        return
    
    # Find the first CSV file
    csv_files = list(test_csv_dir.glob("*.csv"))
    if not csv_files:
        print("❌ No CSV files found in Test CSV directory")
        return
    
    csv_path = csv_files[0]
    print(f"📁 Using test file: {csv_path}")
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Data loading
    if test_data_loading(csv_path):
        tests_passed += 1
        
        # Test 2: Data analysis (only if loading succeeded)
        df, sid_col = load_and_parse_df(csv_path)
        if test_data_analysis(df, sid_col):
            tests_passed += 1
            
            # Test 3: Metric detection (only if analysis succeeded)
            if test_metric_detection(df, sid_col):
                tests_passed += 1
    
    # Test 4: Visualization creation
    if test_visualization_creation(csv_path):
        tests_passed += 1
    
    # Summary
    print(f"\n📊 Diagnostic Summary:")
    print(f"   Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! The visualization should work.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        
        if tests_passed == 0:
            print("\n💡 Suggestions:")
            print("   - Check if the CSV file is corrupted or very large")
            print("   - Verify that the CSV file has the expected format")
            print("   - Check if there are any permission issues")
        elif tests_passed < 3:
            print("\n💡 The issue might be in the data analysis or metric detection phase.")
        else:
            print("\n💡 The issue might be in the visualization creation phase.")

if __name__ == "__main__":
    main() 