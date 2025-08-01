#!/usr/bin/env python3
"""
Dependency Analysis Viewer

This script helps explore and view the generated dependency analysis files.
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def list_generated_files():
    """List all generated dependency analysis files."""
    files = {
        'Visualizations (PNG)': [],
        'Reports (MD)': [],
        'Data (JSON)': [],
        'Source (DOT)': []
    }
    
    for file in Path('.').glob('*'):
        if file.suffix == '.png' and 'dependency' in file.name.lower():
            files['Visualizations (PNG)'].append(file.name)
        elif file.suffix == '.md' and 'dependency' in file.name.lower():
            files['Reports (MD)'].append(file.name)
        elif file.suffix == '.json' and 'dependency' in file.name.lower():
            files['Data (JSON)'].append(file.name)
        elif file.suffix == '.dot' and 'dependency' in file.name.lower():
            files['Source (DOT)'].append(file.name)
    
    return files

def show_project_info():
    """Show basic project information from the analysis."""
    try:
        with open('advanced_dependency_analysis.json', 'r') as f:
            data = json.load(f)
        
        info = data.get('project_info', {})
        print("📊 Project Information:")
        print(f"   Name: {info.get('name', 'N/A')}")
        print(f"   Total Modules: {info.get('total_modules', 'N/A')}")
        print(f"   Total Dependencies: {info.get('total_dependencies', 'N/A')}")
        print(f"   Total Functions: {info.get('total_functions', 'N/A')}")
        print(f"   Total Classes: {info.get('total_classes', 'N/A')}")
        
        # Show architecture layers
        layers = data.get('architecture_layers', {})
        print("\n🏗️  Architecture Layers:")
        for layer, modules in layers.items():
            print(f"   {layer.upper()}: {len(modules)} modules")
            
    except FileNotFoundError:
        print("❌ Analysis data not found. Run the analysis first.")
    except Exception as e:
        print(f"❌ Error reading analysis data: {e}")

def show_top_dependencies():
    """Show the most dependent modules."""
    try:
        with open('advanced_dependency_analysis.json', 'r') as f:
            data = json.load(f)
        
        deps = data.get('module_dependencies', {})
        
        # Count dependents for each module
        dependent_counts = {}
        for module, dependencies in deps.items():
            for dep in dependencies:
                dependent_counts[dep] = dependent_counts.get(dep, 0) + 1
        
        # Sort by count
        sorted_deps = sorted(dependent_counts.items(), key=lambda x: x[1], reverse=True)
        
        print("🔗 Most Dependent Modules:")
        for module, count in sorted_deps[:10]:
            print(f"   {module}: {count} dependents")
            
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

def show_menu():
    """Show the main menu."""
    print("\n" + "="*60)
    print("🔍 FlowProcessor Dependency Analysis Viewer")
    print("="*60)
    
    files = list_generated_files()
    
    print("\n📁 Generated Files:")
    for category, file_list in files.items():
        if file_list:
            print(f"\n{category}:")
            for i, file in enumerate(file_list, 1):
                print(f"   {i}. {file}")
    
    print("\n🎯 Quick Actions:")
    print("   1. Show project information")
    print("   2. Show top dependencies")
    print("   3. Open layered architecture visualization")
    print("   4. Open service dependencies visualization")
    print("   5. Open pydeps dependency map")
    print("   6. View comprehensive summary")
    print("   7. List all files")
    print("   0. Exit")
    
    return files

def main():
    """Main function."""
    while True:
        files = show_menu()
        
        try:
            choice = input("\nEnter your choice (0-7): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                show_project_info()
            elif choice == '2':
                show_top_dependencies()
            elif choice == '3':
                open_visualization('layered_architecture.png')
            elif choice == '4':
                open_visualization('service_dependencies.png')
            elif choice == '5':
                open_visualization('flowproc_dependencies.png')
            elif choice == '6':
                if os.path.exists('DEPENDENCY_ANALYSIS_SUMMARY.md'):
                    try:
                        with open('DEPENDENCY_ANALYSIS_SUMMARY.md', 'r') as f:
                            content = f.read()
                        print("\n" + "="*60)
                        print("📋 DEPENDENCY ANALYSIS SUMMARY")
                        print("="*60)
                        print(content[:2000] + "..." if len(content) > 2000 else content)
                    except Exception as e:
                        print(f"❌ Error reading summary: {e}")
                else:
                    print("❌ Summary file not found")
            elif choice == '7':
                print("\n📁 All Generated Files:")
                for category, file_list in files.items():
                    if file_list:
                        print(f"\n{category}:")
                        for file in file_list:
                            size = os.path.getsize(file) if os.path.exists(file) else 0
                            print(f"   {file} ({size:,} bytes)")
            else:
                print("❌ Invalid choice. Please enter 0-7.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 