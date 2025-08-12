#!/usr/bin/env python3
"""
Analyze HTML file size breakdown to understand why Plotly files are so large.
"""

import sys
import tempfile
from pathlib import Path
import re
import gzip
import json

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.visualization.flow_cytometry_visualizer import plot

def analyze_html_structure(html_content: str) -> dict:
    """Analyze the structure and size breakdown of HTML content."""
    
    analysis = {
        'total_size': len(html_content),
        'total_size_mb': len(html_content) / 1024 / 1024,
        'sections': {},
        'compression': {}
    }
    
    # Analyze different sections
    sections = {
        'html_head': re.search(r'<head>(.*?)</head>', html_content, re.DOTALL),
        'plotly_js': re.search(r'<script[^>]*plotly[^>]*>(.*?)</script>', html_content, re.DOTALL),
        'plotly_config': re.search(r'Plotly\.newPlot\([^,]*,\s*(\[.*?\]),\s*(\{.*?\})', html_content, re.DOTALL),
        'plotly_data': re.search(r'Plotly\.newPlot\([^,]*,\s*(\[.*?\])', html_content, re.DOTALL),
        'css_styles': re.search(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL),
        'body_content': re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
    }
    
    for section_name, match in sections.items():
        if match:
            content = match.group(1) if match.groups() else match.group(0)
            size = len(content)
            analysis['sections'][section_name] = {
                'size_bytes': size,
                'size_mb': size / 1024 / 1024,
                'percentage': (size / len(html_content)) * 100,
                'content_preview': content[:200] + '...' if len(content) > 200 else content
            }
    
    # Analyze compression potential
    original_size = len(html_content)
    compressed_size = len(gzip.compress(html_content.encode('utf-8')))
    
    analysis['compression'] = {
        'original_size_mb': original_size / 1024 / 1024,
        'compressed_size_mb': compressed_size / 1024 / 1024,
        'compression_ratio': compressed_size / original_size,
        'space_saved_mb': (original_size - compressed_size) / 1024 / 1024
    }
    
    return analysis

def analyze_plotly_data_structure(html_content: str) -> dict:
    """Analyze the Plotly data structure specifically."""
    
    # Find Plotly.newPlot calls
    plotly_calls = re.findall(r'Plotly\.newPlot\([^,]*,\s*(\[.*?\])', html_content, re.DOTALL)
    
    data_analysis = {
        'plotly_calls_count': len(plotly_calls),
        'data_structures': []
    }
    
    for i, data_json in enumerate(plotly_calls):
        try:
            # Try to parse the JSON data
            data = json.loads(data_json)
            
            structure_info = {
                'call_index': i,
                'traces_count': len(data),
                'total_points': 0,
                'trace_types': [],
                'trace_sizes': []
            }
            
            for trace in data:
                trace_type = trace.get('type', 'unknown')
                structure_info['trace_types'].append(trace_type)
                
                # Count data points
                if 'x' in trace and 'y' in trace:
                    points = len(trace['x']) if isinstance(trace['x'], list) else 1
                    structure_info['total_points'] += points
                
                # Estimate trace size
                trace_size = len(json.dumps(trace))
                structure_info['trace_sizes'].append(trace_size)
            
            data_analysis['data_structures'].append(structure_info)
            
        except json.JSONDecodeError:
            data_analysis['data_structures'].append({
                'call_index': i,
                'error': 'Failed to parse JSON',
                'raw_size': len(data_json)
            })
    
    return data_analysis

def analyze_plotly_js_embedding(html_content: str) -> dict:
    """Analyze the embedded Plotly.js library."""
    
    # Look for embedded Plotly.js
    plotly_js_patterns = [
        r'<script[^>]*src="[^"]*plotly[^"]*"[^>]*></script>',  # CDN links
        r'<script[^>]*>.*?plotly.*?</script>',  # Embedded script
        r'var Plotly = [^;]+;',  # Plotly variable definition
    ]
    
    js_analysis = {
        'embedding_method': 'unknown',
        'plotly_js_size': 0,
        'plotly_js_size_mb': 0,
        'cdn_links': [],
        'embedded_scripts': []
    }
    
    # Check for CDN links
    cdn_matches = re.findall(r'<script[^>]*src="([^"]*plotly[^"]*)"[^>]*>', html_content)
    if cdn_matches:
        js_analysis['embedding_method'] = 'cdn'
        js_analysis['cdn_links'] = cdn_matches
    
    # Check for embedded Plotly.js
    embedded_matches = re.findall(r'<script[^>]*>(.*?plotly.*?)</script>', html_content, re.DOTALL | re.IGNORECASE)
    if embedded_matches:
        js_analysis['embedding_method'] = 'embedded'
        total_js_size = sum(len(match) for match in embedded_matches)
        js_analysis['plotly_js_size'] = total_js_size
        js_analysis['plotly_js_size_mb'] = total_js_size / 1024 / 1024
        js_analysis['embedded_scripts'] = [match[:200] + '...' for match in embedded_matches]
    
    return js_analysis

