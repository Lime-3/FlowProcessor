#!/usr/bin/env python3
"""
Comprehensive Dependency Analyzer for FlowProcessor Project

This script provides three types of dependency analysis:
1. Module dependency map (which modules import/use others)
2. Function call graph (which functions call or are called by others)
3. Full application graph (complete architecture with all relationships)

Features:
- Layered architecture visualization
- Service dependency tracking
- Function call tracing
- Class inheritance mapping
- Import relationship analysis
- Cross-layer dependency detection
"""

import os
import sys
import ast
import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Any, Optional
import subprocess
import tempfile
from datetime import datetime

class ComprehensiveDependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.flowproc_dir = self.project_root / "flowproc"
        
        # Data structures for different types of analysis
        self.module_dependencies = defaultdict(set)
        self.function_calls = defaultdict(set)
        self.class_inheritance = defaultdict(set)
        self.import_map = defaultdict(set)
        self.function_definitions = defaultdict(set)
        self.class_definitions = defaultdict(set)
        self.service_dependencies = defaultdict(set)
        self.layer_dependencies = defaultdict(set)
        
        # Architecture layers
        self.layers = {
            'presentation': ['presentation'],
            'application': ['application'],
            'domain': ['domain'],
            'infrastructure': ['infrastructure'],
            'core': ['core'],
            'shared': ['config', 'logging_config', 'resource_utils', 'setup_dependencies']
        }
        
        # Color scheme for layers
        self.layer_colors = {
            'presentation': '#FF6B6B',  # Red
            'application': '#4ECDC4',   # Teal
            'domain': '#45B7D1',        # Blue
            'infrastructure': '#96CEB4', # Green
            'core': '#FFEAA7',          # Yellow
            'shared': '#DDA0DD'         # Plum
        }
        
    def find_python_files(self, directory: Path) -> List[Path]:
        """Find all Python files in the directory recursively."""
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip __pycache__, .git, venv, etc.
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'build', '.pytest_cache', '.hypothesis']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files
    
    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        relative_path = file_path.relative_to(self.project_root)
        return str(relative_path).replace('/', '.').replace('\\', '.').replace('.py', '')
    
    def get_layer_for_module(self, module_name: str) -> str:
        """Determine which layer a module belongs to."""
        for layer, patterns in self.layers.items():
            for pattern in patterns:
                if pattern in module_name:
                    return layer
        return 'shared'
    
    def analyze_imports(self, file_path: Path) -> Set[str]:
        """Analyze imports in a Python file."""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
        except Exception as e:
            print(f"Error parsing imports in {file_path}: {e}")
            
        return imports
    
    def get_node_name(self, node) -> Optional[str]:
        """Safely get the name of an AST node."""
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    return f"{node.value.id}.{node.attr}"
                else:
                    base_name = self.get_node_name(node.value)
                    return f"{base_name}.{node.attr}" if base_name else None
            elif isinstance(node, ast.Call):
                return self.get_node_name(node.func)
            elif isinstance(node, ast.Subscript):
                return self.get_node_name(node.value)
            else:
                return None
        except:
            return None
    
    def analyze_function_calls(self, file_path: Path) -> Dict[str, Set[str]]:
        """Analyze function calls in a Python file."""
        calls = defaultdict(set)
        current_function = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Track current function
                if isinstance(node, ast.FunctionDef):
                    current_function = node.name
                elif isinstance(node, ast.AsyncFunctionDef):
                    current_function = node.name
                elif isinstance(node, ast.ClassDef):
                    current_function = f"{node.name}.__init__"
                
                # Track function calls
                if isinstance(node, ast.Call) and current_function:
                    func_name = self.get_node_name(node.func)
                    if func_name:
                        calls[current_function].add(func_name)
                        
        except Exception as e:
            print(f"Error parsing function calls in {file_path}: {e}")
            
        return calls
    
    def analyze_function_definitions(self, file_path: Path) -> Dict[str, List[str]]:
        """Analyze function definitions in a Python file."""
        functions = defaultdict(list)
        module_name = self.get_module_name(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions[module_name].append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions[module_name].append(f"async_{node.name}")
                    
        except Exception as e:
            print(f"Error parsing function definitions in {file_path}: {e}")
            
        return functions
    
    def analyze_class_inheritance(self, file_path: Path) -> Dict[str, List[str]]:
        """Analyze class inheritance in a Python file."""
        classes = defaultdict(list)
        module_name = self.get_module_name(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    base_classes = []
                    for base in node.bases:
                        base_name = self.get_node_name(base)
                        if base_name:
                            base_classes.append(base_name)
                    classes[module_name].append({
                        'name': node.name,
                        'bases': base_classes
                    })
                    
        except Exception as e:
            print(f"Error parsing class inheritance in {file_path}: {e}")
            
        return classes
    
    def build_module_dependency_map(self):
        """Build the module dependency map."""
        print("🔍 Building module dependency map...")
        
        python_files = self.find_python_files(self.flowproc_dir)
        
        for file_path in python_files:
            module_name = self.get_module_name(file_path)
            imports = self.analyze_imports(file_path)
            
            # Filter imports to only include project modules
            project_imports = set()
            for imp in imports:
                if imp.startswith('flowproc.'):
                    project_imports.add(imp)
                elif imp.startswith('flowproc'):
                    project_imports.add(imp)
            
            self.module_dependencies[module_name] = project_imports
            
        print(f"✅ Module dependency map built with {len(self.module_dependencies)} modules")
    
    def build_function_call_graph(self):
        """Build the function call graph."""
        print("🔍 Building function call graph...")
        
        python_files = self.find_python_files(self.flowproc_dir)
        
        for file_path in python_files:
            module_name = self.get_module_name(file_path)
            calls = self.analyze_function_calls(file_path)
            
            for func, called_funcs in calls.items():
                full_func_name = f"{module_name}.{func}"
                self.function_calls[full_func_name] = called_funcs
                
        print(f"✅ Function call graph built with {len(self.function_calls)} functions")
    
    def build_full_application_graph(self):
        """Build the complete application graph with all relationships."""
        print("🔍 Building full application graph...")
        
        # First build the basic dependency maps
        self.build_module_dependency_map()
        self.build_function_call_graph()
        
        # Analyze function definitions and class inheritance
        python_files = self.find_python_files(self.flowproc_dir)
        
        for file_path in python_files:
            module_name = self.get_module_name(file_path)
            
            # Function definitions
            func_defs = self.analyze_function_definitions(file_path)
            for mod, funcs in func_defs.items():
                self.function_definitions[mod].update(funcs)
            
            # Class inheritance
            class_inheritance = self.analyze_class_inheritance(file_path)
            for mod, classes in class_inheritance.items():
                self.class_definitions[mod].update([cls['name'] for cls in classes])
        
        print("✅ Full application graph built")
    
    def generate_module_dependency_visualization(self, filename: str = "module_dependency_map.png"):
        """Generate module dependency map visualization."""
        print(f"📊 Generating module dependency map: {filename}")
        
        G = nx.DiGraph()
        
        # Add nodes with layer information
        for module, deps in self.module_dependencies.items():
            layer = self.get_layer_for_module(module)
            G.add_node(module, layer=layer)
            
            for dep in deps:
                if dep in self.module_dependencies:  # Only include project modules
                    dep_layer = self.get_layer_for_module(dep)
                    G.add_node(dep, layer=dep_layer)
                    G.add_edge(module, dep)
        
        # Create visualization
        plt.figure(figsize=(20, 16))
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Draw nodes by layer
        for layer in self.layer_colors:
            layer_nodes = [n for n, d in G.nodes(data=True) if d.get('layer') == layer]
            nx.draw_networkx_nodes(G, pos, nodelist=layer_nodes, 
                                 node_color=self.layer_colors[layer], 
                                 node_size=1000, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                             arrowsize=20, alpha=0.6)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
        
        # Create legend
        legend_elements = [mpatches.Patch(color=color, label=layer.title()) 
                          for layer, color in self.layer_colors.items()]
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.title("Module Dependency Map", fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Module dependency map saved as {filename}")
    
    def generate_function_call_visualization(self, filename: str = "function_call_graph.png"):
        """Generate function call graph visualization."""
        print(f"📊 Generating function call graph: {filename}")
        
        G = nx.DiGraph()
        
        # Add nodes and edges
        for func, calls in self.function_calls.items():
            module = func.split('.')[0]
            layer = self.get_layer_for_module(module)
            G.add_node(func, layer=layer)
            
            for called_func in calls:
                # Try to resolve the called function to a project module
                if '.' in called_func:
                    called_module = called_func.split('.')[0]
                    if called_module in self.module_dependencies:
                        called_layer = self.get_layer_for_module(called_module)
                        G.add_node(called_func, layer=called_layer)
                        G.add_edge(func, called_func)
        
        # Create visualization
        plt.figure(figsize=(20, 16))
        pos = nx.spring_layout(G, k=2, iterations=30)
        
        # Draw nodes by layer
        for layer in self.layer_colors:
            layer_nodes = [n for n, d in G.nodes(data=True) if d.get('layer') == layer]
            nx.draw_networkx_nodes(G, pos, nodelist=layer_nodes, 
                                 node_color=self.layer_colors[layer], 
                                 node_size=500, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                             arrowsize=15, alpha=0.5)
        
        # Draw labels (only for important functions)
        important_funcs = [n for n in G.nodes() if G.degree(n) > 2]
        labels = {n: n.split('.')[-1] for n in important_funcs}
        nx.draw_networkx_labels(G, pos, labels, font_size=6, font_weight='bold')
        
        # Create legend
        legend_elements = [mpatches.Patch(color=color, label=layer.title()) 
                          for layer, color in self.layer_colors.items()]
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.title("Function Call Graph", fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Function call graph saved as {filename}")
    
    def generate_full_application_visualization(self, filename: str = "full_application_graph.png"):
        """Generate full application graph visualization."""
        print(f"📊 Generating full application graph: {filename}")
        
        G = nx.MultiDiGraph()  # MultiDiGraph to show different types of relationships
        
        # Add module nodes
        for module, deps in self.module_dependencies.items():
            layer = self.get_layer_for_module(module)
            G.add_node(module, type='module', layer=layer)
            
            for dep in deps:
                if dep in self.module_dependencies:
                    dep_layer = self.get_layer_for_module(dep)
                    G.add_node(dep, type='module', layer=dep_layer)
                    G.add_edge(module, dep, type='import')
        
        # Add function nodes and their relationships
        for module, funcs in self.function_definitions.items():
            for func in funcs:
                func_node = f"{module}.{func}"
                layer = self.get_layer_for_module(module)
                G.add_node(func_node, type='function', layer=layer)
                G.add_edge(module, func_node, type='defines')
        
        # Add function call relationships
        for func, calls in self.function_calls.items():
            for called_func in calls:
                if '.' in called_func:
                    called_module = called_func.split('.')[0]
                    if called_module in self.module_dependencies:
                        G.add_edge(func, called_func, type='calls')
        
        # Create visualization
        plt.figure(figsize=(24, 18))
        pos = nx.spring_layout(G, k=4, iterations=50)
        
        # Draw module nodes
        module_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'module']
        for layer in self.layer_colors:
            layer_modules = [n for n in module_nodes 
                           if G.nodes[n].get('layer') == layer]
            nx.draw_networkx_nodes(G, pos, nodelist=layer_modules, 
                                 node_color=self.layer_colors[layer], 
                                 node_size=2000, alpha=0.8, node_shape='s')
        
        # Draw function nodes
        func_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'function']
        for layer in self.layer_colors:
            layer_funcs = [n for n in func_nodes 
                          if G.nodes[n].get('layer') == layer]
            nx.draw_networkx_nodes(G, pos, nodelist=layer_funcs, 
                                 node_color=self.layer_colors[layer], 
                                 node_size=800, alpha=0.6, node_shape='o')
        
        # Draw different types of edges
        import_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'import']
        define_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'defines']
        call_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'calls']
        
        nx.draw_networkx_edges(G, pos, edgelist=import_edges, edge_color='blue', 
                             arrows=True, arrowsize=20, alpha=0.7, width=2)
        nx.draw_networkx_edges(G, pos, edgelist=define_edges, edge_color='green', 
                             arrows=True, arrowsize=15, alpha=0.5, width=1)
        nx.draw_networkx_edges(G, pos, edgelist=call_edges, edge_color='red', 
                             arrows=True, arrowsize=10, alpha=0.4, width=0.5)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
        
        # Create legend
        legend_elements = [
            mpatches.Patch(color=color, label=f"{layer.title()} (Modules)") 
            for layer, color in self.layer_colors.items()
        ]
        legend_elements.extend([
            mpatches.Patch(color='blue', label='Import Dependencies'),
            mpatches.Patch(color='green', label='Function Definitions'),
            mpatches.Patch(color='red', label='Function Calls')
        ])
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        plt.title("Full Application Architecture Graph", fontsize=18, fontweight='bold')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Full application graph saved as {filename}")
    
    def generate_comprehensive_report(self, filename: str = "comprehensive_dependency_report.json"):
        """Generate a comprehensive JSON report with all analysis data."""
        print(f"📊 Generating comprehensive report: {filename}")
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'project_root': str(self.project_root),
                'analysis_type': 'comprehensive_dependency_analysis'
            },
            'project_info': {
                'total_modules': len(self.module_dependencies),
                'total_functions': len(self.function_calls),
                'total_classes': sum(len(classes) for classes in self.class_definitions.values()),
                'architecture_layers': {layer: [] for layer in self.layers.keys()}
            },
            'module_dependencies': {k: list(v) for k, v in self.module_dependencies.items()},
            'function_calls': {k: list(v) for k, v in self.function_calls.items()},
            'function_definitions': {k: list(v) for k, v in self.function_definitions.items()},
            'class_definitions': {k: list(v) for k, v in self.class_definitions.items()},
            'layer_analysis': {},
            'cross_layer_dependencies': {},
            'statistics': {}
        }
        
        # Layer analysis
        for layer in self.layers.keys():
            layer_modules = [mod for mod in self.module_dependencies.keys() 
                           if self.get_layer_for_module(mod) == layer]
            report['project_info']['architecture_layers'][layer] = layer_modules
        
        # Cross-layer dependency analysis
        for layer1 in self.layers.keys():
            for layer2 in self.layers.keys():
                if layer1 != layer2:
                    cross_deps = []
                    for mod, deps in self.module_dependencies.items():
                        if self.get_layer_for_module(mod) == layer1:
                            for dep in deps:
                                if self.get_layer_for_module(dep) == layer2:
                                    cross_deps.append((mod, dep))
                    if cross_deps:
                        report['cross_layer_dependencies'][f"{layer1}_to_{layer2}"] = cross_deps
        
        # Statistics
        report['statistics'] = {
            'modules_per_layer': {layer: len(modules) for layer, modules in report['project_info']['architecture_layers'].items()},
            'total_dependencies': sum(len(deps) for deps in self.module_dependencies.values()),
            'avg_dependencies_per_module': sum(len(deps) for deps in self.module_dependencies.values()) / len(self.module_dependencies) if self.module_dependencies else 0,
            'most_dependent_modules': sorted([(mod, len(deps)) for mod, deps in self.module_dependencies.items()], 
                                           key=lambda x: x[1], reverse=True)[:10]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Comprehensive report saved as {filename}")
    
    def run_comprehensive_analysis(self):
        """Run the complete comprehensive analysis."""
        print("🚀 Starting comprehensive dependency analysis...")
        print("=" * 60)
        
        # Build all graphs
        self.build_full_application_graph()
        
        # Generate visualizations
        self.generate_module_dependency_visualization()
        self.generate_function_call_visualization()
        self.generate_full_application_visualization()
        
        # Generate report
        self.generate_comprehensive_report()
        
        print("=" * 60)
        print("✅ Comprehensive dependency analysis completed!")
        print("\nGenerated files:")
        print("  📊 module_dependency_map.png - Module dependency visualization")
        print("  📊 function_call_graph.png - Function call graph visualization")
        print("  📊 full_application_graph.png - Full application architecture")
        print("  📄 comprehensive_dependency_report.json - Detailed analysis data")

def main():
    """Main entry point."""
    project_root = Path.cwd()
    
    if not (project_root / "flowproc").exists():
        print("❌ Error: flowproc directory not found in current directory")
        print("Please run this script from the project root directory")
        sys.exit(1)
    
    analyzer = ComprehensiveDependencyAnalyzer(str(project_root))
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main() 