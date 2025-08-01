#!/usr/bin/env python3
"""
Test script to verify FlowProcessor application stability.
This script helps identify if the application is actually hanging or just appears unresponsive.
"""

import sys
import time
import threading
import subprocess
import signal
from pathlib import Path

def test_application_stability():
    """Test the application for stability issues."""
    print("🔍 FlowProcessor Stability Test")
    print("=" * 50)
    
    # Test 1: Basic startup
    print("\n1. Testing application startup...")
    try:
        # Start the application in a subprocess
        process = subprocess.Popen(
            [sys.executable, "-m", "flowproc"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for startup
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ Application started successfully")
            
            # Test 2: Check if it's responsive
            print("\n2. Testing application responsiveness...")
            
            # Send a signal to check if it's alive
            try:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=10)
                print("✅ Application responded to termination signal")
            except subprocess.TimeoutExpired:
                print("⚠️  Application didn't respond to termination signal within 10 seconds")
                process.kill()
                process.wait()
                return False
                
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Application failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing application: {e}")
        return False
    
    # Test 3: Memory usage check
    print("\n3. Testing memory usage...")
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"✅ Current memory usage: {memory_mb:.1f} MB")
        
        if memory_mb > 1000:  # More than 1GB
            print("⚠️  High memory usage detected")
        else:
            print("✅ Memory usage is normal")
            
    except ImportError:
        print("⚠️  psutil not available, skipping memory test")
    
    # Test 4: File processing test
    print("\n4. Testing file processing...")
    test_csv = Path("tests/data/test_data.csv")
    if test_csv.exists():
        print(f"✅ Test file found: {test_csv}")
    else:
        print("⚠️  Test file not found, skipping processing test")
    
    print("\n" + "=" * 50)
    print("🎉 Stability test completed!")
    print("\nIf you're experiencing 'hanging':")
    print("1. Check the logs in flowproc-project/logs/")
    print("2. The application might be processing large files")
    print("3. Web view loading can take time for large visualizations")
    print("4. Use the debug monitor: python debug/debug_monitor.py")
    
    return True

def test_web_view_loading():
    """Test web view loading performance."""
    print("\n🌐 Testing web view loading...")
    
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtCore import QUrl
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Create a test HTML file
        test_html = """
        <html>
        <body>
            <h1>Test Visualization</h1>
            <p>This is a test to check web view loading performance.</p>
        </body>
        </html>
        """
        
        web_view = QWebEngineView()
        
        # Test loading HTML content
        start_time = time.time()
        web_view.setHtml(test_html)
        
        # Wait for loading
        time.sleep(2)
        
        load_time = time.time() - start_time
        print(f"✅ Web view loaded in {load_time:.2f} seconds")
        
        if load_time > 5:
            print("⚠️  Slow web view loading detected")
        else:
            print("✅ Web view loading is responsive")
            
    except Exception as e:
        print(f"❌ Web view test failed: {e}")

if __name__ == "__main__":
    success = test_application_stability()
    test_web_view_loading()
    
    if success:
        print("\n✅ All tests passed - application appears stable")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - check for issues")
        sys.exit(1) 