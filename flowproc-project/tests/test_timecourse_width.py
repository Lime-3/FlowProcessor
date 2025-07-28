#!/usr/bin/env python3
"""
Simple test script to verify that timecourse plots use the correct width.
"""

import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flowproc-project'))

from flowproc.domain.visualization.visualize import VisualizationConfig, Visualizer, ProcessedData, visualize_data
import pandas as pd

def test_timecourse_width():
    """Test that timecourse plots use the correct width."""
    
    # Create test data with multiple tissues and subpopulations to force multiple subplots
    test_data = pd.DataFrame({
        'SampleID': [f'Sample_{i+1}' for i in range(16)],  # Unique sample IDs
        'Group_Label': ['Group 1', 'Group 2', 'Group 1', 'Group 2'] * 4,  # 16 rows total
        'Subpopulation': ['CD4', 'CD4', 'CD8', 'CD8'] * 4,  # 2 subpopulations
        'Tissue': ['SP', 'SP', 'SP', 'SP', 'BM', 'BM', 'BM', 'BM'] * 2,  # 2 tissues
        'Mean': [10.5, 15.3, 8.2, 12.1, 9.5, 14.3, 7.2, 11.1, 10.5, 15.3, 8.2, 12.1, 9.5, 14.3, 7.2, 11.1],
        'Std': [0.5, 0.7, 0.3, 0.6, 0.4, 0.6, 0.2, 0.5, 0.5, 0.7, 0.3, 0.6, 0.4, 0.6, 0.2, 0.5],
        'Time': [0.0, 24.0, 0.0, 24.0] * 4,  # 2 time points
        'Metric': ['Freq. of Parent'] * 16
    })
    
    processed_data = ProcessedData(
        dataframes=[test_data],
        metrics=['Freq. of Parent'],
        groups=[1, 2],
        times=[0.0, 24.0],
        tissues_detected=True,  # Set to True to force multiple subplots
        group_map={1: 'Group 1', 2: 'Group 2'},
        replicate_count=2
    )
    
    # Test with width=600
    config = VisualizationConfig(
        metric=None,
        time_course_mode=True,
        width=600,
        height=300
    )
    
    visualizer = Visualizer(config)
    fig = visualizer.create_figure(processed_data)
    
    print(f"Timecourse plot width: {fig.layout.width}")
    print(f"Expected width: 600")
    print(f"Width matches: {fig.layout.width == 600}")
    
    # Check if subplots exist
    if hasattr(fig, '_grid_ref') and fig._grid_ref:
        print(f"Number of subplots: {len(fig._grid_ref)}")
        print(f"Subplot structure: {type(fig._grid_ref)}")
    
    assert fig.layout.width == 600, f"Expected width 600, got {fig.layout.width}"
    print("✅ Timecourse plot width test passed!")
    
    # Test HTML generation
    print("\nTesting HTML generation...")
    
    # Test the figure directly by writing it to HTML
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_html:
        html_path = tmp_html.name
    
    try:
        # Write the figure directly to HTML
        fig.write_html(
            html_path,
            include_plotlyjs=True,  # Use embedded Plotly.js for offline compatibility
            full_html=True
        )
        
        print(f"HTML generation successful")
        print(f"Generated figure width: {fig.layout.width}")
        print(f"Expected width: 600")
        print(f"Width matches: {fig.layout.width == 600}")
        
        # Check the HTML file content
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Look for width in the HTML
        if 'width' in html_content.lower():
            print("✅ Width found in HTML content")
        else:
            print("❌ Width not found in HTML content")
        
        # Look for specific width value
        if '600' in html_content:
            print("✅ Width value 600 found in HTML")
        else:
            print("❌ Width value 600 not found in HTML")
        
        # Look for Plotly layout width
        if '"width": 600' in html_content:
            print("✅ Plotly layout width 600 found in HTML")
        else:
            print("❌ Plotly layout width 600 not found in HTML")
        
        # Look for any width-related content in the HTML
        width_related_lines = [line for line in html_content.split('\n') if 'width' in line.lower()]
        if width_related_lines:
            print(f"Found {len(width_related_lines)} lines with 'width':")
            for line in width_related_lines[:5]:  # Show first 5 lines
                print(f"  {line.strip()}")
        else:
            print("❌ No width-related lines found in HTML")
        
        # Look for the Plotly.newPlot call
        if 'Plotly.newPlot(' in html_content:
            print("✅ Plotly.newPlot found in HTML")
            # Find the Plotly.newPlot call
            plotly_start = html_content.find('Plotly.newPlot(')
            if plotly_start != -1:
                plotly_end = html_content.find(');', plotly_start)
                if plotly_end != -1:
                    plotly_call = html_content[plotly_start:plotly_end+2]
                    print(f"Plotly call: {plotly_call[:200]}...")  # Show first 200 chars
        else:
            print("❌ Plotly.newPlot not found in HTML")
        
        assert fig.layout.width == 600, f"Expected width 600, got {fig.layout.width}"
        print("✅ HTML generation test passed!")
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(html_path)
        except:
            pass

if __name__ == "__main__":
    test_timecourse_width() 