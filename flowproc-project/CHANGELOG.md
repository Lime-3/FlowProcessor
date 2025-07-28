# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-01-XX

### Added
- Async GUI support for improved responsiveness
- Vectorized data aggregation for 5-10x performance improvements
- Enhanced visualization capabilities with Plotly
- Comprehensive test suite with pytest-qt integration
- Pre-commit hooks for automated code quality checks
- Type hints throughout the codebase
- Modern packaging configuration with pyproject.toml
- Development tools: black, flake8, mypy, isort
- Performance profiling tools: memory-profiler, line-profiler

### Changed
- Major version bump to 2.0.0 for async and vectorized features
- Updated to Python 3.13+ requirement
- Modernized dependency management
- Improved error handling and validation
- Enhanced documentation and code organization

### Fixed
- Removed self-referential dependency in requirements.txt
- Fixed version consistency across all packaging files
- Improved test coverage and reliability

### Technical
- Updated setuptools to >=68.0
- Added comprehensive pytest configuration
- Implemented proper package metadata
- Added MANIFEST.in for complete file inclusion
- Enhanced build system configuration

## [1.0.41] - Previous Version

### Features
- Basic flow cytometry data processing
- CSV to Excel conversion
- Simple GUI interface
- Data parsing and validation

### Dependencies
- Core scientific Python stack (numpy, pandas, scikit-learn)
- PySide6 for GUI
- openpyxl for Excel export 