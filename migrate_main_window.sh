#!/bin/bash
# migrate_main_window.sh - Automate the main window refactoring migration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT=$(pwd)
GUI_VIEWS_DIR="flowproc-project/flowproc/presentation/gui/views"
COMPONENTS_DIR="$GUI_VIEWS_DIR/components"
MIXINS_DIR="$GUI_VIEWS_DIR/mixins"

echo -e "${BLUE}🚀 Starting Main Window Refactoring Migration...${NC}"

# Step 1: Backup current files
echo -e "${YELLOW}📁 Step 1: Backing up current files...${NC}"
if [ -f "$GUI_VIEWS_DIR/main_window.py" ]; then
    cp "$GUI_VIEWS_DIR/main_window.py" "$GUI_VIEWS_DIR/main_window_backup.py"
    echo -e "${GREEN}✅ Backed up main_window.py to main_window_backup.py${NC}"
else
    echo -e "${RED}❌ main_window.py not found at expected location${NC}"
    exit 1
fi

# Step 2: Create directory structure
echo -e "${YELLOW}📁 Step 2: Creating new directory structure...${NC}"
mkdir -p "$COMPONENTS_DIR"
mkdir -p "$MIXINS_DIR"
echo -e "${GREEN}✅ Created components/ and mixins/ directories${NC}"

# Step 3: Create __init__.py files
echo -e "${YELLOW}📝 Step 3: Creating __init__.py files...${NC}"

# Components __init__.py
cat > "$COMPONENTS_DIR/__init__.py" << 'EOF'
"""UI Components package for the main window."""

from .ui_builder import UIBuilder
from .event_handler import EventHandler
from .state_manager import StateManager, WindowState
from .processing_coordinator import ProcessingCoordinator
from .file_manager import FileManager

__all__ = [
    'UIBuilder',
    'EventHandler', 
    'StateManager',
    'WindowState',
    'ProcessingCoordinator',
    'FileManager'
]
EOF

# Mixins __init__.py
cat > "$MIXINS_DIR/__init__.py" << 'EOF'
"""UI Mixins package."""

from .styling_mixin import StylingMixin
from .validation_mixin import ValidationMixin

__all__ = ['StylingMixin', 'ValidationMixin']
EOF

echo -e "${GREEN}✅ Created __init__.py files${NC}"

# Step 4: Create placeholder component files
echo -e "${YELLOW}📝 Step 4: Creating component file templates...${NC}"

