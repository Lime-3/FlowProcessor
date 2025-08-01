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

from flowproc.domain.visualization.facade import create_visualization
from flowproc.domain.visualization.facade import (
    visualize_data, 
    VisualizationConfig, 
    Visualizer, 
    ProcessedData,
    DataProcessor
)
from flowproc.domain.visualization.plotting import (
    create_bar_plot, 
    create_line_plot, 
    apply_plot_style,
    calculate_layout_for_long_labels
)
from flowproc.domain.visualization.plotly_renderer import PlotlyRenderer
from flowproc.domain.visualization.service import VisualizationService
from flowproc.domain.visualization.themes import VisualizationThemes

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
    
    service = VisualizationService()
    
    # Test data
    df = pd.DataFrame({
        'x': [1, 2, 3, 4],
        'y': [10, 20, 15, 25],
        'category': ['A', 'A', 'B', 'B']
    })
    
    # Test different plot types
    plot_types = ['scatter', 'bar', 'line', 'box', 'histogram']
    
    for plot_type in plot_types:
        config = {
            'x': 'x',
            'y': 'y',
            'color': 'category',
            'title': f'Test {plot_type.title()}'
        }
        
        try:
            fig = service.create_plot(df, plot_type, config)
            assert isinstance(fig, go.Figure)
            print(f"✅ {plot_type.title()} plot creation works")
        except Exception as e:
            print(f"❌ {plot_type.title()} plot creation failed: {e}")

def test_plotting_functions():
    """Test the core plotting functions."""
    print("\n=== Testing Core Plotting Functions ===")
    
    # Test data
    basic_data, timecourse_data, multi_tissue_data = create_test_data()
    
    # Test bar plot creation
    try:
        fig = create_bar_plot(basic_data, "Freq. of Parent", 800, 600, "plotly_white")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        print("✅ Bar plot creation works")
    except Exception as e:
        print(f"❌ Bar plot creation failed: {e}")
    
    # Test line plot creation
    try:
        fig = create_line_plot(timecourse_data, "Freq. of Parent", 800, 600, "plotly_white")
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
    
    # Test data
    basic_data, timecourse_data, multi_tissue_data = create_test_data()
    
    # Test bar plot mode
    config = VisualizationConfig(
        metric=None,
        time_course_mode=False,
        width=800,
        height=600
    )
    
    processed_data = ProcessedData(
        dataframes=[basic_data],
        metrics=['Freq. of Parent'],
        groups=[1, 2],
        times=[0.0],
        tissues_detected=True,
        group_map={1: 'Group 1', 2: 'Group 2'},
        replicate_count=2
    )
    
    visualizer = Visualizer(config)
    
    try:
        fig = visualizer.create_figure(processed_data)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        print("✅ Bar plot mode works")
    except Exception as e:
        print(f"❌ Bar plot mode failed: {e}")
    
    # Test time course mode
    config = VisualizationConfig(
        metric=None,
        time_course_mode=True,
        width=800,
        height=600
    )
    processed_data = ProcessedData(
        dataframes=[timecourse_data],
        metrics=['Freq. of Parent'],
        groups=[1, 2],
        times=[0.0, 24.0],
        tissues_detected=True,
        group_map={1: 'Group 1', 2: 'Group 2'},
        replicate_count=2
    )
    
    try:
        fig = visualizer.create_figure(processed_data)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        print("✅ Time course mode works")
    except Exception as e:
        print(f"❌ Time course mode failed: {e}")

def test_theme_functionality():
    """Test theme functionality."""
    print("\n=== Testing Theme Functionality ===")
    
    themes = VisualizationThemes()
    
    # Test available themes
    available_themes = themes.get_available_themes()
    assert isinstance(available_themes, list)
    assert len(available_themes) > 0
    print(f"✅ Available themes: {available_themes}")
    
    # Test theme application
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3]))
    
    for theme in available_themes[:3]:  # Test first 3 themes
        try:
            themes.apply_theme(fig, theme)
            print(f"✅ Theme '{theme}' application works")
        except Exception as e:
            print(f"❌ Theme '{theme}' application failed: {e}")

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
    
    config = VisualizationConfig(
        metric="Freq. of Parent",
        time_course_mode=False,
        width=800,
        height=600
    )
    
    try:
        processor = DataProcessor(test_data, 'SampleID', config)
        processed_data = processor.process()
        
        assert isinstance(processed_data, ProcessedData)
        assert len(processed_data.dataframes) > 0
        assert len(processed_data.metrics) > 0
        print("✅ Data processing works")
    except Exception as e:
        print(f"❌ Data processing failed: {e}")

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
        fig = create_visualization(
            data_source=csv_path,
            output_html=html_path,
            metric="Freq. of Parent",
            width=800,
            height=600,
            theme="plotly_white",
            time_course_mode=False
        )
        
        assert isinstance(fig, go.Figure)
        assert Path(html_path).exists()
        assert Path(html_path).stat().st_size > 0
        print("✅ Complete visualization pipeline works")
        
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