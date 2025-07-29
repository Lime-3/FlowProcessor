# FlowProcessor Debugging Guide

## Overview

This guide provides comprehensive debugging tools and techniques for FlowProcessor. Your application is working well, but these tools will help you monitor performance and troubleshoot any issues that arise.

## Quick Status Check

Your current environment status: ✅ **HEALTHY**

- ✅ Python 3.13.3 with virtual environment
- ✅ All critical dependencies installed and working
- ✅ FlowProc modules importing successfully
- ✅ System resources adequate (4.8GB RAM available)
- ✅ GUI environment ready

## Debugging Tools

### 1. Quick Diagnostic (`quick_debug.py`)

Run this for a rapid assessment of your environment:

```bash
source venv/bin/activate
python quick_debug.py
```

**What it checks:**
- Python environment and virtual environment
- Critical package imports (numpy, pandas, plotly, etc.)
- Project structure and key files
- FlowProc module imports
- System resources (memory, disk, CPU)
- Log files and their status
- GUI environment readiness

### 2. Enhanced Debug Monitor (`debug_monitor.py`)

Real-time monitoring with multiple modes:

```bash
# Health check only
python debug_monitor.py health

# Run application with monitoring
python debug_monitor.py monitor

# Default: run with monitoring
python debug_monitor.py
```

**Features:**
- Real-time memory and CPU monitoring
- Error detection and logging
- System health checks
- Performance metrics collection
- Enhanced logging to `debug.log`

### 3. System Health Check (`scripts/system_health_check.py`)

Comprehensive system validation:

```bash
python scripts/system_health_check.py
```

**What it validates:**
- System resources and limits
- Python environment compatibility
- Dependency versions and known issues
- File system permissions
- Memory management
- Concurrency safety
- GUI environment configuration

## Common Issues and Solutions

### 1. Application Won't Start

**Symptoms:** GUI doesn't appear, import errors

**Debugging Steps:**
```bash
# 1. Check environment
python quick_debug.py

# 2. Check for import errors
python -c "from flowproc.presentation.gui import create_gui; print('Import OK')"

# 3. Run with verbose logging
python debug_monitor.py monitor
```

**Common Solutions:**
- Ensure virtual environment is activated
- Check PySide6 installation: `pip install PySide6`
- Verify Python version compatibility

### 2. Memory Issues

**Symptoms:** Application becomes slow, crashes, high memory usage

**Debugging Steps:**
```bash
# 1. Monitor memory usage
python debug_monitor.py monitor

# 2. Check for memory leaks
# Look for continuously increasing memory in debug.log

# 3. Check system resources
python scripts/system_health_check.py
```

**Common Solutions:**
- Close large CSV files when not needed
- Restart application periodically
- Check for large temporary files

### 3. File Processing Errors

**Symptoms:** CSV files fail to load, parsing errors

**Debugging Steps:**
```bash
# 1. Check file permissions and format
python quick_debug.py

# 2. Look at processing logs
tail -f flowproc/data/logs/processing.log

# 3. Test with a simple CSV file
```

**Common Solutions:**
- Ensure CSV files are UTF-8 encoded
- Check file permissions
- Verify CSV format (no extra headers/footers)

### 4. GUI Issues

**Symptoms:** Interface not responding, display problems

**Debugging Steps:**
```bash
# 1. Check GUI environment
python quick_debug.py

# 2. Try headless mode for testing
export QT_QPA_PLATFORM=offscreen
python -m flowproc

# 3. Check for Qt errors in logs
grep -i "qt\|gui\|display" flowproc/data/logs/processing.log
```

**Common Solutions:**
- Restart the application
- Check display settings
- Update PySide6 if needed

## Log Analysis

### Key Log Files

1. **`flowproc/data/logs/processing.log`** - Main application logs
2. **`debug.log`** - Enhanced debug information (created by debug_monitor.py)

### Important Log Patterns

**Look for these patterns in logs:**

```bash
# Error patterns
grep -i "error\|exception\|failed" flowproc/data/logs/processing.log

# Warning patterns  
grep -i "warning\|deprecated" flowproc/data/logs/processing.log

# Performance patterns
grep -i "memory\|cpu\|time" flowproc/data/logs/processing.log
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General application flow
- **WARNING**: Potential issues (non-critical)
- **ERROR**: Problems that need attention
- **CRITICAL**: Severe issues requiring immediate action

## Performance Monitoring

### Memory Usage

Monitor memory usage patterns:

```bash
# Real-time monitoring
python debug_monitor.py monitor

# Check memory in logs
grep "Memory:" debug.log
```

**Normal patterns:**
- Initial load: 50-100MB
- File processing: +10-50MB per file
- Peak usage: <500MB for typical workflows

### CPU Usage

Monitor CPU usage:

```bash
# Check CPU patterns
grep "CPU:" debug.log
```

**Normal patterns:**
- Idle: <5%
- File processing: 20-80%
- Visualization: 10-30%

## Troubleshooting Workflow

### Step-by-Step Debugging

1. **Quick Assessment**
   ```bash
   python quick_debug.py
   ```

2. **Health Check**
   ```bash
   python debug_monitor.py health
   ```

3. **Monitor Application**
   ```bash
   python debug_monitor.py monitor
   ```

4. **Analyze Logs**
   ```bash
   tail -f flowproc/data/logs/processing.log
   tail -f debug.log
   ```

5. **Check System Resources**
   ```bash
   python scripts/system_health_check.py
   ```

### Emergency Debugging

If the application is completely unresponsive:

```bash
# 1. Force kill any running instances
pkill -f flowproc

# 2. Clear temporary files
rm -rf /tmp/flowproc_*

# 3. Restart with minimal logging
export FLOWPROC_LOG_LEVEL=ERROR
python -m flowproc

# 4. Check system resources
python scripts/system_health_check.py
```

## Best Practices

### 1. Regular Monitoring

- Run `python quick_debug.py` before starting work
- Use `python debug_monitor.py monitor` for long sessions
- Check logs periodically

### 2. Resource Management

- Close large files when not needed
- Restart application every few hours for long sessions
- Monitor memory usage during large file processing

### 3. Error Prevention

- Always use virtual environment
- Keep dependencies updated
- Test with sample files before processing large datasets

### 4. Log Management

- Regularly check log file sizes
- Archive old logs if needed
- Monitor for error patterns

## Getting Help

If you encounter issues that aren't resolved by this guide:

1. **Collect Information:**
   ```bash
   python quick_debug.py > debug_report.txt
   python scripts/system_health_check.py >> debug_report.txt
   ```

2. **Include Logs:**
   - `flowproc/data/logs/processing.log`
   - `debug.log` (if available)
   - Recent error messages

3. **Document Steps:**
   - What you were doing when the issue occurred
   - Steps to reproduce the problem
   - System information from debug tools

## Summary

Your FlowProcessor environment is healthy and ready for use. The debugging tools provided will help you:

- ✅ Monitor application performance
- ✅ Detect issues early
- ✅ Troubleshoot problems efficiently
- ✅ Maintain optimal performance

Use these tools proactively to ensure smooth operation of your flow cytometry data processing workflows. 