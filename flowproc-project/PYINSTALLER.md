# PyInstaller Compatibility Guide

This document explains how the FlowProcessor application has been made compatible with PyInstaller and cx_Freeze for creating standalone executables.

## Problem with Hard-coded Paths

When Python applications are packaged with PyInstaller, the file structure changes significantly:

- In **development**: Files are in their original locations relative to the source code
- In **PyInstaller bundle**: Files are extracted to a temporary directory accessible via `sys._MEIPASS`

### Before (Broken in PyInstaller)

```python
# BROKEN: Will fail in PyInstaller/cx_Freeze
config_path = "config/settings.ini"
template_path = "./templates/report.html"
log_path = Path(__file__).resolve().parent / "data" / "logs"
```

Problems:
- Hard-coded relative paths break when working directory changes
- `Path(__file__)` points to temporary PyInstaller directory
- Resources may not be bundled or accessible

## Solution: Resource Discovery Pattern

### Resource Utilities (`flowproc/resource_utils.py`)

The application now includes utility functions for PyInstaller-compatible resource discovery:

```python
from flowproc.resource_utils import get_resource_path, get_data_path, get_package_root

# Works in both development and PyInstaller
config_path = get_resource_path("config/settings.ini")
template_path = get_resource_path("templates/report.html")
log_path = get_data_path("logs")
```

### Available Functions

#### `get_resource_path(relative_path)`
- Get path to read-only resources (templates, configs, etc.)
- Uses `sys._MEIPASS` in PyInstaller, package directory in development
- Example: `get_resource_path("resources/icon.icns")`

#### `get_data_path(relative_path="")`
- Get path for writable data files (logs, user configs, etc.)
- Uses directory near executable in PyInstaller, package directory in development
- Creates parent directories automatically
- Example: `get_data_path("logs/processing.log")`

#### `get_package_root()`
- Get the package root directory
- Returns `sys._MEIPASS` in PyInstaller, package directory in development

#### `ensure_writable_dir(dir_path)`
- Ensure a directory exists and is writable
- Handles permission errors gracefully

## Updated Components

### 1. Logging Configuration (`logging_config.py`)

**Before:**
```python
resolved_root = Path(__file__).resolve().parent
log_path = resolved_root / 'data' / 'logs'
```

**After:**
```python
from .resource_utils import get_data_path, ensure_writable_dir

log_path = get_data_path('logs')
ensure_writable_dir(log_path)
```

### 2. Entry Points (`__main__.py`, `gui.py`)

**Before:**
```python
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
```

**After:**
```python
from .resource_utils import get_package_root

# Only adjust sys.path in development mode
if not hasattr(sys, '_MEIPASS'):
    package_root = get_package_root()
    parent_dir = package_root.parent
    sys.path.insert(0, str(parent_dir))
```

### 3. PyInstaller Configuration (`run.sh`)

Updated to include resources and new module:

```bash
pyinstaller --windowed \
            --add-data "$(pwd)/flowproc:flowproc" \
            --add-data "$(pwd)/flowproc/resources:flowproc/resources" \
            --add-data "$(pwd)/logs:logs" \
            --hidden-import flowproc.resource_utils \
            # ... other options
```

## Testing Resource Discovery

Use the included test script to verify resource discovery:

```bash
cd flowproc-project
python3 test_resource_discovery.py
```

**Development Output:**
```
=== Resource Discovery Test ===
Running in PyInstaller: False
Package root: /path/to/flowproc
Resources found: ['icon.icns', 'entitlements.plist']
Data directory: /path/to/flowproc/data
```

**PyInstaller Output:**
```
=== Resource Discovery Test ===
Running in PyInstaller: True
PyInstaller temp path: /tmp/_MEI123456
Package root: /tmp/_MEI123456
Resources found: ['icon.icns', 'entitlements.plist']
Data directory: /path/to/executable/data
```

## Building the Executable

1. **Install dependencies:**
   ```bash
   cd flowproc-project
   pip install . pyinstaller
   ```

2. **Build the executable:**
   ```bash
   ./run.sh
   ```

3. **Test the executable:**
   ```bash
   ./dist/FlowCytometryProcessor.app/Contents/MacOS/FlowCytometryProcessor
   ```

## Best Practices

### DO:
- ✅ Use `get_resource_path()` for read-only resources
- ✅ Use `get_data_path()` for writable data files
- ✅ Test both development and packaged modes
- ✅ Include all resources in PyInstaller `--add-data`

### DON'T:
- ❌ Use `Path(__file__).parent` for resource discovery
- ❌ Use hard-coded relative paths like `"config/settings.ini"`
- ❌ Assume working directory location
- ❌ Forget to add new modules to `--hidden-import`

## Troubleshooting

### Resource Not Found
- Verify resource is included in `--add-data`
- Check if path separators are correct for your OS
- Use `test_resource_discovery.py` to debug paths

### Import Errors
- Add missing modules to `--hidden-import`
- Check if module uses conditional imports

### Permission Errors
- Use `get_data_path()` for writable files, not `get_resource_path()`
- Ensure executable has write permissions to data directory

### Path Issues on macOS
- The utility handles `.app` bundle structure automatically
- Data files are placed relative to the `.app` directory, not inside it 