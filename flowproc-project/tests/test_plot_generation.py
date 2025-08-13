#!/usr/bin/env python3
"""
Test script to specifically test plot generation with the new filter interface.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flowproc.presentation.gui.views.dialogs.visualization_dialog import (
    VisualizationDialog
)
from flowproc.presentation.gui.views.dialogs.visualization_options import (
    VisualizationOptions
)

def test_plot_generation():
    """Test plot generation with the new filter interface."""
    # Reuse existing app if one already exists to avoid singleton errors
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Use a test CSV file
    test_csv = project_root / "tests" / "data" / "AT25-AS293.csv"
    
    if not test_csv.exists():
        print(f"Test CSV not found: {test_csv}")
        return 1
    
    print(f"Testing plot generation with: {test_csv}")
    
    # Create the dialog
    dialog = VisualizationDialog(csv_path=test_csv)
    
    # Show the dialog
    dialog.show()
    
    # Set up a timer to trigger plot generation after 2 seconds
    def generate_plot():
        print("Triggering plot generation...")
        try:
            # Get current options and generate plot
            options = dialog.get_current_options()
            print(f"Current options: time_course_mode={options.time_course_mode}")
            dialog._generate_plot()
            print("Plot generation completed")
        except Exception as e:
            print(f"Plot generation failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Set up a timer to close the dialog after 15 seconds
    def close_dialog():
        print("Closing dialog...")
        dialog.close()
    
    plot_timer = QTimer()
    plot_timer.timeout.connect(generate_plot)
    plot_timer.start(2000)  # 2 seconds
    
    close_timer = QTimer()
    close_timer.timeout.connect(close_dialog)
    close_timer.start(15000)  # 15 seconds
    
    print("Dialog opened. Plot will be generated in 2 seconds.")
    print("Dialog will close automatically in 15 seconds.")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_plot_generation()) 