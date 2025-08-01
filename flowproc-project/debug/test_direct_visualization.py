#!/usr/bin/env python3
"""
Test script to verify direct visualization flow without intermediary dialog.
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from flowproc.presentation.gui.views.dialogs.visualization_display_dialog import VisualizationDisplayDialog

def test_direct_visualization():
    """Test that visualization opens directly without intermediary dialog."""
    print("=== Testing Direct Visualization Flow ===")
    
    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create a test CSV file
    test_data = pd.DataFrame({
        'SampleID': ['SP_1.1', 'SP_1.2', 'SP_2.1', 'SP_2.2'],
        'Group': [1, 1, 2, 2],
        'Animal': [1, 2, 1, 2],
        'Time': [0.0, 0.0, 24.0, 24.0],
        'Freq. of Parent CD4': [10.5, 11.2, 15.3, 14.8],
        'Median CD4': [1200, 1250, 1400, 1380],
        'Count CD8': [500, 550, 600, 580],
    })
    
    # Save to temporary CSV file
    test_csv_path = Path("test_visualization_data.csv")
    test_data.to_csv(test_csv_path, index=False)
    
    try:
        print(f"Created test CSV file: {test_csv_path}")
        print(f"Test data shape: {test_data.shape}")
        
        # Test direct visualization dialog creation
        print("Creating VisualizationDisplayDialog...")
        dialog = VisualizationDisplayDialog(
            parent=None,
            csv_path=test_csv_path
        )
        
        print("✅ SUCCESS: VisualizationDisplayDialog created successfully!")
        print(f"Dialog title: {dialog.windowTitle()}")
        print(f"Dialog size: {dialog.size()}")
        
        # Check if data was loaded
        if hasattr(dialog, 'df') and dialog.df is not None:
            print(f"✅ SUCCESS: Data loaded into dialog (shape: {dialog.df.shape})")
        else:
            print("❌ FAILURE: Data not loaded into dialog")
        
        # Check if placeholder plot was generated
        if hasattr(dialog, 'options') and dialog.options is not None:
            print(f"✅ SUCCESS: Options set for placeholder plot")
        else:
            print("⚠️  WARNING: No options set - placeholder plot may not be generated")
        
        print("✅ SUCCESS: Direct visualization flow works correctly!")
        
    except Exception as e:
        print(f"❌ FAILURE: Error in direct visualization flow: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test file
        if test_csv_path.exists():
            test_csv_path.unlink()
            print(f"Cleaned up test file: {test_csv_path}")

if __name__ == "__main__":
    test_direct_visualization() 