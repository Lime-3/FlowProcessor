#!/usr/bin/env python3
"""
Detailed HTML analysis to identify specific components causing large file sizes.
"""

import sys
import tempfile
from pathlib import Path
import re
import json

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.visualization.flow_cytometry_visualizer import plot

def analyze_html_content_detailed(html_content: str) -> dict:
    """Perform detailed analysis of HTML content."""
    
    analysis = {
        'total_size': len(html_content),
        'total_size_mb': len(html_content) / 1024 / 1024,
        'components': {}
    }
    
    # Look for specific components
    components = {
        'plotly_js_library': {
            'pattern': r'<script[^>]*>.*?var Plotly.*?</script>',
            'description': 'Embedded Plotly.js library'
        },
        'plotly_newplot_call': {
            'pattern': r'Plotly\.newPlot\([^)]*\)',
            'description': 'Plotly.newPlot function call'
        },
        'plotly_data_array': {
            'pattern': r'\[.*?\]',
            'description': 'Data arrays in Plotly calls'
        },
        'plotly_layout_object': {
            'pattern': r'\{.*?\}',
            'description': 'Layout objects in Plotly calls'
        },
        'html_structure': {
            'pattern': r'<[^>]+>',
            'description': 'HTML tags'
        },
        'css_styles': {
            'pattern': r'<style[^>]*>.*?</style>',
            'description': 'CSS style blocks'
        }
    }
    
    for component_name, config in components.items():
        matches = re.findall(config['pattern'], html_content, re.DOTALL)
        total_size = sum(len(match) for match in matches)
        
        analysis['components'][component_name] = {
            'description': config['description'],
            'matches_count': len(matches),
            'total_size': total_size,
            'size_mb': total_size / 1024 / 1024,
            'percentage': (total_size / len(html_content)) * 100,
            'largest_match': max(len(match) for match in matches) if matches else 0,
            'sample_content': matches[0][:500] + '...' if matches and len(matches[0]) > 500 else (matches[0] if matches else '')
        }
    
    return analysis

def find_plotly_js_embedding(html_content: str) -> dict:
    """Find and analyze Plotly.js embedding."""
    
    # Look for the main Plotly.js script tag
    plotly_script_pattern = r'<script[^>]*>.*?var Plotly.*?</script>'
    plotly_matches = re.findall(plotly_script_pattern, html_content, re.DOTALL)
    
    if plotly_matches:
        plotly_script = plotly_matches[0]
        
        # Analyze the Plotly.js content
        analysis = {
            'found': True,
            'script_size': len(plotly_script),
            'script_size_mb': len(plotly_script) / 1024 / 1024,
            'percentage_of_total': (len(plotly_script) / len(html_content)) * 100,
            'content_preview': plotly_script[:1000] + '...' if len(plotly_script) > 1000 else plotly_script
        }
        
        # Look for specific parts within Plotly.js
        plotly_parts = {
            'plotly_version': re.search(r'Plotly\.version\s*=\s*["\']([^"\']+)["\']', plotly_script),
            'plotly_license': re.search(r'Plotly\.LICENSE\s*=\s*["\']([^"\']+)["\']', plotly_script),
            'plotly_modules': re.findall(r'Plotly\.register\([^)]+\)', plotly_script),
        }
        
        analysis['parts'] = plotly_parts
        
        return analysis
    else:
        return {'found': False}

def analyze_plotly_data_structure_detailed(html_content: str) -> dict:
    """Analyze the Plotly data structure in detail."""
    
    # Find the Plotly.newPlot call
    newplot_pattern = r'Plotly\.newPlot\([^,]*,\s*(\[.*?\]),\s*(\{.*?\})\)'
    newplot_matches = re.findall(newplot_pattern, html_content, re.DOTALL)
    
    if newplot_matches:
        data_json, layout_json = newplot_matches[0]
        
        try:
            data = json.loads(data_json)
            layout = json.loads(layout_json)
            
            analysis = {
                'data_size': len(data_json),
                'data_size_mb': len(data_json) / 1024 / 1024,
                'layout_size': len(layout_json),
                'layout_size_mb': len(layout_json) / 1024 / 1024,
                'total_plotly_data_size': len(data_json) + len(layout_json),
                'total_plotly_data_size_mb': (len(data_json) + len(layout_json)) / 1024 / 1024,
                'traces_count': len(data),
                'trace_details': []
            }
            
            for i, trace in enumerate(data):
                trace_size = len(json.dumps(trace))
                trace_analysis = {
                    'index': i,
                    'type': trace.get('type', 'unknown'),
                    'size': trace_size,
                    'size_kb': trace_size / 1024,
                    'keys': list(trace.keys()),
                    'data_points': len(trace.get('x', [])) if isinstance(trace.get('x'), list) else 0
                }
                analysis['trace_details'].append(trace_analysis)
            
            return analysis
            
        except json.JSONDecodeError as e:
            return {
                'error': f'Failed to parse JSON: {e}',
                'data_preview': data_json[:500] + '...' if len(data_json) > 500 else data_json,
                'layout_preview': layout_json[:500] + '...' if len(layout_json) > 500 else layout_json
            }
    
    return {'error': 'No Plotly.newPlot call found'}

