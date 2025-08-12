#!/usr/bin/env python3
"""
Debug script to test plot title functionality and identify tracing issues.
"""

import sys
import logging
from pathlib import Path

# Add the flowproc package to the path
sys.path.insert(0, str(Path(__file__).parent / 'flowproc'))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from flowproc.presentation.gui.views.dialogs.visualization_dialog import VisualizationOptions
from flowproc.domain.visualization.column_utils import create_timecourse_plot_title, create_comprehensive_plot_title

def test_filter_options():
    """Test the filter options object and title creation."""
    print("=== Testing Filter Options ===")
    
    # Create a test options object
    options = VisualizationOptions(
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

if __name__ == "__main__":
    test_filter_options()
    test_with_none_filter_options()
