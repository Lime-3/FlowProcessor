#!/usr/bin/env python3
"""
Test script to verify that y-axis dropdown only shows summary metrics.
"""

import pandas as pd
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from flowproc.presentation.gui.views.dialogs.visualization_options_dialog import VisualizationOptionsDialog

def test_y_axis_options():
    """Test that y-axis dropdown only shows summary metrics."""
    print("=== Testing Y-Axis Options ===")
    
    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create sample data with both summary metrics and other columns
    df = pd.DataFrame({
        'SampleID': ['SP_1.1', 'SP_1.2', 'SP_2.1', 'SP_2.2'],
        'Group': [1, 1, 2, 2],
        'Animal': [1, 2, 1, 2],
        'Time': [0.0, 0.0, 24.0, 24.0],
        'Freq. of Parent CD4': [10.5, 11.2, 15.3, 14.8],  # Summary metric
        'Median CD4': [1200, 1250, 1400, 1380],  # Summary metric
        'Count CD8': [500, 550, 600, 580],  # Summary metric
        'Raw_Data_Column': [1.2, 1.3, 1.4, 1.5],  # Non-summary column
        'Another_Column': [100, 110, 120, 130],  # Non-summary column
    })
    
    print(f"Test data columns: {list(df.columns)}")
    
    # Test the _identify_summary_metrics method
    dialog = VisualizationOptionsDialog()
    summary_metrics = dialog._identify_summary_metrics(df)
    
    print(f"Identified summary metrics: {summary_metrics}")
    
    # Test the _populate_column_options method
    dialog._populate_column_options(df)
    
    # Get y-axis options
    y_axis_options = []
    for i in range(dialog.y_axis_combo.count()):
        y_axis_options.append(dialog.y_axis_combo.itemText(i))
    
    print(f"Y-axis dropdown options: {y_axis_options}")
    
    # Get custom y-axis options
    custom_y_axis_options = []
    for i in range(dialog.custom_y_axis_combo.count()):
        custom_y_axis_options.append(dialog.custom_y_axis_combo.itemText(i))
    
    print(f"Custom Y-axis dropdown options: {custom_y_axis_options}")
    
    # Verify that y-axis only contains summary metrics
    expected_y_axis = ['Auto-detect'] + summary_metrics
    if y_axis_options == expected_y_axis:
        print("✅ SUCCESS: Y-axis dropdown only contains summary metrics!")
    else:
        print("❌ FAILURE: Y-axis dropdown contains non-summary metrics!")
        print(f"Expected: {expected_y_axis}")
        print(f"Actual: {y_axis_options}")
    
    # Verify that custom y-axis contains all columns
    expected_custom_y_axis = ['Select column...'] + list(df.columns)
    if custom_y_axis_options == expected_custom_y_axis:
        print("✅ SUCCESS: Custom Y-axis dropdown contains all columns!")
    else:
        print("❌ FAILURE: Custom Y-axis dropdown missing columns!")
        print(f"Expected: {expected_custom_y_axis}")
        print(f"Actual: {custom_y_axis_options}")

if __name__ == "__main__":
    test_y_axis_options() 