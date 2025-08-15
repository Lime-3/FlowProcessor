# FlowProcessor Scripts

This directory contains utility scripts for development, testing, and project management.

## Available Scripts

### Testing & Development
- **`test_runner.py`** - Enhanced test runner with isolation and error handling
- **`test_suite.sh`** - Complete test suite runner for validation
- **`setup-pre-commit.sh`** - Pre-commit hooks setup and configuration

### Project Setup
- **`project_setup.sh`** - Comprehensive project setup with multiple installation options
- **`quick_install.sh`** - Fast installation for development environments

## Usage

### Running Tests
```bash
# Run complete test suite
./test_suite.sh

# Run specific test categories with isolation
python test_runner.py safe
python test_runner.py isolated
python test_runner.py gui
python test_runner.py integration
```

### Project Setup
```bash
# Comprehensive setup (recommended for first-time setup)
./project_setup.sh

# Quick development install
./quick_install.sh

# Setup pre-commit hooks
./setup-pre-commit.sh
```

## Script Categories

- **Core Testing**: `test_runner.py`, `test_suite.sh`
- **Development Tools**: `setup-pre-commit.sh`
- **Installation**: `project_setup.sh`, `quick_install.sh`

## Notes

- All scripts require Python 3.13+ and a virtual environment
- The `test_runner.py` provides better isolation for different test types
- `project_setup.sh` offers multiple installation strategies
- `quick_install.sh` is optimized for fast development setup
