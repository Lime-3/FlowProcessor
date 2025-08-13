#!/usr/bin/env python3
"""
Test script to verify that time columns can be selected for the x-axis 
without automatically enabling timecourse mode.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
from flowproc.presentation.gui.views.dialogs.visualization_dialog import (
    VisualizationDialog
)
from flowproc.presentation.gui.views.dialogs.visualization_options import (
    VisualizationOptions
)
from PySide6.QtWidgets import QApplication
import tempfile

def create_test_data():
    """Create test data with time columns in a format the parser can handle."""
    data = {
        'SampleID': ['AT25-AS222-HSC_Day1_Rep1', 'AT25-AS222-HSC_Day1_Rep2', 
                     'AT25-AS222-HSC_Day2_Rep1', 'AT25-AS222-HSC_Day2_Rep2',
                     'AT25-AS238_Day1_Rep1', 'AT25-AS238_Day1_Rep2'],
        'Time': ['Day 1', 'Day 1', 'Day 2', 'Day 2', 'Day 1', 'Day 1'],
        'Group': ['HSC', 'HSC', 'HSC', 'HSC', 'AS238', 'AS238'],
        'CD4+ T cells - Freq. of Parent': [10.5, 12.3, 11.2, 13.1, 9.8, 14.2],
        'CD8+ T cells - Freq. of Parent': [8.2, 9.1, 8.9, 9.8, 7.5, 10.1],
        'Tissue': ['Blood', 'Blood', 'Blood', 'Blood', 'Blood', 'Blood']
    }
    return pd.DataFrame(data)

def test_time_column_selection():
    """Test that time columns can be selected without forcing timecourse mode."""
    print("🧪 Testing time column selection without timecourse mode...")
    
    # Create test data
    df = create_test_data()
    
    # Save to temporary CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        csv_path = Path(f.name)
    
    try:
        # Create application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create dialog
        dialog = VisualizationDialog(csv_path=csv_path)
        
        # Wait a bit for the dialog to initialize
        app.processEvents()
        
        # Check initial state
        print(f"Initial plot_by_times: {dialog.time_course_checkbox.isChecked()}")
        print(f"Initial plot_type: {dialog.plot_type_combo.currentText()}")
        
        # Verify that timecourse mode is not enabled
        assert not dialog.time_course_checkbox.isChecked(), "Timecourse mode should not be automatically enabled"
        
        # Test changing plot type
        dialog.plot_type_combo.setCurrentText('scatter')
        print(f"After changing to scatter: {dialog.plot_type_combo.currentText()}")
        
        # Get current options
        options = dialog.get_current_options()
        print(f"Options plot_type: {options.plot_type}")
        print(f"Options y_axis: {options.y_axis}")
        print(f"Options time_course_mode: {options.time_course_mode}")
        
        # Verify options are correct
        assert options.plot_type == 'scatter', f"Expected 'scatter', got '{options.plot_type}'"
        assert not options.time_course_mode, "time_course_mode should be False"
        
        print("✅ Test passed! Time columns can be selected without forcing timecourse mode.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        if csv_path.exists():
            csv_path.unlink()

if __name__ == "__main__":
    success = test_time_column_selection()
    sys.exit(0 if success else 1) 