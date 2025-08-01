#!/usr/bin/env python3
"""
Advanced Dependency Analyzer for FlowProcessor Project

This script provides comprehensive dependency analysis including:
1. Module dependency map (which modules import/use others)
2. Function call graph (which functions call or are called by others)
3. Class inheritance relationships
4. Service layer dependencies
5. Full application architecture graph
"""

import os
import sys
import ast
import json
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Any, Optional
import subprocess
import tempfile

class AdvancedDependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.flowproc_dir = self.project_root / "flowproc"
        self.module_dependencies = defaultdict(set)
        self.function_calls = defaultdict(set)
        self.class_inheritance = defaultdict(set)
        self.import_map = defaultdict(set)
        self.all_modules = set()
        self.function_definitions = defaultdict(set)
        self.class_definitions = defaultdict(set)
        self.service_dependencies = defaultdict(set)
        
    def find_python_files(self, directory: Path) -> List[Path]:
        """Find all Python files in the directory recursively."""
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip __pycache__, .git, venv, etc.
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'build', '.pytest_cache']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files
    
    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        relative_path = file_path.relative_to(self.project_root)
        return str(relative_path).replace('/', '.').replace('\\', '.').replace('.py', '')
    
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
            print(f"Error parsing {file_path}: {e}")
            
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
                    return self.get_node_name(node.value) + "." + node.attr if self.get_node_name(node.value) else None
            elif isinstance(node, ast.Call):
                return self.get_node_name(node.func)
            elif isinstance(node, ast.Subscript):
                return self.get_node_name(node.value)
            else:
                return None
        except:
            return None
    
    def analyze_function_calls(self, file_path: Path) -> Dict[str, Set[str]]:
        """Analyze function calls in a Python file with improved error handling."""
        calls = defaultdict(set)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self.get_node_name(node.func)
                    if func_name:
                        calls['function_calls'].add(func_name)
                        
        except Exception as e:
            print(f"Error analyzing function calls in {file_path}: {e}")
            
        return calls
    
    def analyze_function_definitions(self, file_path: Path) -> Dict[str, List[str]]:
        """Analyze function definitions in a Python file."""
        functions = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions[node.name] = []
                    # Analyze function body for calls
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            func_name = self.get_node_name(child.func)
                            if func_name:
                                functions[node.name].append(func_name)
                        
        except Exception as e:
            print(f"Error analyzing function definitions in {file_path}: {e}")
            
        return functions
    
    def analyze_class_inheritance(self, file_path: Path) -> Dict[str, List[str]]:
        """Analyze class inheritance in a Python file."""
        inheritance = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = []
                    for base in node.bases:
                        base_name = self.get_node_name(base)
                        if base_name:
                            bases.append(base_name)
                    inheritance[node.name] = bases
                        
        except Exception as e:
            print(f"Error analyzing class inheritance in {file_path}: {e}")
            
        return inheritance
    
    def categorize_modules(self) -> Dict[str, List[str]]:
        """Categorize modules by their architectural layer."""
        categories = {
            'application': [],
            'domain': [],
            'infrastructure': [],
            'presentation': [],
            'core': [],
            'other': []
        }
        
        for module in self.all_modules:
            if module.startswith('flowproc.application'):
                categories['application'].append(module)
            elif module.startswith('flowproc.domain'):
                categories['domain'].append(module)
            elif module.startswith('flowproc.infrastructure'):
                categories['infrastructure'].append(module)
            elif module.startswith('flowproc.presentation'):
                categories['presentation'].append(module)
            elif module.startswith('flowproc.core'):
                categories['core'].append(module)
            else:
                categories['other'].append(module)
        
        return categories
    
    def build_module_dependency_map(self):
        """Build module dependency map."""
        print("Building module dependency map...")
        
        python_files = self.find_python_files(self.flowproc_dir)
        
        for file_path in python_files:
            module_name = self.get_module_name(file_path)
            self.all_modules.add(module_name)
            
            imports = self.analyze_imports(file_path)
            for imp in imports:
                # Filter to only include internal modules
                if imp.startswith('flowproc.') or imp == 'flowproc':
                    self.module_dependencies[module_name].add(imp)
                    self.import_map[imp].add(module_name)
    
    def build_function_call_graph(self):
        """Build function call graph."""
        print("Building function call graph...")
        
        python_files = self.find_python_files(self.flowproc_dir)
        
        for file_path in python_files:
            module_name = self.get_module_name(file_path)
            calls = self.analyze_function_calls(file_path)
            functions = self.analyze_function_definitions(file_path)
            inheritance = self.analyze_class_inheritance(file_path)
            
            # Store function definitions
            for func_name, func_calls in functions.items():
                self.function_definitions[module_name].add(func_name)
                for call in func_calls:
                    self.function_calls[module_name].add(call)
            
            # Store class definitions
            for class_name in inheritance.keys():
                self.class_definitions[module_name].add(class_name)
    
    def identify_service_dependencies(self):
        """Identify service layer dependencies."""
        print("Identifying service dependencies...")
        
        service_modules = [
            'flowproc.domain.parsing.service',
            'flowproc.domain.processing.service',
            'flowproc.domain.visualization.service',
            'flowproc.domain.export.service',
            'flowproc.domain.validation.input_validator',
            'flowproc.infrastructure.config.settings',
            'flowproc.application.container'
        ]
        
        for service in service_modules:
            if service in self.module_dependencies:
                self.service_dependencies[service] = self.module_dependencies[service]
    
    def generate_layered_architecture_graph(self, filename: str):
        """Generate a layered architecture visualization."""
        try:
            categories = self.categorize_modules()
            
            G = nx.DiGraph()
            
            # Define layer positions
            layer_positions = {
                'presentation': 0,
                'application': 1,
                'domain': 2,
                'infrastructure': 3,
                'core': 4,
                'other': 5
            }
            
            # Add nodes with layer information
            for layer, modules in categories.items():
                for module in modules:
                    G.add_node(module, layer=layer)
            
            # Add edges
            for source, targets in self.module_dependencies.items():
                for target in targets:
                    if target in G.nodes:
                        G.add_edge(source, target)
            
            # Create visualization
            plt.figure(figsize=(24, 18))
            
            # Position nodes by layer
            pos = {}
            for layer, modules in categories.items():
                y_pos = layer_positions[layer]
                for i, module in enumerate(modules):
                    x_pos = (i - len(modules) / 2) * 2
                    pos[module] = (x_pos, y_pos)
            
            # Draw nodes with different colors for each layer
            colors = {
                'presentation': 'lightcoral',
                'application': 'lightblue',
                'domain': 'lightgreen',
                'infrastructure': 'lightyellow',
                'core': 'lightgray',
                'other': 'lightpink'
            }
            
            for layer, color in colors.items():
                layer_nodes = [n for n, d in G.nodes(data=True) if d.get('layer') == layer]
                if layer_nodes:
                    nx.draw_networkx_nodes(G, pos, nodelist=layer_nodes, 
                                         node_color=color, node_size=2000, alpha=0.8)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                 arrows=True, arrowsize=20, alpha=0.6)
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, font_size=6, font_weight='bold')
            
            # Add layer labels
            for layer, y_pos in layer_positions.items():
                plt.text(-15, y_pos, layer.upper(), fontsize=14, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=colors.get(layer, 'white')))
            
            plt.title("FlowProcessor Layered Architecture", fontsize=20, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
            
        except Exception as e:
            print(f"Error generating layered architecture graph: {e}")
    
    def generate_service_dependency_graph(self, filename: str):
        """Generate service dependency graph."""
        try:
            G = nx.DiGraph()
            
            # Add service nodes
            for service, deps in self.service_dependencies.items():
                G.add_node(service)
                for dep in deps:
                    if dep in self.service_dependencies:
                        G.add_edge(service, dep)
            
            # Create visualization
            plt.figure(figsize=(16, 12))
            pos = nx.spring_layout(G, k=2, iterations=50)
            
            # Draw nodes
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                 node_size=3000, alpha=0.8)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, edge_color='gray', 
                                 arrows=True, arrowsize=20, alpha=0.6)
            
            # Draw labels
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
            
            plt.title("FlowProcessor Service Dependencies", fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
            
        except Exception as e:
            print(f"Error generating service dependency graph: {e}")
    
    def generate_comprehensive_report(self, filename: str):
        """Generate a comprehensive dependency report."""
        categories = self.categorize_modules()
        
        report_lines = [
            "# FlowProcessor Comprehensive Dependency Analysis Report",
            "",
            f"## Project Overview",
            f"- Total modules: {len(self.all_modules)}",
            f"- Total dependencies: {sum(len(deps) for deps in self.module_dependencies.values())}",
            f"- Total functions defined: {sum(len(funcs) for funcs in self.function_definitions.values())}",
            f"- Total classes defined: {sum(len(classes) for classes in self.class_definitions.values())}",
            "",
            "## Architecture Layers",
            ""
        ]
        
        # Layer breakdown
        for layer, modules in categories.items():
            report_lines.append(f"### {layer.upper()} Layer ({len(modules)} modules)")
            for module in sorted(modules):
                report_lines.append(f"- {module}")
            report_lines.append("")
        
        # Service dependencies
        report_lines.extend([
            "## Service Dependencies",
            ""
        ])
        
        for service, deps in self.service_dependencies.items():
            report_lines.append(f"### {service}")
            if deps:
                report_lines.append("Dependencies:")
                for dep in sorted(deps):
                    report_lines.append(f"- {dep}")
            else:
                report_lines.append("No dependencies")
            report_lines.append("")
        
        # Most complex modules
        report_lines.extend([
            "## Most Complex Modules (by dependency count)",
            ""
        ])
        
        sorted_modules = sorted(
            self.module_dependencies.items(), 
            key=lambda x: len(x[1]), 
            reverse=True
        )
        
        for module, deps in sorted_modules[:10]:
            if deps:
                report_lines.append(f"### {module}")
                report_lines.append(f"Dependencies ({len(deps)}):")
                for dep in sorted(deps):
                    report_lines.append(f"- {dep}")
                report_lines.append("")
        
        # Function call analysis
        report_lines.extend([
            "## Function Call Analysis",
            ""
        ])
        
        for module, calls in self.function_calls.items():
            if calls:
                report_lines.append(f"### {module}")
                report_lines.append(f"Function calls ({len(calls)}):")
                for call in sorted(calls):
                    report_lines.append(f"- {call}")
                report_lines.append("")
        
        with open(filename, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Generated {filename}")
    
    def run_analysis(self):
        """Run complete advanced dependency analysis."""
        print("Starting advanced dependency analysis...")
        
        # Build dependency maps
        self.build_module_dependency_map()
        self.build_function_call_graph()
        self.identify_service_dependencies()
        
        # Generate reports
        self.generate_comprehensive_report('advanced_dependency_report.md')
        
        # Generate visualizations
        self.generate_layered_architecture_graph('layered_architecture.png')
        self.generate_service_dependency_graph('service_dependencies.png')
        
        # Generate JSON data
        analysis_data = {
            "project_info": {
                "name": "FlowProcessor",
                "total_modules": len(self.all_modules),
                "total_dependencies": sum(len(deps) for deps in self.module_dependencies.values()),
                "total_functions": sum(len(funcs) for funcs in self.function_definitions.values()),
                "total_classes": sum(len(classes) for classes in self.class_definitions.values())
            },
            "architecture_layers": self.categorize_modules(),
            "module_dependencies": {k: list(v) for k, v in self.module_dependencies.items()},
            "function_calls": {k: list(v) for k, v in self.function_calls.items()},
            "function_definitions": {k: list(v) for k, v in self.function_definitions.items()},
            "class_definitions": {k: list(v) for k, v in self.class_definitions.items()},
            "service_dependencies": {k: list(v) for k, v in self.service_dependencies.items()},
            "import_map": {k: list(v) for k, v in self.import_map.items()},
            "all_modules": list(self.all_modules)
        }
        
        with open('advanced_dependency_analysis.json', 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print("Generated advanced_dependency_analysis.json")
        
        print("\nAdvanced dependency analysis complete!")
        print("Generated files:")
        print("- advanced_dependency_report.md (comprehensive report)")
        print("- advanced_dependency_analysis.json (complete data)")
        print("- layered_architecture.png (layered architecture visualization)")
        print("- service_dependencies.png (service dependency graph)")

def main():
    analyzer = AdvancedDependencyAnalyzer(".")
    analyzer.run_analysis()

if __name__ == "__main__":
    main() 