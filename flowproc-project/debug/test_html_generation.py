#!/usr/bin/env python3
"""
Test HTML Generation - Verify CDN loading works correctly
"""

import sys
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.visualization.simple_visualizer import plot

def test_html_generation():
    """Test that HTML files are generated correctly with CDN loading."""
    print("🔍 Testing HTML Generation...")
    
    # Use a test file
    test_file = Path("../Test CSV/AT25-AS272_GFP.csv")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    try:
        # Generate HTML file
        output_file = Path("test_output.html")
        fig = plot(test_file, save_html=output_file)
        
        # Check if file was created
        if not output_file.exists():
            print("❌ HTML file was not created")
            return
        
        # Check file size
        file_size_mb = output_file.stat().st_size / 1024 / 1024
        print(f"✅ HTML file created: {file_size_mb:.3f} MB")
        
        # Check file content
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for CDN links
        if 'cdn.plot.ly' in content:
            print("✅ CDN link found in HTML")
        else:
            print("❌ CDN link not found in HTML")
        
        # Check for Plotly script
        if 'plotly-latest.min.js' in content:
            print("✅ Plotly script found in HTML")
        else:
            print("❌ Plotly script not found in HTML")
        
        # Check for fallback CDN
        if 'cdnjs.cloudflare.com' in content:
            print("✅ Fallback CDN found in HTML")
        else:
            print("❌ Fallback CDN not found in HTML")
        
        # Check for plotly div
        if '<div id="' in content:
            print("✅ Plotly div found in HTML")
        else:
            print("❌ Plotly div not found in HTML")
        
        print("\n🎉 HTML generation test completed!")
        
        # Clean up
        output_file.unlink()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_html_generation() 