def main():
    """Analyze HTML file size breakdown."""
    print("🔍 Analyzing HTML file size breakdown...")
    
    # Find a test CSV file
    test_csv_dir = Path("../Test CSV")
    if not test_csv_dir.exists():
        test_csv_dir = Path("../../Test CSV")
    
    if not test_csv_dir.exists():
        print("❌ Could not find Test CSV directory")
        return
    
    csv_files = list(test_csv_dir.glob("*.csv"))
    if not csv_files:
        print("❌ No CSV files found in Test CSV directory")
        return
    
    csv_path = csv_files[0]
    print(f"📁 Using test file: {csv_path.name}")
    
    try:
        # Create visualization
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            output_html = Path(tmp_file.name)
        
        # Create visualization
        fig = plot(
            data_source=csv_path,
            metric="Freq. of Parent",
            output_html=output_html,
            time_course_mode=False,
            theme="default",
            width=800,
            height=600
        )
        
        # Read the HTML content
        with open(output_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"✅ Generated HTML file: {output_html}")
        print(f"📊 File size: {len(html_content) / 1024 / 1024:.2f} MB")
        
        # Analyze structure
        print("\n📋 HTML Structure Analysis:")
        structure_analysis = analyze_html_structure(html_content)
        
        print(f"   Total size: {structure_analysis['total_size_mb']:.2f} MB")
        print(f"   Compressed size: {structure_analysis['compression']['compressed_size_mb']:.2f} MB")
        print(f"   Compression ratio: {structure_analysis['compression']['compression_ratio']:.2%}")
        print(f"   Space saved with compression: {structure_analysis['compression']['space_saved_mb']:.2f} MB")
        
        print("\n📦 Section Breakdown:")
        for section_name, info in structure_analysis['sections'].items():
            print(f"   {section_name}: {info['size_mb']:.2f} MB ({info['percentage']:.1f}%)")
        
        # Analyze Plotly data
        print("\n📊 Plotly Data Analysis:")
        data_analysis = analyze_plotly_data_structure(html_content)
        print(f"   Plotly calls: {data_analysis['plotly_calls_count']}")
        
        for structure in data_analysis['data_structures']:
            if 'error' not in structure:
                print(f"   Call {structure['call_index']}: {structure['traces_count']} traces, {structure['total_points']} points")
                print(f"     Trace types: {structure['trace_types']}")
                print(f"     Trace sizes: {[f'{s/1024:.1f}KB' for s in structure['trace_sizes']]}")
            else:
                print(f"   Call {structure['call_index']}: {structure['error']}")
        
        # Analyze Plotly.js embedding
        print("\n🔧 Plotly.js Embedding Analysis:")
        js_analysis = analyze_plotly_js_embedding(html_content)
        print(f"   Embedding method: {js_analysis['embedding_method']}")
        
        if js_analysis['embedding_method'] == 'cdn':
            print(f"   CDN links: {js_analysis['cdn_links']}")
        elif js_analysis['embedding_method'] == 'embedded':
            print(f"   Embedded Plotly.js size: {js_analysis['plotly_js_size_mb']:.2f} MB")
        
        # Clean up
        output_html.unlink()
        
        print("\n💡 Key Findings:")
        if structure_analysis['total_size_mb'] > 4:
            print("   ⚠️  File is very large (>4MB)")
            if 'plotly_js' in structure_analysis['sections']:
                js_size = structure_analysis['sections']['plotly_js']['size_mb']
                print(f"   📦 Plotly.js library: {js_size:.2f} MB ({structure_analysis['sections']['plotly_js']['percentage']:.1f}%)")
            if 'plotly_data' in structure_analysis['sections']:
                data_size = structure_analysis['sections']['plotly_data']['size_mb']
                print(f"   📊 Data payload: {data_size:.2f} MB ({structure_analysis['sections']['plotly_data']['percentage']:.1f}%)")
        
        print(f"   🗜️  Compression could reduce size by {structure_analysis['compression']['space_saved_mb']:.2f} MB")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 