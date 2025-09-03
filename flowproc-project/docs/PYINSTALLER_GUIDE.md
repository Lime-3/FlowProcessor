# PyInstaller Integration

This document explains how to use PyInstaller to create standalone executables for the FlowProcessor application.

## Overview

PyInstaller is used to package Python applications into standalone executables that can run without requiring Python to be installed on the target system.

## Prerequisites

1. Python 3.11 or higher
2. Virtual environment with all dependencies installed
3. PyInstaller installed: `pip install pyinstaller`

## Quick Start

### Using the Makefile (Recommended)

```bash
# Build standalone executable
make pyinstaller

# Clean PyInstaller build artifacts
make pyinstaller-clean
```

### Using the Build Script Directly

```bash
# Full build with tests
./scripts/build_pyinstaller.sh

# Build without running tests
./scripts/build_pyinstaller.sh --no-tests

# Build without testing the executable
./scripts/build_pyinstaller.sh --no-test-exe

# Only clean previous builds
./scripts/build_pyinstaller.sh --clean-only

# Show help
./scripts/build_pyinstaller.sh --help
```

## Build Process

The PyInstaller build process:

1. **Prerequisites Check**: Verifies Python version and PyInstaller installation
2. **Clean**: Removes previous build artifacts
3. **Dependencies**: Installs/updates required dependencies
4. **Tests**: Runs test suite (optional)
5. **Build**: Creates standalone executable using PyInstaller
6. **Verification**: Checks that executables were created correctly
7. **Testing**: Tests the executable (optional)

## Build Artifacts

After a successful build, you'll find:

- **Linux/macOS**: `dist/pyinstaller/FlowProcessor/FlowProcessor`
- **Windows**: `dist/pyinstaller/FlowProcessor/FlowProcessor.exe`
- **macOS App Bundle**: `dist/pyinstaller/FlowProcessor.app`

## Configuration

### PyInstaller Spec File

The main configuration is in `flowproc.spec`:

- **Entry Point**: `flowproc-project/flowproc/__main__.py`
- **Data Files**: Resources, icons, and documentation
- **Hidden Imports**: All required modules and dependencies
- **Exclusions**: Development and testing modules
- **Platform Specific**: macOS entitlements and app bundle configuration

### Project Configuration

PyInstaller settings in `pyproject.toml`:

```toml
[tool.pyinstaller]
spec-file = "flowproc.spec"
workpath = "build/pyinstaller"
distpath = "dist/pyinstaller"
clean-build = true
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure all dependencies are installed in the virtual environment
2. **Import Errors**: Check that all required modules are listed in `hiddenimports`
3. **Resource Files**: Verify that data files are correctly specified in the spec file
4. **Platform Issues**: Some dependencies may behave differently on different platforms

### Debug Mode

To build with debug information:

```bash
python3 -m PyInstaller flowproc.spec --debug=all
```

### Manual PyInstaller Command

For advanced users, you can run PyInstaller directly:

```bash
python3 -m PyInstaller flowproc.spec \
    --workpath=build/pyinstaller \
    --distpath=dist/pyinstaller \
    --clean \
    --noconfirm
```

## Distribution

### What to Distribute

- **Linux/macOS**: The entire `FlowProcessor` directory
- **Windows**: The entire `FlowProcessor` directory
- **macOS**: The `.app` bundle (recommended) or the directory

### File Sizes

Typical executable sizes:
- **Linux**: ~50-100 MB
- **macOS**: ~60-120 MB  
- **Windows**: ~70-150 MB

### Optimization

To reduce file size:

1. Use `--strip` flag (removes debug symbols)
2. Exclude unnecessary modules in the spec file
3. Use UPX compression (already enabled in spec file)

## Integration with CI/CD

The PyInstaller build can be integrated into continuous integration:

```yaml
# Example GitHub Actions step
- name: Build PyInstaller executable
  run: |
    source venv/bin/activate
    make pyinstaller
```

## Platform-Specific Notes

### macOS

- Requires entitlements file for proper sandboxing
- Creates both executable and `.app` bundle
- May require code signing for distribution

### Windows

- Creates `.exe` executable
- May require antivirus exclusions during development
- Consider using NSIS for installer creation

### Linux

- Creates ELF binary
- May require specific libraries on target systems
- Consider using AppImage for better distribution

## Advanced Configuration

### Custom Hooks

Create custom PyInstaller hooks in `hooks/` directory:

```python
# hooks/hook-custom_module.py
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('custom_module')
```

### Runtime Hooks

Add runtime hooks for initialization:

```python
# runtime_hooks/custom_init.py
import sys
import os

# Custom initialization code
```

### Environment Variables

Set environment variables in the spec file:

```python
# In the Analysis section
a = Analysis(
    # ... other options ...
    runtime_hooks=['runtime_hooks/set_env.py'],
)
```

## Performance Considerations

1. **Startup Time**: PyInstaller executables may have longer startup times
2. **Memory Usage**: Slightly higher memory usage due to bundled dependencies
3. **File I/O**: Resource access may be slower due to extraction from archive

## Security Considerations

1. **Code Obfuscation**: PyInstaller doesn't obfuscate code - consider additional tools
2. **Dependency Scanning**: Regularly scan bundled dependencies for vulnerabilities
3. **Code Signing**: Sign executables for production distribution
4. **Sandboxing**: Use appropriate entitlements and permissions
