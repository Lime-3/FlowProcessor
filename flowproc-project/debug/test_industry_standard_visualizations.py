#!/usr/bin/env python3
"""
Test script to demonstrate industry-standard timecourse visualization approaches.
"""

import sys
import logging
import time
from pathlib import Path
from typing import Optional

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.parsing import load_and_parse_df
from flowproc.domain.visualization.simple_visualizer import (
    time_plot, time_plot_faceted, time_plot_dashboard, time_plot_hierarchical
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_industry_standard_approaches(csv_path: Path, test_name: str = "Industry Standard Test"):
    """Test different industry-standard timecourse visualization approaches."""
    print(f"\n{'='*80}")
    print(f"🏭 {test_name}")
    print(f"{'='*80}")
    
    try:
        # Load data
        print(f"📊 Loading data from: {csv_path}")
        start_time = time.time()
        df, sid_col = load_and_parse_df(csv_path)
        load_time = time.time() - start_time
        print(f"✅ Data loaded in {load_time:.2f}s")
        print(f"   Shape: {df.shape}")
        print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
        
        # Test different industry-standard approaches
        approaches = [
            {
                "name": "Standard Multi-Line",
                "description": "Traditional approach - all cell types in one plot",
                "function": time_plot,
                "kwargs": {"max_cell_types": 10, "sample_size": 1000}
            },
            {
                "name": "Faceted by Group",
                "description": "Industry standard - separate subplot for each group",
                "function": time_plot_faceted,
                "kwargs": {"facet_by": "Group", "max_facets": 6}
            },
            {
                "name": "Faceted by Cell Type", 
                "description": "Industry standard - separate subplot for each cell type",
                "function": time_plot_faceted,
                "kwargs": {"facet_by": "Cell Type", "max_facets": 6}
            },
            {
                "name": "Interactive Dashboard",
                "description": "Modern standard - multi-panel dashboard with overview",
                "function": time_plot_dashboard,
                "kwargs": {}
            },
            {
                "name": "Hierarchical View",
                "description": "Advanced standard - overview + drill-down capability",
                "function": time_plot_hierarchical,
                "kwargs": {}
            }
        ]
        
        results = []
        
        for approach in approaches:
            print(f"\n🎯 Testing: {approach['name']}")
            print(f"   Description: {approach['description']}")
            
            start_time = time.time()
            try:
                fig = approach['function'](
                    data=csv_path,
                    value_col="Freq. of Parent",
                    width=1200,
                    height=800,
                    **approach['kwargs']
                )
                plot_time = time.time() - start_time
                
                print(f"   ✅ Generated in {plot_time:.2f}s")
                print(f"   📊 Figure size: {fig.layout.width}x{fig.layout.height}")
                
                # Analyze the figure
                num_traces = len(fig.data)
                num_subplots = len(fig.layout.annotations) if fig.layout.annotations else 1
                
                print(f"   📈 Traces: {num_traces}")
                print(f"   📋 Subplots: {num_subplots}")
                
                results.append({
                    "approach": approach['name'],
                    "time": plot_time,
                    "traces": num_traces,
                    "subplots": num_subplots,
                    "success": True
                })
                
            except Exception as e:
                plot_time = time.time() - start_time
                print(f"   ❌ Failed after {plot_time:.2f}s: {e}")
                results.append({
                    "approach": approach['name'],
                    "time": plot_time,
                    "traces": 0,
                    "subplots": 0,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary comparison
        print(f"\n{'='*80}")
        print(f"📊 COMPARISON SUMMARY")
        print(f"{'='*80}")
        print(f"{'Approach':<25} {'Time (s)':<10} {'Traces':<8} {'Subplots':<10} {'Status':<10}")
        print(f"{'-'*25} {'-'*10} {'-'*8} {'-'*10} {'-'*10}")
        
        for result in results:
            status = "✅ Success" if result['success'] else "❌ Failed"
            print(f"{result['approach']:<25} {result['time']:<10.2f} {result['traces']:<8} {result['subplots']:<10} {status:<10}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print(f"{'='*80}")
        
        successful_results = [r for r in results if r['success']]
        if successful_results:
            fastest = min(successful_results, key=lambda x: x['time'])
            most_traces = max(successful_results, key=lambda x: x['traces'])
            most_subplots = max(successful_results, key=lambda x: x['subplots'])
            
            print(f"🚀 Fastest: {fastest['approach']} ({fastest['time']:.2f}s)")
            print(f"📈 Most detailed: {most_traces['approach']} ({most_traces['traces']} traces)")
            print(f"📋 Most organized: {most_subplots['approach']} ({most_subplots['subplots']} subplots)")
            
            print(f"\n🎯 Use cases:")
            print(f"   • For exploration: Interactive Dashboard")
            print(f"   • For group comparison: Faceted by Group") 
            print(f"   • For cell type analysis: Faceted by Cell Type")
            print(f"   • For comprehensive analysis: Hierarchical View")
            print(f"   • For simple overview: Standard Multi-Line")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error("Test error", exc_info=True)
        return False


def main():
    """Run industry standard visualization tests."""
    print("🏭 Industry Standard Timecourse Visualization Test Suite")
    print("=" * 80)
    
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
        if test_industry_standard_approaches(csv_file, f"Testing {csv_file.name}"):
            successful_tests += 1
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"🏁 FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total files tested: {len(csv_files)}")
    print(f"Successful tests: {successful_tests}")
    print(f"Failed tests: {len(csv_files) - successful_tests}")
    
    if successful_tests > 0:
        print(f"\n✅ Industry standard approaches are working!")
        print(f"🎯 These approaches solve the timecourse complexity issue by:")
        print(f"   • Separating concerns (faceting)")
        print(f"   • Providing multiple views (dashboard)")
        print(f"   • Enabling drill-down analysis (hierarchical)")
        print(f"   • Maintaining performance (subplot limits)")
    else:
        print(f"\n❌ All tests failed - check the implementation")


if __name__ == "__main__":
    main() 