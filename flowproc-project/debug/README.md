# Debug Tools

This directory contains various debugging and diagnostic tools for the FlowProcessor project.

## Files

### `debug.sh`
- **Purpose**: Main debug script for running comprehensive debugging operations
- **Usage**: `./debug.sh [options]`
- **Description**: Shell script that orchestrates various debugging tasks and can be used for automated debugging workflows

### `debug_monitor.py`
- **Purpose**: Real-time monitoring and debugging of the application
- **Usage**: `python debug_monitor.py`
- **Description**: Provides live monitoring capabilities for tracking application performance, memory usage, and system health

### `quick_debug.py`
- **Purpose**: Quick debugging utilities and helper functions
- **Usage**: `python quick_debug.py`
- **Description**: Contains utility functions for rapid debugging and troubleshooting common issues

### `debug_mapping.py`
- **Purpose**: Debugging tools specifically for data mapping operations
- **Usage**: `python debug_mapping.py`
- **Description**: Helps diagnose issues with data mapping, parsing, and transformation processes

### `system_health_check.py`
- **Purpose**: Comprehensive system health and performance analysis
- **Usage**: `python system_health_check.py`
- **Description**: Performs thorough system diagnostics including memory usage, CPU performance, disk space, and application-specific health checks

### `validate_migration.py`
- **Purpose**: Validation tool for migration processes
- **Usage**: `python validate_migration.py`
- **Description**: Validates migration operations and ensures data integrity during system updates

## Usage

1. For general debugging: Run `debug.sh` for automated debugging workflows
2. For real-time monitoring: Use `debug_monitor.py` to track application performance
3. For quick troubleshooting: Use `quick_debug.py` for rapid issue diagnosis
4. For mapping issues: Use `debug_mapping.py` to debug data processing problems
5. For system analysis: Use `system_health_check.py` for comprehensive system diagnostics
6. For migration validation: Use `validate_migration.py` to validate migration processes

## Notes

- These tools are intended for development and debugging purposes
- Some tools may require specific permissions or dependencies
- Always review the output and logs carefully when using these debugging tools 