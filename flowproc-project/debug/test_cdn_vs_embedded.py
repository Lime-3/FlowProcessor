#!/usr/bin/env python3
"""
Test script to compare CDN vs embedded Plotly.js file sizes.
"""

import sys
import tempfile
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.visualization.facade import create_visualization
from flowproc.domain.visualization.plotly_renderer import PlotlyRenderer

def test_cdn_vs_embedded():
    """Compare CDN vs embedded file sizes."""
    print("🔍 Testing CDN vs Embedded Plotly.js...")
    
    # Find a test CSV file
    test_csv_dir = Path("../Test CSV")
    if not test_csv_dir.exists():
        test_csv_dir = Path("../../Test CSV")
    
    if not test_csv_dir.exists():
        print("❌ Could not find Test CSV directory")
        return
    
    csv_files = list(test_csv_dir.glob("*.csv"))
    if not csv_files:
        print("❌ No CSV files found")
        return
    
    test_file = csv_files[0]
    print(f"📁 Using test file: {test_file.name}")
    
    # Create renderer
    renderer = PlotlyRenderer()
    
    # Test with CDN (current setting)
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_cdn:
        cdn_file = Path(tmp_cdn.name)
    
    # Test with embedded (old setting)
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp_embedded:
        embedded_file = Path(tmp_embedded.name)
    
    try:
        # Create visualization
        result = create_visualization(str(test_file))
        if result is None:
            print(f"❌ Failed to create visualization")
            return
        
        # Export with CDN
        renderer.export_to_html(result, str(cdn_file), include_plotlyjs=True)
        
        # Export with embedded (temporarily change the setting)
        original_export = renderer.export_to_html
        def export_embedded(fig, filepath, include_plotlyjs=True, full_html=True):
            fig.write_html(
                filepath,
                include_plotlyjs=True,  # Force embedded
                full_html=full_html,
                config=dict(
                    editable=True,
                    edits=dict(
                        axisTitleText=True,
                        titleText=True,
                        legendText=True
                    )
                )
            )
        
        renderer.export_to_html = export_embedded
        renderer.export_to_html(result, str(embedded_file), include_plotlyjs=True)
        renderer.export_to_html = original_export
        
        # Compare sizes
        cdn_size = cdn_file.stat().st_size / 1024 / 1024
        embedded_size = embedded_file.stat().st_size / 1024 / 1024
        
        print(f"\n📊 File Size Comparison:")
        print(f"   CDN Loading:     {cdn_size:.2f} MB")
        print(f"   Embedded:        {embedded_size:.2f} MB")
        print(f"   Size Reduction:  {((embedded_size - cdn_size) / embedded_size * 100):.1f}%")
        print(f"   Space Saved:     {embedded_size - cdn_size:.2f} MB")
        
        # Check if CDN file contains CDN link
        with open(cdn_file, 'r') as f:
            cdn_content = f.read()
        
        if 'cdn.plot.ly' in cdn_content:
            print(f"✅ CDN file correctly uses CDN loading")
        else:
            print(f"❌ CDN file still contains embedded library")
        
        if 'plotly.min.js' in cdn_content and len(cdn_content) > 1000000:
            print(f"❌ CDN file still contains embedded library (large size)")
        else:
            print(f"✅ CDN file is properly optimized")
            
    finally:
        # Cleanup
        cdn_file.unlink(missing_ok=True)
        embedded_file.unlink(missing_ok=True)

if __name__ == "__main__":
    test_cdn_vs_embedded() 