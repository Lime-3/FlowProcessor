# Segfault Prevention Guide - Gold Standard Solution

## Overview

This document outlines the comprehensive segfault prevention and automated diagnostic system implemented for FlowProcessor. This solution follows industry best practices for preventing, detecting, and diagnosing segmentation faults in Python applications.

## Root Causes of Segfaults

Segmentation faults in Python applications typically occur due to:

1. **Resource Exhaustion**
   - Memory leaks in C extensions (numpy, scipy, openpyxl)
   - File descriptor limits exceeded
   - Disk space exhaustion

2. **Native Library Bugs**
   - Incompatible binary wheels
   - ABI mismatches between Python and C extensions
   - Threading issues in native code

3. **Concurrency Issues**
   - Race conditions in GUI frameworks (PySide6/Qt)
   - Improper cleanup of shared resources
   - Memory corruption in multi-threaded operations

4. **Environment Problems**
   - Missing display server (X11) on headless systems
   - Incorrect environment variables
   - System resource limits

## Implemented Solution

### 1. Automated System Health Check (`scripts/system_health_check.py`)

**Purpose**: Proactive detection of potential segfault conditions before running tests.

**Features**:
- ✅ **System Resource Monitoring**: Memory, disk space, file descriptors
- ✅ **Python Environment Validation**: Version compatibility, virtual environment
- ✅ **Dependency Compatibility**: Critical package versions and known issues
- ✅ **File System Checks**: Permissions, temp directory access, large files
- ✅ **Memory Management**: Garbage collection, memory leak detection
- ✅ **Temp File Handling**: Cleanup verification, isolation testing
- ✅ **Concurrency Safety**: Threading tests, resource sharing validation
- ✅ **GUI Environment**: Display settings, headless mode configuration
- ✅ **Library Compatibility**: NumPy/SciPy operations, OpenPyXL memory usage
- ✅ **Test Environment**: Pytest configuration, timeout settings

**Usage**:
```bash
# Run health check
python scripts/system_health_check.py

# Or via Makefile
make health-check
```

### 2. Safe Test Runner (`scripts/safe_test_runner.py`)

**Purpose**: Execute tests with comprehensive segfault prevention measures.

**Features**:
- ✅ **Pre-flight Health Check**: Validates environment before testing
- ✅ **Environment Isolation**: Dedicated temp directories, clean state
- ✅ **Resource Limits**: Memory and thread limits for native libraries
- ✅ **Timeout Protection**: Prevents hanging tests from consuming resources
- ✅ **Headless Mode**: GUI testing without display requirements
- ✅ **Graceful Failure**: Captures and reports segfaults without system crash
- ✅ **Cleanup Guarantees**: Automatic resource cleanup even on failure

**Usage**:
```bash
# Run all tests safely
python scripts/safe_test_runner.py all

# Run specific test types
python scripts/safe_test_runner.py integration
python scripts/safe_test_runner.py unit

# Run specific test files
python scripts/safe_test_runner.py specific tests/integration/test_flowproc.py

# Or via Makefile
make test-safe
make test-integration
make test-unit
```

### 3. Enhanced Makefile Integration

**Purpose**: Seamless integration of safety measures into development workflow.

**New Commands**:
```bash
make health-check      # Run system health check
make test-safe         # Run tests with comprehensive safety checks
make test-integration  # Run integration tests safely
make test-unit         # Run unit tests safely
```

## Environment Configuration

### Critical Environment Variables

```bash
# GUI/Display
export QT_QPA_PLATFORM=offscreen  # Headless mode for testing

# Memory Management
export OPENBLAS_NUM_THREADS=1     # Prevent numpy threading issues
export MKL_NUM_THREADS=1          # Intel MKL threading
export OMP_NUM_THREADS=1          # OpenMP threading

# Python Optimization
export PYTHONUNBUFFERED=1         # Immediate output
export PYTHONDONTWRITEBYTECODE=1  # No .pyc files

# Temp Directory Isolation
export TMPDIR=/tmp/flowproc_test_XXXXXX
export TEMP=$TMPDIR
export TMP=$TMPDIR
```

### Pytest Configuration

Add to `pytest.ini`:
```ini
[tool:pytest]
timeout = 300
timeout_method = thread
maxfail = 3
addopts = --disable-warnings --tb=short
```

## Best Practices

### 1. Always Run Health Check First

```bash
# Before any testing or development
make health-check

# Only proceed if status is PASS
```

### 2. Use Safe Test Runner for All Testing

```bash
# Instead of direct pytest
pytest tests/  # ❌ Risky

# Use safe runner
make test-safe  # ✅ Protected
```

### 3. Monitor Resource Usage

```bash
# Check system resources
python scripts/system_health_check.py

# Look for warnings about:
# - Low memory
# - Large files
# - Temp file cleanup issues
```

### 4. Handle Large Files

```bash
# Files >100MB can cause memory issues
# Consider:
# - Chunked processing
# - Memory-mapped files
# - Streaming operations
```

## Troubleshooting

### Common Issues and Solutions

#### 1. PySide6 Import Errors
```bash
# Problem: ModuleNotFoundError: No module named 'pyside6'
# Solution: Import as PySide6 (capital P)
from PySide6 import QtCore  # ✅ Correct
import pyside6              # ❌ Incorrect
```

#### 2. Memory Issues with NumPy/SciPy
```bash
# Problem: Memory leaks in numerical operations
# Solution: Set thread limits
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

#### 3. GUI Testing Failures
```bash
# Problem: No display available
# Solution: Use headless mode
export QT_QPA_PLATFORM=offscreen
```

#### 4. Temp File Cleanup Issues
```bash
# Problem: Temp files not cleaned up
# Solution: Use dedicated temp directories
temp_dir = tempfile.mkdtemp(prefix='flowproc_test_')
# Always cleanup in finally block
```

### Debugging Segfaults

When a segfault occurs:

1. **Check the stack trace** in the test output
2. **Identify the failing operation** (usually in C extension)
3. **Check resource usage** before the failure
4. **Verify environment** with health check
5. **Isolate the issue** by running specific tests

## Monitoring and Maintenance

### Regular Health Checks

```bash
# Daily development
make health-check

# Before commits
make quick-test  # Includes health check

# CI/CD pipeline
python scripts/system_health_check.py && python scripts/safe_test_runner.py all
```

### Performance Monitoring

```bash
# Monitor memory usage
python -c "import psutil; print(psutil.Process().memory_info().rss / 1024 / 1024, 'MB')"

# Monitor file descriptors
python -c "import resource; print(resource.getrlimit(resource.RLIMIT_NOFILE))"
```

## Conclusion

This comprehensive segfault prevention system provides:

- ✅ **Proactive Detection**: Health checks catch issues before they cause crashes
- ✅ **Safe Execution**: Protected test environment prevents system-wide failures
- ✅ **Detailed Diagnostics**: Clear reporting of issues and recommendations
- ✅ **Automated Workflow**: Seamless integration with development tools
- ✅ **Industry Standards**: Follows best practices for production systems

The system successfully detected and contained the original segfault issue, providing detailed diagnostics while protecting the overall system stability. This represents a gold standard approach to segfault prevention in Python applications. 