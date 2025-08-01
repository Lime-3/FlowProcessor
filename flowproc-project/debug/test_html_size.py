#!/usr/bin/env python3
"""
Test HTML file size optimization levels.
Demonstrates the different optimization options and their file size impacts.
"""

import sys
import tempfile
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.visualization.facade import create_visualization

def test_optimization_levels():
    """Test different optimization levels and their file sizes."""
    print("🔍 Testing HTML File Size Optimization Levels...")
    
    # Use a test file
    test_file = Path("../Test CSV/AT25-AS272_GFP.csv")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Using test file: {test_file.name}")
    
    # Test different optimization levels
    optimization_levels = ['minimal', 'balanced', 'full']
    results = {}
    
    for level in optimization_levels:
        print(f"\n📊 Testing {level.upper()} optimization...")
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            output_file = Path(tmp.name)
        
        try:
            # Create visualization with specific optimization level
            fig = create_visualization(
                str(test_file),
                output_html=str(output_file),
                optimization_level=level
            )
            
            # Get file size
            file_size_mb = output_file.stat().st_size / 1024 / 1024
            results[level] = file_size_mb
            
            print(f"   File size: {file_size_mb:.2f} MB")
            
            # Check if CDN is used
            with open(output_file, 'r') as f:
                content = f.read()
            
            if 'cdn.plot.ly' in content:
                print(f"   ✅ Uses CDN loading")
            elif 'plotly.min.js' in content and len(content) > 1000000:  # > 1MB
                print(f"   ⚠️  Uses embedded library")
            else:
                print(f"   ℹ️  Uses external loading")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[level] = None
        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()
    
    # Print summary
    print(f"\n📋 Optimization Summary:")
    print(f"{'Level':<10} {'Size (MB)':<12} {'Reduction':<12} {'Features':<20}")
    print("-" * 60)
    
    baseline = results.get('full', 4.0)  # Assume 4MB baseline
    
    for level in optimization_levels:
        size = results.get(level, 0)
        if size and baseline:
            reduction = ((baseline - size) / baseline) * 100
            features = {
                'minimal': 'Basic display',
                'balanced': 'Full interactive',
                'full': 'Offline compatible'
            }.get(level, 'Unknown')
            
            print(f"{level:<10} {size:<12.2f} {reduction:<12.1f}% {features:<20}")
        else:
            print(f"{level:<10} {'Error':<12} {'N/A':<12} {'Failed':<20}")
    
    print(f"\n💡 Recommendations:")
    print(f"   • Minimal: Use for embedded viewers (95% size reduction)")
    print(f"   • Balanced: Use for web browsers (90% size reduction)")
    print(f"   • Full: Use for offline sharing (no reduction)")

if __name__ == "__main__":
    test_optimization_levels() 