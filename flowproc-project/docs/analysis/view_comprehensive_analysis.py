#!/usr/bin/env python3
"""
Comprehensive Dependency Analysis Viewer

This script helps explore and view the generated comprehensive dependency analysis files.
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def list_generated_files():
    """List all generated comprehensive dependency analysis files."""
    files = {
        'Visualizations (PNG)': [],
        'Reports (JSON/MD)': [],
        'Analysis Tool': []
    }
    
    for file in Path('.').glob('*'):
        if file.suffix == '.png' and any(keyword in file.name.lower() for keyword in ['module_dependency', 'function_call', 'full_application']):
            files['Visualizations (PNG)'].append(file.name)
        elif file.suffix in ['.json', '.md'] and any(keyword in file.name.lower() for keyword in ['comprehensive', 'dependency']):
            files['Reports (JSON/MD)'].append(file.name)
        elif file.name == 'comprehensive_dependency_analyzer.py':
            files['Analysis Tool'].append(file.name)
    
    return files

def show_project_statistics():
    """Show key statistics from the comprehensive analysis."""
    try:
        with open('comprehensive_dependency_report.json', 'r') as f:
            data = json.load(f)
        
        stats = data.get('statistics', {})
        project_info = data.get('project_info', {})
        
        print("📊 Comprehensive Dependency Analysis Statistics:")
        print("=" * 50)
        print(f"   Total Modules: {project_info.get('total_modules', 'N/A')}")
        print(f"   Total Functions: {project_info.get('total_functions', 'N/A')}")
        print(f"   Total Classes: {project_info.get('total_classes', 'N/A')}")
        print(f"   Total Dependencies: {stats.get('total_dependencies', 'N/A')}")
        print(f"   Avg Dependencies per Module: {stats.get('avg_dependencies_per_module', 'N/A'):.2f}")
        
        print("\n🏗️  Architecture Layer Distribution:")
        modules_per_layer = stats.get('modules_per_layer', {})
        for layer, count in modules_per_layer.items():
            percentage = (count / project_info.get('total_modules', 1)) * 100
            print(f"   {layer.title()}: {count} modules ({percentage:.1f}%)")
        
        print("\n🔗 Most Dependent Modules:")
        most_dependent = stats.get('most_dependent_modules', [])
        for i, (module, count) in enumerate(most_dependent[:5], 1):
            print(f"   {i}. {module}: {count} dependencies")
            
    except FileNotFoundError:
        print("❌ Comprehensive analysis data not found. Run the analysis first.")
    except Exception as e:
        print(f"❌ Error reading analysis data: {e}")

def show_cross_layer_dependencies():
    """Show cross-layer dependency analysis."""
    try:
        with open('comprehensive_dependency_report.json', 'r') as f:
            data = json.load(f)
        
        cross_deps = data.get('cross_layer_dependencies', {})
        
        if not cross_deps:
            print("ℹ️  No cross-layer dependencies found.")
            return
        
        print("🔗 Cross-Layer Dependencies:")
        print("=" * 40)
        
        for dep_type, dependencies in cross_deps.items():
            print(f"\n{dep_type.replace('_', ' → ').title()}:")
            for source, target in dependencies[:5]:  # Show first 5
                print(f"   {source} → {target}")
            if len(dependencies) > 5:
                print(f"   ... and {len(dependencies) - 5} more")
                
    except FileNotFoundError:
        print("❌ Analysis data not found.")
    except Exception as e:
        print(f"❌ Error reading dependency data: {e}")

def open_visualization(filename):
    """Open a visualization file."""
    if os.path.exists(filename):
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(['open', filename])
            elif sys.platform == "win32":  # Windows
                subprocess.run(['start', filename], shell=True)
            else:  # Linux
                subprocess.run(['xdg-open', filename])
            print(f"✅ Opened {filename}")
        except Exception as e:
            print(f"❌ Error opening {filename}: {e}")
    else:
        print(f"❌ File {filename} not found")

def show_visualization_info():
    """Show information about the generated visualizations."""
    print("📊 Generated Visualizations:")
    print("=" * 30)
    
    visualizations = {
        'module_dependency_map.png': {
            'title': 'Module Dependency Map',
            'description': 'Shows which modules import/use other modules with color-coded layers',
            'focus': 'Import relationships and layer separation'
        },
        'function_call_graph.png': {
            'title': 'Function Call Graph', 
            'description': 'Shows which functions call or are called by other functions',
            'focus': 'Function-level dependencies and call hierarchy'
        },
        'full_application_graph.png': {
            'title': 'Full Application Graph',
            'description': 'Complete application architecture with all relationship types',
            'focus': 'Comprehensive view of modules, functions, and their relationships'
        }
    }
    
    for filename, info in visualizations.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename) / (1024 * 1024)  # MB
            print(f"\n📁 {info['title']}")
            print(f"   File: {filename} ({size:.1f} MB)")
            print(f"   Description: {info['description']}")
            print(f"   Focus: {info['focus']}")
        else:
            print(f"\n❌ {filename} - Not found")

def show_menu():
    """Show the main menu."""
    print("\n" + "=" * 60)
    print("🔍 Comprehensive Dependency Analysis Viewer")
    print("=" * 60)
    print("1. Show project statistics")
    print("2. Show cross-layer dependencies")
    print("3. Show visualization information")
    print("4. Open module dependency map")
    print("5. Open function call graph")
    print("6. Open full application graph")
    print("7. List all generated files")
    print("8. Regenerate analysis")
    print("0. Exit")
    print("=" * 60)

def regenerate_analysis():
    """Regenerate the comprehensive analysis."""
    print("🔄 Regenerating comprehensive dependency analysis...")
    try:
        result = subprocess.run(['python', 'comprehensive_dependency_analyzer.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Analysis regenerated successfully!")
            print(result.stdout)
        else:
            print("❌ Error regenerating analysis:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error running analysis: {e}")

def main():
    """Main entry point."""
    print("🔍 Comprehensive Dependency Analysis Viewer")
    print("Loading analysis data...")
    
    while True:
        show_menu()
        choice = input("\nEnter your choice (0-8): ").strip()
        
        if choice == '0':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            show_project_statistics()
        elif choice == '2':
            show_cross_layer_dependencies()
        elif choice == '3':
            show_visualization_info()
        elif choice == '4':
            open_visualization('module_dependency_map.png')
        elif choice == '5':
            open_visualization('function_call_graph.png')
        elif choice == '6':
            open_visualization('full_application_graph.png')
        elif choice == '7':
            files = list_generated_files()
            for category, file_list in files.items():
                print(f"\n{category}:")
                for file in file_list:
                    print(f"   {file}")
        elif choice == '8':
            regenerate_analysis()
        else:
            print("❌ Invalid choice. Please enter a number between 0 and 8.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 