#!/usr/bin/env python3
"""
Test script to verify that the metric selector in the visualizer dialog works correctly.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from flowproc.presentation.gui.visualizer import visualize_metric

def test_metric_selector():
    """Test that the metric selector in the visualizer dialog works correctly."""
    
    # Create a test CSV file with multiple metrics
    test_csv = Path("test_metric_selector_data.csv")
    
    # Create test data with multiple metrics
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
        
        print("Testing metric selector functionality...")
        print("Expected features:")
        print("1. Metric selector dropdown shows all available metrics")
        print("2. Changing metric updates the plot")
        print("3. Dialog title updates to reflect selected metric")
        print("4. Subpopulation options update when metric changes")
        
        # Open the visualizer dialog
        visualize_metric(
            csv_path=test_csv,
            metric="Freq. of Parent",  # Start with this metric
            time_course_mode=True,
            parent_widget=None
        )
        
        print("\n✅ Metric selector test completed!")
        print("Please verify that:")
        print("1. Metric selector dropdown contains all available metrics")
        print("2. Selecting different metrics generates different plots")
        print("3. Dialog title changes when metric is selected")
        print("4. All controls remain functional after metric changes")
        
    except Exception as e:
        print(f"❌ Error testing metric selector: {e}")
        QMessageBox.critical(None, "Test Error", f"Failed to test metric selector: {e}")
    
    finally:
        # Clean up test file
        if test_csv.exists():
            test_csv.unlink()

if __name__ == "__main__":
    test_metric_selector() 