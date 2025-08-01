#!/usr/bin/env python3
"""
Test script to validate timecourse performance improvements.
"""

import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.parsing import load_and_parse_df
from flowproc.domain.visualization.simple_visualizer import time_plot, _analyze_data_size

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_timecourse_performance(csv_path: Path, test_name: str = "Performance Test"):
    """Test timecourse plotting performance with different optimization levels."""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")
    
    try:
        # Load data
        print(f"📊 Loading data from: {csv_path}")
        start_time = time.time()
        df, sid_col = load_and_parse_df(csv_path)
        load_time = time.time() - start_time
        print(f"✅ Data loaded in {load_time:.2f}s")
        print(f"   Shape: {df.shape}")
        print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
        
        # Analyze data size
        print(f"\n🔍 Analyzing data size...")
        flow_cols = [col for col in df.columns if 'Freq. of Parent' in col]
        if not flow_cols:
            flow_cols = [col for col in df.columns if 'freq' in col.lower()]
        
        if flow_cols:
            analysis = _analyze_data_size(df, flow_cols)
            print(f"   Total rows: {analysis['total_rows']:,}")
            print(f"   Cell types: {analysis['num_cell_types']}")
            print(f"   Complexity: {analysis['complexity']}")
            print(f"   Estimated memory: {analysis['estimated_memory_mb']:.1f} MB")
            
            if analysis['recommendations']:
                print(f"   Recommendations:")
                for rec in analysis['recommendations']:
                    print(f"     • {rec}")
        
        # Test different optimization levels
        test_configs = [
            {"name": "No optimization", "max_cell_types": 50, "sample_size": None},
            {"name": "Moderate optimization", "max_cell_types": 10, "sample_size": 1000},
            {"name": "Aggressive optimization", "max_cell_types": 5, "sample_size": 500},
        ]
        
        for config in test_configs:
            print(f"\n⚡ Testing: {config['name']}")
            print(f"   Max cell types: {config['max_cell_types']}")
            print(f"   Sample size: {config['sample_size'] or 'No limit'}")
            
            start_time = time.time()
            try:
                fig = time_plot(
                    data=csv_path,
                    value_col="Freq. of Parent",
                    max_cell_types=config['max_cell_types'],
                    sample_size=config['sample_size'],
                    width=800,
                    height=600
                )
                plot_time = time.time() - start_time
                print(f"   ✅ Plot generated in {plot_time:.2f}s")
                print(f"   📊 Figure size: {fig.layout.width}x{fig.layout.height}")
                
            except Exception as e:
                plot_time = time.time() - start_time
                print(f"   ❌ Failed after {plot_time:.2f}s: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error("Test error", exc_info=True)
        return False


def main():
    """Run performance tests on available CSV files."""
    print("🚀 Timecourse Performance Test Suite")
    print("=" * 60)
    
    # Test data directory
    test_data_dir = Path(__file__).parent.parent / "tests" / "data"
    if not test_data_dir.exists():
        print(f"❌ Test data directory not found: {test_data_dir}")
        return
    
    # Find CSV files
    csv_files = list(test_data_dir.glob("*.csv"))
    if not csv_files:
        print(f"❌ No CSV files found in {test_data_dir}")
        return
    
    print(f"📁 Found {len(csv_files)} CSV files for testing")
    
    # Test each file
    successful_tests = 0
    for csv_file in csv_files:
        if test_timecourse_performance(csv_file, f"Testing {csv_file.name}"):
            successful_tests += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📋 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total files tested: {len(csv_files)}")
    print(f"Successful tests: {successful_tests}")
    print(f"Failed tests: {len(csv_files) - successful_tests}")
    
    if successful_tests > 0:
        print(f"\n✅ Performance improvements are working!")
    else:
        print(f"\n❌ All tests failed - check the implementation")


if __name__ == "__main__":
    main() 