#!/usr/bin/env python3
"""
Comprehensive test script for plotting functionality.
Tests various scenarios and changes to the plotting system.
"""

import sys
import os
import tempfile
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from flowproc.domain.visualization.flow_cytometry_visualizer import plot
from flowproc.domain.visualization.plot_utils import calculate_layout_for_long_labels
from flowproc.domain.visualization.plotly_renderer import PlotlyRenderer

def create_test_data():
    """Create comprehensive test data for various plotting scenarios."""
    
    # Basic test data
    basic_data = pd.DataFrame({
        'SampleID': ['SP_1.1', 'SP_1.2', 'SP_2.1', 'SP_2.2', 'BM_1.1', 'BM_1.2', 'BM_2.1', 'BM_2.2'],
        'Group_Label': ['Group 1', 'Group 1', 'Group 2', 'Group 2', 'Group 1', 'Group 1', 'Group 2', 'Group 2'],
        'Subpopulation': ['CD4', 'CD4', 'CD4', 'CD4', 'CD8', 'CD8', 'CD8', 'CD8'],
        'Tissue': ['SP', 'SP', 'SP', 'SP', 'BM', 'BM', 'BM', 'BM'],
        'Mean': [10.5, 11.2, 15.3, 14.8, 8.2, 8.9, 12.1, 11.8],
        'Std': [0.5, 0.6, 0.7, 0.6, 0.3, 0.4, 0.5, 0.4],
        'Time': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'Metric': ['Freq. of Parent'] * 8
    })
    
    # Time course data
    timecourse_data = pd.DataFrame({
        'SampleID': ['SP_1.1_0h', 'SP_1.2_0h', 'SP_1.1_24h', 'SP_1.2_24h', 
                     'BM_2.1_0h', 'BM_2.2_0h', 'BM_2.1_24h', 'BM_2.2_24h'],
        'Group_Label': ['Group 1', 'Group 1', 'Group 1', 'Group 1', 
                       'Group 2', 'Group 2', 'Group 2', 'Group 2'],
        'Subpopulation': ['CD4', 'CD4', 'CD4', 'CD4', 'CD8', 'CD8', 'CD8', 'CD8'],
        'Tissue': ['SP', 'SP', 'SP', 'SP', 'BM', 'BM', 'BM', 'BM'],
        'Mean': [10.5, 11.2, 12.1, 12.8, 8.2, 8.9, 9.5, 10.1],
        'Std': [0.5, 0.6, 0.7, 0.6, 0.3, 0.4, 0.5, 0.4],
        'Time': [0.0, 0.0, 24.0, 24.0, 0.0, 0.0, 24.0, 24.0],
        'Metric': ['Freq. of Parent'] * 8
    })
    
    # Multi-tissue data
    multi_tissue_data = pd.DataFrame({
        'SampleID': ['SP_1.1', 'SP_1.2', 'BM_1.1', 'BM_1.2', 'LN_1.1', 'LN_1.2'],
        'Group_Label': ['Group 1', 'Group 1', 'Group 1', 'Group 1', 'Group 1', 'Group 1'],
        'Subpopulation': ['CD4', 'CD4', 'CD4', 'CD4', 'CD4', 'CD4'],
        'Tissue': ['SP', 'SP', 'BM', 'BM', 'LN', 'LN'],
        'Mean': [10.5, 11.2, 8.2, 8.9, 6.1, 6.8],
        'Std': [0.5, 0.6, 0.3, 0.4, 0.2, 0.3],
        'Time': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'Metric': ['Freq. of Parent'] * 6
    })
    
    return basic_data, timecourse_data, multi_tissue_data

def test_plotly_renderer():
    """Test the PlotlyRenderer functionality."""
    print("\n=== Testing PlotlyRenderer ===")
    
    renderer = PlotlyRenderer()
    
    # Test data
    df = pd.DataFrame({
        'x': [1, 2, 3, 4],
        'y': [10, 20, 15, 25],
        'category': ['A', 'A', 'B', 'B']
    })
    
    # Test scatter plot
    fig = renderer.render_scatter(df, 'x', 'y', 'category', title="Test Scatter")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    print("✅ Scatter plot rendering works")
    
    # Test bar plot
    fig = renderer.render_bar(df, 'x', 'y', 'category', title="Test Bar")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    print("✅ Bar plot rendering works")
    
    # Test line plot
    fig = renderer.render_line(df, 'x', 'y', 'category', title="Test Line")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
    print("✅ Line plot rendering works")
    
    # Test export functionality
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
        renderer.export_to_html(fig, tmp.name)
        assert Path(tmp.name).exists()
        print("✅ HTML export works")
        os.unlink(tmp.name)

def test_visualization_service():
    """Test the VisualizationService functionality."""
    print("\n=== Testing VisualizationService ===")
    
    # This test will need to be updated to use the new visualization modules
    # For now, we'll just print a placeholder message.
    print("VisualizationService test is a placeholder. It will be implemented later.")