# Create template files that need to be filled with content from the artifact
create_template_file() {
    local file_path="$1"
    local module_name="$2"
    local description="$3"
    
    cat > "$file_path" << EOF
"""
$description
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)


# TODO: Copy implementation from the provided artifact
# This is a placeholder - replace with the actual implementation
class Placeholder$module_name:
    """Placeholder class - replace with actual implementation from artifact."""
    
    def __init__(self):
        raise NotImplementedError(
            "This is a placeholder. Copy the implementation from the artifact."
        )
EOF
}

# Create template files
create_template_file "$COMPONENTS_DIR/state_manager.py" "StateManager" "State management for the main window."
create_template_file "$COMPONENTS_DIR/ui_builder.py" "UIBuilder" "UI building and layout management."
create_template_file "$COMPONENTS_DIR/event_handler.py" "EventHandler" "Event handling for the main window."
create_template_file "$COMPONENTS_DIR/processing_coordinator.py" "ProcessingCoordinator" "Processing coordination and management."
create_template_file "$COMPONENTS_DIR/file_manager.py" "FileManager" "File management and operations."
create_template_file "$MIXINS_DIR/styling_mixin.py" "StylingMixin" "Styling mixin for consistent UI appearance."
create_template_file "$MIXINS_DIR/validation_mixin.py" "ValidationMixin" "Validation mixin for input validation."

echo -e "${GREEN}✅ Created component template files${NC}"

# Step 5: Create validation script
echo -e "${YELLOW}🧪 Step 5: Creating validation script...${NC}"
cat > "flowproc-project/validate_migration.py" << 'EOF'
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
EOF

chmod +x flowproc-project/validate_migration.py
echo -e "${GREEN}✅ Created validation script${NC}"

# Step 6: Update views __init__.py
echo -e "${YELLOW}📝 Step 6: Updating views __init__.py...${NC}"
cat > "$GUI_VIEWS_DIR/__init__.py" << 'EOF'
"""
GUI Views Module

This module contains the view classes that handle the user interface
components and their presentation logic.
"""

from .main_window import MainWindow

# Import components (will work after implementations are copied from artifact)
try:
    from .components import (
        UIBuilder, EventHandler, StateManager, 
        ProcessingCoordinator, FileManager
    )
    from .mixins import StylingMixin, ValidationMixin
    
    __all__ = [
        'MainWindow',
        'UIBuilder',
        'EventHandler', 
        'StateManager',
        'ProcessingCoordinator',
        'FileManager',
        'StylingMixin',
        'ValidationMixin'
    ]
except ImportError:
    # During migration, components may not be fully implemented yet
    __all__ = ['MainWindow']
EOF

echo -e "${GREEN}✅ Updated views __init__.py${NC}"

# Step 7: Create migration checklist
echo -e "${YELLOW}📋 Step 7: Creating migration checklist...${NC}"
cat > "flowproc-project/MIGRATION_CHECKLIST.md" << 'EOF'
# Migration Checklist

## Phase 1: Setup (Automated) ✅
- [x] Backup original main_window.py
- [x] Create directory structure
- [x] Create __init__.py files
- [x] Create template files

## Phase 2: Implementation (Manual)
- [ ] Copy StateManager implementation from artifact
- [ ] Copy UIBuilder implementation from artifact  
- [ ] Copy EventHandler implementation from artifact
- [ ] Copy ProcessingCoordinator implementation from artifact
- [ ] Copy FileManager implementation from artifact
- [ ] Copy StylingMixin implementation from artifact
- [ ] Copy ValidationMixin implementation from artifact
- [ ] Copy refactored MainWindow implementation from artifact

## Phase 3: Integration (Manual)
- [ ] Update import statements in existing files
- [ ] Update gui/__init__.py with new exports
- [ ] Fix any circular import issues
- [ ] Update external references to MainWindow internals

## Phase 4: Testing
- [ ] Run validation script: `python validate_migration.py`
- [ ] Test GUI startup: `python -m flowproc.presentation.gui.main`
- [ ] Run existing tests: `python -m pytest tests/integration/test_gui.py`
- [ ] Manual testing of all GUI functionality

## Phase 5: Cleanup
- [ ] Remove template placeholder code
- [ ] Add proper error handling
- [ ] Update documentation
- [ ] Remove backup file if everything works

## Quick Commands
```bash
# Run validation
python validate_migration.py

# Test GUI startup  
python -c "from flowproc.presentation.gui.main import main; print('Import successful')"

# Run tests
python -m pytest tests/integration/test_gui.py -v
```
EOF

echo -e "${GREEN}✅ Created migration checklist${NC}"

# Final instructions
echo -e "${BLUE}"
echo "════════════════════════════════════════════════════════════════"
echo "🎉 Migration setup complete!"
echo "════════════════════════════════════════════════════════════════"
echo -e "${NC}"

echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Copy implementations from the provided artifact into:"
echo "   - $COMPONENTS_DIR/*.py"
echo "   - $MIXINS_DIR/*.py" 
echo "   - $GUI_VIEWS_DIR/main_window.py"
echo ""
echo "2. Run validation: ${GREEN}cd flowproc-project && python validate_migration.py${NC}"
echo ""
echo "3. Follow the checklist: ${GREEN}cat flowproc-project/MIGRATION_CHECKLIST.md${NC}"
echo ""
echo "4. Test the application: ${GREEN}cd flowproc-project && python -m flowproc.presentation.gui.main${NC}"

echo -e "${GREEN}"
echo "✨ Files created:"
echo "  - Components directory with templates"
echo "  - Mixins directory with templates"
echo "  - Migration validation script"
echo "  - Migration checklist"
echo "  - Updated __init__.py files"
echo -e "${NC}"

echo -e "${YELLOW}⚠️  Remember: The template files contain placeholders."
echo "   Copy the actual implementations from the provided artifact!${NC}"