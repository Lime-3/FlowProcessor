#!/usr/bin/env python3
"""
Simple test script to check if QWebEngineView works properly.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

def test_webview():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("WebView Test")
    window.resize(800, 600)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    # Create web view
    web_view = QWebEngineView()
    layout.addWidget(web_view)
    
    # Load simple HTML file
    html_path = Path("test_simple.html")
    if html_path.exists():
        print(f"Loading HTML file: {html_path}")
        web_view.load(QUrl.fromLocalFile(str(html_path)))
    else:
        print("HTML file not found, loading simple HTML content")
        web_view.setHtml("<html><body><h1>Test</h1><p>This is a test</p></body></html>")
    
    # Show window
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_webview() 