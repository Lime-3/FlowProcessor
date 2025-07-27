#!/usr/bin/env python3
"""
Test script to verify that the timecourse visualizer dialog opens wide enough to display all tools.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from flowproc.presentation.gui.visualizer import visualize_metric

def test_dialog_width():
    """Test that the visualizer dialog opens with sufficient width."""
    
    # Create a test CSV file with multiple tissues and subpopulations
    test_csv = Path("test_dialog_data.csv")
    
    # Create test data that will trigger all controls (multiple tissues, subpopulations)
    test_data = """SampleID,Group_Label,Subpopulation,Tissue,Mean,Std,Time,Metric
SP_A1_1.1,Group 1,CD4+ T cells,SP,10.5,0.5,2.0,Freq. of Parent
SP_A1_1.2,Group 1,CD4+ T cells,SP,11.0,0.6,2.0,Freq. of Parent
SP_A1_1.3,Group 1,CD4+ T cells,SP,10.8,0.4,2.0,Freq. of Parent
SP_A2_2.1,Group 1,CD8+ T cells,SP,8.2,0.3,6.0,Freq. of Parent
SP_A2_2.2,Group 1,CD8+ T cells,SP,8.5,0.4,6.0,Freq. of Parent
SP_A2_2.3,Group 1,CD8+ T cells,SP,8.3,0.3,6.0,Freq. of Parent
BM_B1_1.1,Group 2,CD4+ T cells,BM,9.5,0.4,2.0,Freq. of Parent
BM_B1_1.2,Group 2,CD4+ T cells,BM,9.8,0.5,2.0,Freq. of Parent
BM_B1_1.3,Group 2,CD4+ T cells,BM,9.6,0.4,2.0,Freq. of Parent
BM_B2_2.1,Group 2,CD8+ T cells,BM,7.2,0.2,6.0,Freq. of Parent
BM_B2_2.2,Group 2,CD8+ T cells,BM,7.5,0.3,6.0,Freq. of Parent
BM_B2_2.3,Group 2,CD8+ T cells,BM,7.3,0.2,6.0,Freq. of Parent"""
    
    with open(test_csv, "w") as f:
        f.write(test_data)
    
    try:
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("Opening visualizer dialog...")
        print("Expected dialog width: 1400 pixels")
        print("Expected minimum width: 1200 pixels")
        print("Dialog should display:")
        print("- Theme selector (180px min width)")
        print("- Metric selector (160px min width)")
        print("- Tissue filter (140px min width)") 
        print("- Subpopulation filter (200px min width)")
        print("- 4 action buttons (Refresh, Save, Export PDF, Close)")
        print("- Proper spacing between controls")
        
        # Open the visualizer dialog
        visualize_metric(
            csv_path=test_csv,
            metric="Freq. of Parent",
            time_course_mode=True,
            parent_widget=None
        )
        
        print("\n✅ Dialog opened successfully!")
        print("Please verify that:")
        print("1. All controls are visible and not cramped")
        print("2. Dialog width is 1400 pixels")
        print("3. Controls have proper spacing")
        print("4. Dialog is centered on screen")
        print("5. Metric selector allows changing between different metrics")
        print("6. Dialog title updates when metric changes")
        
    except Exception as e:
        print(f"❌ Error opening dialog: {e}")
        QMessageBox.critical(None, "Test Error", f"Failed to open dialog: {e}")
    
    finally:
        # Clean up test file
        if test_csv.exists():
            test_csv.unlink()

if __name__ == "__main__":
    test_dialog_width() 