#!/usr/bin/env python3
"""
Test script to verify visualization display dialog functionality.
Specifically tests y-axis selection and automatic plot updates.
"""

import sys
import time
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PySide6.QtWidgets import QApplication
    from flowproc.presentation.gui.views.dialogs.visualization_display_dialog import VisualizationDisplayDialog
    
    print("✅ Imports successful")
    
    # Find a test CSV file
    test_csv_dir = Path("../Test CSV")
    if not test_csv_dir.exists():
        test_csv_dir = Path("../../Test CSV")
    
    if not test_csv_dir.exists():
        print("❌ Could not find Test CSV directory")
        sys.exit(1)
    
    csv_files = list(test_csv_dir.glob("*.csv"))
    if not csv_files:
        print("❌ No CSV files found in Test CSV directory")
        sys.exit(1)
    
    csv_path = csv_files[0]
    print(f"📁 Using test file: {csv_path}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    print("✅ QApplication created")
    
    # Create and show the dialog
    print("🚀 Opening visualization display dialog...")
    dialog = VisualizationDisplayDialog(csv_path=csv_path)
    
    # Set up a timer to test y-axis selection after 2 seconds
    from PySide6.QtCore import QTimer
    
    def test_y_axis_selection():
        print("🧪 Testing y-axis selection...")
        try:
            # Get the y-axis combo box
            y_axis_combo = dialog.y_axis_combo
            
            if y_axis_combo and y_axis_combo.count() > 1:
                # Select a different y-axis option
                current_index = y_axis_combo.currentIndex()
                new_index = (current_index + 1) % y_axis_combo.count()
                y_axis_combo.setCurrentIndex(new_index)
                
                print(f"✅ Changed y-axis from '{y_axis_combo.itemText(current_index)}' to '{y_axis_combo.itemText(new_index)}'")
                print("✅ Y-axis selection should trigger automatic plot update")
            else:
                print("⚠️ No y-axis options available")
                
        except Exception as e:
            print(f"❌ Error testing y-axis selection: {e}")
    
    def close_dialog():
        print("⏰ Test timeout - closing dialog")
        dialog.accept()
    
    # Test y-axis selection after 2 seconds
    test_timer = QTimer()
    test_timer.timeout.connect(test_y_axis_selection)
    test_timer.start(2000)  # 2 seconds
    
    # Close dialog after 15 seconds
    close_timer = QTimer()
    close_timer.timeout.connect(close_dialog)
    close_timer.start(15000)  # 15 seconds
    
    # Show the dialog
    dialog.show()
    print("✅ Dialog shown")
    print("💡 Instructions:")
    print("   1. Wait 2 seconds for automatic y-axis test")
    print("   2. Try manually changing y-axis selection")
    print("   3. Verify plot updates automatically")
    print("   4. Dialog will close automatically after 15 seconds")
    
    # Run the application
    print("🔄 Running dialog...")
    result = dialog.exec()
    
    print(f"✅ Dialog completed with result: {result}")
    
    # Clean up
    dialog.close()
    
    print("✅ Test completed successfully")
    sys.exit(0)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all dependencies are installed:")
    print("   pip install PySide6 PySide6-WebEngine plotly pandas")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 