def main():
    """Perform detailed HTML analysis."""
    print("🔍 Performing detailed HTML analysis...")
    
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
        
        # Detailed component analysis
        print("\n📋 Detailed Component Analysis:")
        component_analysis = analyze_html_content_detailed(html_content)
        
        for component_name, info in component_analysis['components'].items():
            if info['total_size'] > 0:
                print(f"   {component_name}:")
                print(f"     Description: {info['description']}")
                print(f"     Size: {info['size_mb']:.2f} MB ({info['percentage']:.1f}%)")
                print(f"     Matches: {info['matches_count']}")
                print(f"     Largest match: {info['largest_match'] / 1024 / 1024:.2f} MB")
        
        # Plotly.js embedding analysis
        print("\n🔧 Plotly.js Embedding Analysis:")
        js_analysis = find_plotly_js_embedding(html_content)
        
        if js_analysis['found']:
            print(f"   ✅ Plotly.js found")
            print(f"   📦 Script size: {js_analysis['script_size_mb']:.2f} MB ({js_analysis['percentage_of_total']:.1f}%)")
            
            if 'parts' in js_analysis:
                parts = js_analysis['parts']
                if parts['plotly_version']:
                    print(f"   📋 Version: {parts['plotly_version'].group(1)}")
                if parts['plotly_modules']:
                    print(f"   🔌 Modules: {len(parts['plotly_modules'])} registered")
        else:
            print("   ❌ Plotly.js not found")
        
        # Plotly data structure analysis
        print("\n📊 Plotly Data Structure Analysis:")
        data_analysis = analyze_plotly_data_structure_detailed(html_content)
        
        if 'error' not in data_analysis:
            print(f"   📈 Data size: {data_analysis['data_size_mb']:.2f} MB")
            print(f"   🎨 Layout size: {data_analysis['layout_size_mb']:.2f} MB")
            print(f"   📊 Total Plotly data: {data_analysis['total_plotly_data_size_mb']:.2f} MB")
            print(f"   🔢 Traces: {data_analysis['traces_count']}")
            
            for trace in data_analysis['trace_details']:
                print(f"     Trace {trace['index']}: {trace['type']} - {trace['size_kb']:.1f}KB ({trace['data_points']} points)")
        else:
            print(f"   ❌ {data_analysis['error']}")
        
        # Summary and recommendations
        print("\n💡 Summary and Recommendations:")
        
        total_size = component_analysis['total_size_mb']
        plotly_js_size = component_analysis['components'].get('plotly_js_library', {}).get('size_mb', 0)
        plotly_data_size = data_analysis.get('total_plotly_data_size_mb', 0) if 'error' not in data_analysis else 0
        
        print(f"   📊 Total file size: {total_size:.2f} MB")
        print(f"   📦 Plotly.js library: {plotly_js_size:.2f} MB ({(plotly_js_size/total_size)*100:.1f}%)")
        print(f"   📈 Plotly data: {plotly_data_size:.2f} MB ({(plotly_data_size/total_size)*100:.1f}%)")
        
        if plotly_js_size > 3:
            print("   ⚠️  Plotly.js library is the main contributor to file size")
            print("   💡 Recommendation: Use CDN instead of embedding")
        
        if plotly_data_size > 1:
            print("   ⚠️  Plotly data is substantial")
            print("   💡 Recommendation: Consider data compression or sampling")
        
        # Clean up
        output_html.unlink()
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 