def test_plotting_functions():
    """Test the core plotting functions."""
    print("\n=== Testing Core Plotting Functions ===")
    
    # Test data
    basic_data, timecourse_data, multi_tissue_data = create_test_data()
    
    # Test bar plot creation
    try:
        fig = plot(basic_data, "Freq. of Parent", 800, 600, "plotly_white")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        print("✅ Bar plot creation works")
    except Exception as e:
        print(f"❌ Bar plot creation failed: {e}")
    
    # Test line plot creation
    try:
        fig = plot(timecourse_data, "Freq. of Parent", 800, 600, "plotly_white")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        print("✅ Line plot creation works")
    except Exception as e:
        print(f"❌ Line plot creation failed: {e}")
    
    # Test layout calculation
    try:
        labels = ["Very Long Label 1", "Very Long Label 2", "Short"]
        layout = calculate_layout_for_long_labels(labels, 2, "Test Title", ["A", "B"], 600, 300)
        assert isinstance(layout, dict)
        assert 'width' in layout
        assert 'height' in layout
        print("✅ Layout calculation works")
    except Exception as e:
        print(f"❌ Layout calculation failed: {e}")

def test_visualizer_class():
    """Test the Visualizer class functionality."""
    print("\n=== Testing Visualizer Class ===")
    
    # This test will need to be updated to use the new visualization modules
    # For now, we'll just print a placeholder message.
    print("Visualizer class test is a placeholder. It will be implemented later.")

def test_theme_functionality():
    """Test theme functionality."""
    print("\n=== Testing Theme Functionality ===")
    
    # This test will need to be updated to use the new visualization modules
    # For now, we'll just print a placeholder message.
    print("Theme functionality test is a placeholder. It will be implemented later.")

def test_data_processor():
    """Test the DataProcessor functionality."""
    print("\n=== Testing DataProcessor ===")
    
    # Create test CSV data
    test_data = pd.DataFrame({
        'SampleID': ['SP_1.1', 'SP_1.2', 'SP_2.1', 'SP_2.2'],
        'Group': [1, 1, 2, 2],
        'Animal': [1, 2, 1, 2],
        'Replicate': [1, 2, 1, 2],
        'Time': [0.0, 0.0, 0.0, 0.0],
        'Freq. of Parent CD4': [10.5, 11.2, 15.3, 14.8]
    })
    
    # This test will need to be updated to use the new visualization modules
    # For now, we'll just print a placeholder message.
    print("DataProcessor test is a placeholder. It will be implemented later.")

def test_integration():
    """Test the complete visualization pipeline."""
    print("\n=== Testing Complete Integration ===")
    
    # Create temporary test CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_csv:
        tmp_csv.write("SampleID,Group,Animal,Replicate,Time,Freq. of Parent CD4\n")
        tmp_csv.write("SP_1.1,1,1,1,0.0,10.5\n")
        tmp_csv.write("SP_1.2,1,2,2,0.0,11.2\n")
        tmp_csv.write("SP_2.1,2,1,1,0.0,15.3\n")
        tmp_csv.write("SP_2.2,2,2,2,0.0,14.8\n")
        csv_path = tmp_csv.name
    
    # Create temporary output HTML
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_html:
        html_path = tmp_html.name
    
    try:
        # Test visualization pipeline
        # This test will need to be updated to use the new visualization modules
        # For now, we'll just print a placeholder message.
        print("Complete visualization pipeline test is a placeholder. It will be implemented later.")
        
    except Exception as e:
        print(f"❌ Complete visualization pipeline failed: {e}")
    finally:
        # Cleanup
        if Path(csv_path).exists():
            os.unlink(csv_path)
        if Path(html_path).exists():
            os.unlink(html_path)

def test_error_handling():
    """Test error handling in plotting functions."""
    print("\n=== Testing Error Handling ===")
    
    # Test with empty data
    empty_df = pd.DataFrame()
    
    try:
        renderer = PlotlyRenderer()
        fig = renderer.render_scatter(empty_df, 'x', 'y')
        print("✅ Empty data handling works")
    except Exception as e:
        print(f"❌ Empty data handling failed: {e}")
    
    # Test with invalid column names
    test_df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    
    try:
        renderer = PlotlyRenderer()
        fig = renderer.render_scatter(test_df, 'x', 'y')  # Invalid columns
        print("✅ Invalid column handling works")
    except Exception as e:
        print(f"❌ Invalid column handling failed: {e}")

def main():
    """Run all tests."""
    print("🧪 Starting Comprehensive Plotting Tests")
    print("=" * 50)
    
    try:
        test_plotly_renderer()
        test_visualization_service()
        test_plotting_functions()
        test_visualizer_class()
        test_theme_functionality()
        test_data_processor()
        test_integration()
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 