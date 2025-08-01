#!/usr/bin/env python3
"""
Test script to verify visualization options dialog functionality.
"""

import sys
import time
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PySide6.QtWidgets import QApplication
    from flowproc.presentation.gui.views.dialogs.visualization_options_dialog import VisualizationOptionsDialog
    
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
    print("🚀 Opening visualization options dialog...")
    dialog = VisualizationOptionsDialog(csv_path=csv_path)
    
    # Set up a timer to close the dialog after 10 seconds for testing
    from PySide6.QtCore import QTimer
    
    def close_dialog():
        print("⏰ Test timeout - closing dialog")
        dialog.accept()
    
    timer = QTimer()
    timer.timeout.connect(close_dialog)
    timer.start(10000)  # 10 seconds
    
    # Show the dialog
    print("✅ Dialog shown")
    
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