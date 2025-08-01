#!/usr/bin/env python3
"""
Validation script for the main window refactoring migration.
Run this after copying the implementations from the artifact.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test that all new modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        # Test component imports
        from flowproc.presentation.gui.views.components import (
            StateManager, UIBuilder, EventHandler, 
            ProcessingCoordinator, FileManager
        )
        print("✅ Component imports successful")
        
        # Test mixin imports
        from flowproc.presentation.gui.views.mixins import (
            StylingMixin, ValidationMixin
        )
        print("✅ Mixin imports successful")
        
        # Test main window import
        from flowproc.presentation.gui.views.main_window import MainWindow
        print("✅ MainWindow import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality of components."""
    print("🔍 Testing basic functionality...")
    
    try:
        from flowproc.presentation.gui.views.components import StateManager
        
        # Test StateManager basic functionality
        state_manager = StateManager()
        
        # Test property setting
        test_paths = ["/test/path1.csv", "/test/path2.csv"]
        state_manager.preview_paths = test_paths
        
        if state_manager.preview_paths == test_paths:
            print("✅ StateManager basic functionality works")
            return True
        else:
            print("❌ StateManager functionality test failed")
            return False
            
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("🚀 Starting migration validation...\n")
    
    # Check if implementations are in place
    components_dir = Path("flowproc/presentation/gui/views/components")
    if not components_dir.exists():
        print("❌ Components directory not found")
        return False
        
    # Check for placeholder files
    state_manager_file = components_dir / "state_manager.py"
    if state_manager_file.exists():
        content = state_manager_file.read_text()
        if "Placeholder" in content:
            print("⚠️  WARNING: Template files detected. Please copy implementations from the artifact.")
            print("   Files still containing placeholders:")
            for py_file in components_dir.glob("*.py"):
                if "Placeholder" in py_file.read_text():
                    print(f"   - {py_file.name}")
            print()
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    if test_imports():
        tests_passed += 1
    
    if test_basic_functionality():
        tests_passed += 1
    
    print(f"\n📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 Migration validation successful!")
        return True
    else:
        print("❌ Migration validation failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
