# FlowProcessor

A high-performance tool for processing flow cytometry CSV data with async GUI support and vectorized data aggregation.

## Features

- **High Performance**: Vectorized data aggregation for 5-10x performance improvements
- **Async GUI**: Responsive PySide6-based interface with async processing
- **Data Processing**: Advanced CSV parsing and Excel export capabilities
- **Visualization**: Interactive plots with Plotly integration
- **Type Safety**: Comprehensive type hints throughout the codebase
- **Testing**: Extensive test suite with pytest-qt integration

## Installation

### Prerequisites

- Python 3.13 or higher
- pip

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/FlowProcessor.git
cd FlowProcessor/flowproc-project

# Install with development dependencies
pip install -e ".[dev]"
```

### Development Setup

```bash
# Create virtual environment and install
make setup

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

### GUI Application

```bash
# Run the GUI application
flowproc

# Or directly with Python
python -m flowproc
```

### Programmatic usage

```python
from flowproc.domain.visualization.flow_cytometry_visualizer import plot
from flowproc.domain.parsing import load_and_parse_df

# Load and parse CSV data
df, _ = load_and_parse_df("your_data.csv")

# Create visualizations
fig = plot(df, y="Freq. of Parent")
fig.write_html("output.html")
```

## Development

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Run all quality checks
make check
```

### Testing

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Quick test suite
make quick-test
```

### Building

```bash
# Build package
make build

# Build wheel distribution
make build-wheel

# Build source distribution
make build-sdist

# Build standalone executable with PyInstaller
make pyinstaller

# Clean PyInstaller build artifacts
make pyinstaller-clean
```

### Standalone Executables

The project includes PyInstaller integration for creating standalone executables that don't require Python installation.

```bash
# Quick build (recommended)
make pyinstaller

# Build without tests
./scripts/build_pyinstaller.sh --no-tests

# Clean build artifacts
make pyinstaller-clean
```

After building, you'll find the executable in `dist/pyinstaller/FlowProcessor/`.

For detailed PyInstaller documentation, see [PYINSTALLER_GUIDE.md](PYINSTALLER_GUIDE.md).

### Pre-commit Hooks

```bash
# Setup pre-commit hooks
make pre-commit-setup

# Run pre-commit checks
make pre-commit-run
```

## Project Structure

```
flowproc-project/
├── flowproc/                 # Main package
│   ├── application/         # Application layer
│   ├── core/               # Core models and protocols
│   ├── domain/             # Business logic
│   │   ├── export/         # Excel export functionality
│   │   ├── parsing/        # CSV parsing and validation
│   │   ├── processing/     # Data processing and aggregation
│   │   └── visualization/  # Plotting and visualization
│   ├── infrastructure/     # External integrations
│   └── presentation/       # GUI and CLI interfaces
├── tests/                  # Test suite
├── scripts/                # Build and utility scripts
└── resources/              # Icons and configuration files
```

## Dependencies

### Core Dependencies

- **numpy** >= 1.26.4 - Numerical computing
- **pandas** >= 2.3.1 - Data manipulation
- **PySide6** >= 6.7.0 - GUI framework
- **plotly** >= 5.18.0 - Interactive visualization
- **openpyxl** >= 3.1.5 - Excel file handling
- **scikit-learn** >= 1.7.0 - Machine learning utilities
- **pydantic** >= 2.0.0 - Data validation

### Development Dependencies

- **pytest** >= 8.0.0 - Testing framework
- **pytest-qt** >= 4.3.0 - GUI testing
- **black** >= 24.0.0 - Code formatting
- **flake8** >= 7.0.0 - Linting
- **mypy** >= 1.8.0 - Type checking
- **isort** >= 5.13.0 - Import sorting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `make test`
5. Run code quality checks: `make check`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for a detailed version history.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/FlowProcessor/issues)
- **Documentation**: [Project Wiki](https://github.com/yourusername/FlowProcessor/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/FlowProcessor/discussions) 