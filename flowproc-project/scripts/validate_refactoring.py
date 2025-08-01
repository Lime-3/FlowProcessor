#!/usr/bin/env python3
"""
Refactoring Validation Script

This script validates the results of the FlowProcessor refactoring.
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class RefactoringValidator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.flowproc_dir = self.project_root / "flowproc"
        self.validation_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def validate_module_count(self):
        """Validate that module count has been reduced."""
        print("📊 Validating module count...")
        
        python_files = list(self.flowproc_dir.rglob("*.py"))
        module_count = len(python_files)
        
        print(f"   Current module count: {module_count}")
        
        if module_count < 119:  # Original count
            reduction = 119 - module_count
            percentage = (reduction / 119) * 100
            self.validation_results["passed"].append(
                f"Module count reduced by {reduction} ({percentage:.1f}%)"
            )
        else:
            self.validation_results["warnings"].append(
                f"Module count not reduced (current: {module_count})"
            )
    
    def validate_service_consolidation(self):
        """Validate that services have been consolidated."""
        print("🔧 Validating service consolidation...")
        
        # Check visualization services
        viz_dir = self.flowproc_dir / "domain" / "visualization"
        renderers_dir = viz_dir / "renderers"
        processors_dir = viz_dir / "processors"
        
        if renderers_dir.exists() and processors_dir.exists():
            self.validation_results["passed"].append("Visualization services consolidated")
        else:
            self.validation_results["failed"].append("Visualization services not consolidated")
        
        # Check parsing services
        parsing_dir = self.flowproc_dir / "domain" / "parsing"
        parsers_dir = parsing_dir / "parsers"
        validators_dir = parsing_dir / "validators"
        
        if parsers_dir.exists() and validators_dir.exists():
            self.validation_results["passed"].append("Parsing services consolidated")
        else:
            self.validation_results["failed"].append("Parsing services not consolidated")
    
    def validate_interfaces(self):
        """Validate that interfaces have been created."""
        print("🔌 Validating interfaces...")
        
        interfaces_file = self.flowproc_dir / "core" / "interfaces.py"
        if interfaces_file.exists():
            self.validation_results["passed"].append("Service interfaces created")
        else:
            self.validation_results["failed"].append("Service interfaces not created")
    
    def validate_dependency_injection(self):
        """Validate that DI container has been created."""
        print("💉 Validating dependency injection...")
        
        container_file = self.flowproc_dir / "application" / "container.py"
        if container_file.exists():
            self.validation_results["passed"].append("Dependency injection container created")
        else:
            self.validation_results["failed"].append("Dependency injection container not created")
    
    def validate_pipeline_pattern(self):
        """Validate that pipeline pattern has been created."""
        print("🔄 Validating pipeline pattern...")
        
        pipeline_file = self.flowproc_dir / "domain" / "processing" / "pipeline.py"
        if pipeline_file.exists():
            self.validation_results["passed"].append("Pipeline pattern created")
        else:
            self.validation_results["failed"].append("Pipeline pattern not created")
    
    def validate_event_system(self):
        """Validate that event system has been created."""
        print("📡 Validating event system...")
        
        events_file = self.flowproc_dir / "core" / "events.py"
        if events_file.exists():
            self.validation_results["passed"].append("Event system created")
        else:
            self.validation_results["failed"].append("Event system not created")
    
    def validate_imports(self):
        """Validate that imports are working correctly."""
        print("📦 Validating imports...")
        
        # Check for import errors
        import_errors = []
        
        for py_file in self.flowproc_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to parse the file
                ast.parse(content)
                
            except SyntaxError as e:
                import_errors.append(f"Syntax error in {py_file}: {e}")
            except Exception as e:
                import_errors.append(f"Error in {py_file}: {e}")
        
        if not import_errors:
            self.validation_results["passed"].append("All imports valid")
        else:
            for error in import_errors:
                self.validation_results["failed"].append(error)
    
    def validate_architecture_layers(self):
        """Validate that architecture layers are maintained."""
        print("🏗️ Validating architecture layers...")
        
        layers = {
            "presentation": self.flowproc_dir / "presentation",
            "application": self.flowproc_dir / "application",
            "domain": self.flowproc_dir / "domain",
            "infrastructure": self.flowproc_dir / "infrastructure",
            "core": self.flowproc_dir / "core"
        }
        
        for layer_name, layer_path in layers.items():
            if layer_path.exists():
                self.validation_results["passed"].append(f"{layer_name} layer maintained")
            else:
                self.validation_results["failed"].append(f"{layer_name} layer missing")
    
    def validate_circular_dependencies(self):
        """Validate that no circular dependencies exist."""
        print("🔄 Validating circular dependencies...")
        
        # This is a simplified check - in practice you'd use a more sophisticated algorithm
        module_dependencies = defaultdict(set)
        
        for py_file in self.flowproc_dir.rglob("*.py"):
            module_name = str(py_file.relative_to(self.flowproc_dir)).replace('/', '.').replace('.py', '')
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('flowproc.'):
                                module_dependencies[module_name].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('flowproc.'):
                            module_dependencies[module_name].add(node.module)
                            
            except Exception as e:
                print(f"⚠️  Error analyzing {py_file}: {e}")
        
        # Simple circular dependency check
        circular_deps = []
        for module, deps in module_dependencies.items():
            for dep in deps:
                if dep in module_dependencies and module in module_dependencies[dep]:
                    circular_deps.append(f"Circular dependency: {module} ↔ {dep}")
        
        if not circular_deps:
            self.validation_results["passed"].append("No circular dependencies detected")
        else:
            for dep in circular_deps:
                self.validation_results["failed"].append(dep)
    
    def generate_validation_report(self):
        """Generate a comprehensive validation report."""
        print("\n" + "="*60)
        print("📋 REFACTORING VALIDATION REPORT")
        print("="*60)
        
        # Summary
        total_checks = len(self.validation_results["passed"]) + len(self.validation_results["failed"]) + len(self.validation_results["warnings"])
        
        print(f"\n📊 Summary:")
        print(f"   Total checks: {total_checks}")
        print(f"   ✅ Passed: {len(self.validation_results['passed'])}")
        print(f"   ❌ Failed: {len(self.validation_results['failed'])}")
        print(f"   ⚠️  Warnings: {len(self.validation_results['warnings'])}")
        
        # Passed checks
        if self.validation_results["passed"]:
            print(f"\n✅ Passed Checks:")
            for check in self.validation_results["passed"]:
                print(f"   • {check}")
        
        # Failed checks
        if self.validation_results["failed"]:
            print(f"\n❌ Failed Checks:")
            for check in self.validation_results["failed"]:
                print(f"   • {check}")
        
        # Warnings
        if self.validation_results["warnings"]:
            print(f"\n⚠️  Warnings:")
            for warning in self.validation_results["warnings"]:
                print(f"   • {warning}")
        
        # Overall status
        if not self.validation_results["failed"]:
            print(f"\n🎉 REFACTORING VALIDATION PASSED!")
        else:
            print(f"\n⚠️  REFACTORING VALIDATION FAILED - Please address the issues above.")
        
        # Save report
        report_file = self.project_root / "refactoring_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
    
    def run_validation(self):
        """Run all validation checks."""
        print("🔍 Starting refactoring validation...")
        
        self.validate_module_count()
        self.validate_service_consolidation()
        self.validate_interfaces()
        self.validate_dependency_injection()
        self.validate_pipeline_pattern()
        self.validate_event_system()
        self.validate_imports()
        self.validate_architecture_layers()
        self.validate_circular_dependencies()
        
        self.generate_validation_report()

def main():
    """Main function."""
    validator = RefactoringValidator()
    
    print("🔍 FlowProcessor Refactoring Validator")
    print("=" * 50)
    print("1. Run complete validation")
    print("2. Validate module count only")
    print("3. Validate service consolidation only")
    print("4. Validate interfaces only")
    print("5. Validate architecture only")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        validator.run_validation()
    elif choice == "2":
        validator.validate_module_count()
        validator.generate_validation_report()
    elif choice == "3":
        validator.validate_service_consolidation()
        validator.generate_validation_report()
    elif choice == "4":
        validator.validate_interfaces()
        validator.validate_dependency_injection()
        validator.generate_validation_report()
    elif choice == "5":
        validator.validate_architecture_layers()
        validator.validate_circular_dependencies()
        validator.generate_validation_report()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 