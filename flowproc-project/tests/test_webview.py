#!/usr/bin/env python3
"""
Test script to check if the web view is working properly.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QUrl

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_webview():
    """Test if web view is working."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Web View Test")
    window.resize(800, 600)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        print("✓ PySide6.QtWebEngineWidgets imported successfully")
        
        # Create web view
        web_view = QWebEngineView()
        layout.addWidget(web_view)
        
        # Load a simple HTML page
        test_html = """
        <html>
        <body style="background-color: #2b2b2b; color: #ffffff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
            <div style="text-align: center;">
                <h1>Web View Test</h1>
                <p>If you can see this, the web view is working!</p>
                <p>This is a test of the PySide6.QtWebEngineWidgets functionality.</p>
            </div>
        </body>
        </html>
        """
        
        web_view.setHtml(test_html)
        print("✓ Web view created and HTML loaded")
        
        # Show the window
        window.show()
        print("✓ Window displayed")
        
        # Set up a timer to close after 5 seconds
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(window.close)
        timer.start(5000)  # 5 seconds
        
        print("Window will close automatically in 5 seconds.")
        return app.exec()
        
    except ImportError as e:
        print(f"✗ Failed to import PySide6.QtWebEngineWidgets: {e}")
        print("This might be why plots aren't showing.")
        return 1
    except Exception as e:
        print(f"✗ Web view test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_webview()) 