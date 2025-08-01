#!/usr/bin/env python3
"""
Test script to check if PySide6 WebEngine is working properly.
"""

import sys
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtCore import QUrl
    import tempfile
    
    print("✅ PySide6 imports successful")
    
    # Create a simple HTML file
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Visualization</title>
        <style>
            body { 
                background-color: #2b2b2b; 
                color: #ffffff; 
                font-family: Arial, sans-serif; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                margin: 0; 
            }
            .content { text-align: center; }
        </style>
    </head>
    <body>
        <div class="content">
            <h3>Test Visualization</h3>
            <p>If you can see this, the WebEngine is working!</p>
            <p>This is a test page to verify the web view component.</p>
        </div>
    </body>
    </html>
    """
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
        tmp_file.write(html_content)
        html_path = Path(tmp_file.name)
    
    print(f"✅ Created test HTML file: {html_path}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    print("✅ QApplication created")
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("WebEngine Test")
    window.resize(800, 600)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    # Create layout
    layout = QVBoxLayout(central_widget)
    
    # Create web view
    web_view = QWebEngineView()
    web_view.setMinimumHeight(400)
    layout.addWidget(web_view)
    
    print("✅ WebEngineView created")
    
    # Load the HTML file
    file_url = QUrl.fromLocalFile(str(html_path))
    print(f"✅ Loading URL: {file_url}")
    
    web_view.load(file_url)
    
    # Show the window
    window.show()
    print("✅ Window shown")
    
    # Run the application
    print("🚀 Starting application...")
    result = app.exec()
    
    # Clean up
    if html_path.exists():
        html_path.unlink()
    
    print("✅ Test completed successfully")
    sys.exit(result)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure PySide6 and PySide6-WebEngine are installed:")
    print("   pip install PySide6 PySide6-WebEngine")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 