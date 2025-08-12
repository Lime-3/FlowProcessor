#!/usr/bin/env python3
"""
Simple debug script to test plot title functionality without GUI dependencies.
"""

import sys
import logging
from pathlib import Path

# Add the flowproc package to the path
sys.path.insert(0, str(Path(__file__).parent / 'flowproc'))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a simple mock options class
class MockVisualizationOptions:
    """Mock class to simulate the VisualizationOptions without GUI dependencies."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def test_filter_options():
    """Test the filter options object and title creation."""
    print("=== Testing Filter Options ===")
    
    # Create a test options object
    options = MockVisualizationOptions(
        plot_type="bar",
        y_axis="Test Metric",
        time_course_mode=True,
        selected_tissues=["Tissue A", "Tissue B"],
        selected_times=["Day 1", "Day 2"],
        selected_population="CD4+"
    )
    
    print(f"Options object: {options}")
    print(f"Options type: {type(options)}")
    print(f"hasattr selected_population: {hasattr(options, 'selected_population')}")
    print(f"hasattr selected_tissues: {hasattr(options, 'selected_tissues')}")
    print(f"hasattr selected_times: {hasattr(options, 'selected_times')}")
    
    # Test direct attribute access
    try:
        print(f"selected_population: {options.selected_population}")
        print(f"selected_tissues: {options.selected_tissues}")
        print(f"selected_times: {options.selected_times}")
    except Exception as e:
        print(f"Error accessing attributes: {e}")
    
    # Test title creation
    print("\n=== Testing Title Creation ===")
    
    try:
        from flowproc.domain.visualization.column_utils import create_timecourse_plot_title, create_comprehensive_plot_title
        
        timecourse_title = create_timecourse_plot_title(
            df=None,  # Not needed for this test
            metric_type="Test Metric",
            cell_types=["CD4+"],
            filter_options=options
        )
        print(f"Timecourse title created: {timecourse_title}")
    except Exception as e:
        print(f"Error creating timecourse title: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        comprehensive_title = create_comprehensive_plot_title(
            df=None,  # Not needed for this test
            metric_type="Test Metric",
            cell_types=["CD4+"],
            filter_options=options
        )
        print(f"Comprehensive title created: {comprehensive_title}")
    except Exception as e:
        print(f"Error creating comprehensive title: {e}")
        import traceback
        traceback.print_exc()

def test_with_none_filter_options():
    """Test title creation with None filter options."""
    print("\n=== Testing with None Filter Options ===")
    
    try:
        from flowproc.domain.visualization.column_utils import create_timecourse_plot_title, create_comprehensive_plot_title
        
        timecourse_title = create_timecourse_plot_title(
            df=None,
            metric_type="Test Metric",
            cell_types=["CD4+"],
            filter_options=None
        )
        print(f"Timecourse title with None filter_options: {timecourse_title}")
    except Exception as e:
        print(f"Error creating timecourse title with None filter_options: {e}")
    
    try:
        comprehensive_title = create_comprehensive_plot_title(
            df=None,
            metric_type="Test Metric",
            cell_types=["CD4+"],
            filter_options=None
        )
        print(f"Comprehensive title with None filter_options: {comprehensive_title}")
    except Exception as e:
        print(f"Error creating comprehensive title with None filter_options: {e}")

def test_attribute_access():
    """Test different ways of accessing attributes."""
    print("\n=== Testing Attribute Access Methods ===")
    
    options = MockVisualizationOptions(
        selected_population="CD4+",
        selected_tissues=["Tissue A"],
        selected_times=["Day 1"]
    )
    
    # Test hasattr
    print(f"hasattr selected_population: {hasattr(options, 'selected_population')}")
    print(f"hasattr selected_tissues: {hasattr(options, 'selected_tissues')}")
    print(f"hasattr selected_times: {hasattr(options, 'selected_times')}")
    print(f"hasattr non_existent: {hasattr(options, 'non_existent')}")
    
    # Test getattr with default
    print(f"getattr selected_population: {getattr(options, 'selected_population', 'NOT_FOUND')}")
    print(f"getattr non_existent: {getattr(options, 'non_existent', 'NOT_FOUND')}")
    
    # Test direct access
    print(f"direct selected_population: {options.selected_population}")
    print(f"direct selected_tissues: {options.selected_tissues}")
    print(f"direct selected_times: {options.selected_times}")

if __name__ == "__main__":
    test_attribute_access()
    test_filter_options()
    test_with_none_filter_options()
