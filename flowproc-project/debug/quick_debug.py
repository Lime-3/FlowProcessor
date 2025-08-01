#!/usr/bin/env python3
"""
Quick Debug Diagnostic for FlowProcessor
Rapid assessment of common issues and system status.
"""

import sys
import os
import platform
import traceback
from pathlib import Path

def check_python_environment():
    """Check Python environment."""
    print("🐍 Python Environment:")
    print(f"  Python Version: {sys.version}")
    print(f"  Platform: {platform.platform()}")
    print(f"  Architecture: {platform.architecture()}")
    print(f"  Executable: {sys.executable}")
    
    # Check if running in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"  Virtual Environment: ✅ Active ({sys.prefix})")
    else:
        print(f"  Virtual Environment: ❌ Not detected")

def check_imports():
    """Check critical imports."""
    print("\n📦 Critical Imports:")
    
    critical_modules = [
        ('numpy', 'Numerical computing'),
        ('pandas', 'Data manipulation'),
        ('plotly', 'Visualization'),
        ('PySide6', 'GUI framework'),
        ('openpyxl', 'Excel export'),
        ('scipy', 'Scientific computing')
    ]
    
    for module_name, description in critical_modules:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"  {module_name}: ✅ {version} ({description})")
        except ImportError as e:
            print(f"  {module_name}: ❌ Import failed - {e}")

def check_project_structure():
    """Check project structure."""
    print("\n📁 Project Structure:")
    
    current_dir = Path.cwd()
    print(f"  Current Directory: {current_dir}")
    
    # Check for key directories
    key_dirs = ['flowproc', 'tests', 'scripts']
    for dir_name in key_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            print(f"  {dir_name}/: ✅ Found")
        else:
            print(f"  {dir_name}/: ❌ Missing")
    
    # Check for key files
    key_files = ['pyproject.toml', 'requirements.txt', 'setup.py']
    for file_name in key_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"  {file_name}: ✅ Found")
        else:
            print(f"  {file_name}: ❌ Missing")

def check_flowproc_imports():
    """Check FlowProc specific imports."""
    print("\n🔧 FlowProc Imports:")
    
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        flowproc_modules = [
            'flowproc.logging_config',
            'flowproc.presentation.gui',
            'flowproc.domain.parsing',
            'flowproc.domain.processing',
            'flowproc.domain.visualization'
        ]
        
        for module_name in flowproc_modules:
            try:
                __import__(module_name)
                print(f"  {module_name}: ✅ Imported successfully")
            except ImportError as e:
                print(f"  {module_name}: ❌ Import failed - {e}")
                
    except Exception as e:
        print(f"  Error checking FlowProc imports: {e}")

def check_system_resources():
    """Check system resources."""
    print("\n💻 System Resources:")
    
    try:
        import psutil
        
        # Memory
        memory = psutil.virtual_memory()
        print(f"  Memory: {memory.available / (1024**3):.1f}GB available / {memory.total / (1024**3):.1f}GB total")
        
        # Disk space
        disk = psutil.disk_usage('.')
        print(f"  Disk: {disk.free / (1024**3):.1f}GB available / {disk.total / (1024**3):.1f}GB total")
        
        # CPU
        print(f"  CPU Cores: {psutil.cpu_count()}")
        
    except ImportError:
        print("  psutil not available - cannot check system resources")
    except Exception as e:
        print(f"  Error checking system resources: {e}")

def check_log_files():
    """Check log files."""
    print("\n📋 Log Files:")
    
    log_paths = [
        Path('flowproc/data/logs/processing.log'),
        Path('debug.log'),
        Path('logs/processing.log')
    ]
    
    for log_path in log_paths:
        if log_path.exists():
            size_mb = log_path.stat().st_size / (1024 * 1024)
            print(f"  {log_path}: ✅ Found ({size_mb:.1f}MB)")
            
            # Check if log is recent
            import time
            mtime = log_path.stat().st_mtime
            age_hours = (time.time() - mtime) / 3600
            if age_hours < 24:
                print(f"    Last modified: {age_hours:.1f} hours ago")
            else:
                print(f"    Last modified: {age_hours/24:.1f} days ago")
        else:
            print(f"  {log_path}: ❌ Not found")

def check_gui_environment():
    """Check GUI environment."""
    print("\n🖥️ GUI Environment:")
    
    # Check display
    display = os.environ.get('DISPLAY')
    if display:
        print(f"  DISPLAY: ✅ {display}")
    else:
        print(f"  DISPLAY: ❌ Not set")
    
    # Check Qt platform
    qt_platform = os.environ.get('QT_QPA_PLATFORM')
    if qt_platform:
        print(f"  QT_QPA_PLATFORM: {qt_platform}")
    else:
        print(f"  QT_QPA_PLATFORM: Not set (will use default)")
    
    # Check if we can import Qt
    try:
        from PySide6.QtWidgets import QApplication
        print(f"  PySide6: ✅ Can import QApplication")
    except ImportError as e:
        print(f"  PySide6: ❌ Import failed - {e}")

def run_quick_test():
    """Run a quick functionality test."""
    print("\n🧪 Quick Functionality Test:")
    
    try:
        # Test basic FlowProc functionality
        from flowproc.logging_config import setup_logging
        setup_logging()
        print("  Logging setup: ✅ Success")
        
        # Test resource utils
        from flowproc.resource_utils import get_data_path
        data_path = get_data_path('logs')
        print(f"  Resource utils: ✅ Data path resolved: {data_path}")
        
        print("  Basic functionality: ✅ All tests passed")
        
    except Exception as e:
        print(f"  Functionality test: ❌ Failed - {e}")
        traceback.print_exc()

def main():
    """Run all diagnostic checks."""
    print("="*60)
    print("FLOWPROCESSOR QUICK DEBUG DIAGNOSTIC")
    print("="*60)
    
    check_python_environment()
    check_imports()
    check_project_structure()
    check_flowproc_imports()
    check_system_resources()
    check_log_files()
    check_gui_environment()
    run_quick_test()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    
    print("\n💡 Next Steps:")
    print("  1. If any ❌ issues found, address them first")
    print("  2. Run: python debug_monitor.py health")
    print("  3. Run: python debug_monitor.py monitor")
    print("  4. Check debug.log for detailed information")

if __name__ == "__main__":
    main() 