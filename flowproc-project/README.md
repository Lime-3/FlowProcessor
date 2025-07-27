# FlowProcessor

A comprehensive tool for processing flow cytometry CSV files into organized Excel workbooks with advanced visualization capabilities.

## Overview

FlowProcessor is a Python application that processes FlowJo CSV exports into well-organized Excel workbooks. It features a modern GUI built with PySide6, command-line interface, and supports time-course studies with automatic tissue detection and parsing.

## Features

- **Data Processing**: Process FlowJo CSV exports into organized Excel workbooks
- **Time-course Studies**: Support for time-course studies with automatic time parsing
- **Tissue Detection**: Automatic tissue detection and parsing
- **Group/Replicate Configuration**: Manual or automatic group/replicate configuration
- **Multiple Interfaces**: GUI (PySide6) and command-line interfaces
- **Advanced Visualization**: Plotly-based interactive visualizations
- **Data Validation**: Comprehensive data validation and error handling
- **Performance Optimized**: Vectorized operations for large datasets
- **Modular Architecture**: Clean separation of concerns with domain-driven design

## Project Structure

The project follows a clean architecture pattern with clear separation of concerns:

```
flowproc/
├── core/                    # Core business logic and models
├── domain/                  # Domain services (parsing, processing, visualization, export)
├── infrastructure/          # Infrastructure layer (config, persistence, monitoring)
├── presentation/            # Presentation layer (CLI and GUI)
├── application/             # Application services and workflows
└── resources/               # Static resources (icons, templates, schemas)
```

## Installation

### Prerequisites
- Python 3.13 or higher
- pip

### Quick Installation Options

#### Option 1: Interactive Installer (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd FlowProcessor/flowproc-project

# Run the interactive installer
./install.sh
```

#### Option 2: Quick Setup Script
```bash
# Clone the repository
git clone <repository-url>
cd FlowProcessor/flowproc-project

# Run the setup script (creates virtual environment)
./setup.sh
```

#### Option 3: Direct pip Install
```bash
# Clone the repository
git clone <repository-url>
cd FlowProcessor/flowproc-project

# Quick pip install
./pip-install.sh

# Or manually
pip install -e .
```

#### Option 4: Install with Extras
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install with test dependencies
pip install -e ".[test]"

# Install with all extras
pip install -e ".[dev,test]"
```

### Traditional Installation Methods

#### From pyproject.toml
```bash
pip install .
```

#### From setup.py
```bash
pip install .
```

#### From requirements.txt
```bash
pip install -r requirements.txt
```

### Dependencies
The application requires the following key dependencies:
- **numpy>=1.26.4**: Numerical computing
- **pandas>=2.3.1**: Data manipulation
- **openpyxl>=3.1.5**: Excel file handling
- **PySide6>=6.7.0**: GUI framework
- **plotly>=5.18.0**: Interactive visualizations
- **kaleido>=1.0.0**: Static image export (PNG, PDF, SVG)
- **scikit-learn>=1.7.0**: Data transformations
- **pydantic>=2.0.0**: Data validation and settings

## Usage

### GUI Mode (Recommended)
```bash
# Launch the GUI application
python -m flowproc.presentation.gui.main

# Or use the entry point
flowproc
```

### Command Line Mode
```bash
# Process files from command line
python -m flowproc.presentation.cli.cli --input-dir /path/to/csv/files --output-dir /path/to/output
```

### Programmatic Usage
```python
from flowproc.domain.parsing.service import ParseService
from flowproc.domain.processing.service import DataProcessingService
from flowproc.domain.export.service import ExportService

# Initialize services
parse_service = ParseService()
processing_service = DataProcessingService()
export_service = ExportService()

# Process your data
# ... implementation details
```

## Image Export

FlowProcessor supports high-quality static image export using the Kaleido engine:

### Supported Formats
- **PNG**: High-resolution raster images (default)
- **PDF**: Vector graphics for publications
- **SVG**: Scalable vector graphics

### Export Features
- **High DPI**: 600 DPI equivalent output for publication quality
- **Customizable**: Configurable width, height, and scale
- **GUI Integration**: Save plots directly from the visualization interface
- **Programmatic**: Export via Python API

### Example Usage
```python
from flowproc.domain.visualization.plotly_renderer import PlotlyRenderer

renderer = PlotlyRenderer()
fig = renderer.render_scatter(data, x_col='x', y_col='y')

# Export to different formats
renderer.export_to_image(fig, 'plot.png', format='png', width=800, height=600)
renderer.export_to_image(fig, 'plot.pdf', format='pdf')
renderer.export_to_image(fig, 'plot.svg', format='svg')
```

## Supported FlowJo Metrics

The tool recognizes and processes the following FlowJo table export metrics:
- Frequency of Parent
- Frequency of Live  
- Median
- Mean
- Count
- Geometric Mean (GeoMean)
- Coefficient of Variation (CV)
- Standard Deviation (SD)
- Minimum (Min)
- Maximum (Max)
- Sum
- Mode
- Range

## Logging

The application automatically creates a `logs/` directory in the current working directory and writes log files to `logs/processing.log`. This directory is created automatically if it doesn't exist, making the tool suitable for distribution.

### Log File Location
- **Default**: `./logs/processing.log` (relative to current working directory)
- **Created automatically**: The `logs/` directory is created if it doesn't exist
- **Distribution ready**: Uses relative paths, no hardcoded absolute paths

## Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=flowproc

# Type checking
mypy flowproc/
```

### Project Architecture

The application follows a clean architecture pattern:

- **Core Layer**: Contains business models, exceptions, and protocols
- **Domain Layer**: Contains business logic for parsing, processing, visualization, and export
- **Infrastructure Layer**: Handles configuration, persistence, and monitoring
- **Presentation Layer**: Provides CLI and GUI interfaces
- **Application Layer**: Orchestrates workflows and handles application-level concerns

### Testing

The project includes comprehensive testing:
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Performance Tests**: Benchmark critical operations
- **GUI Tests**: Test user interface functionality

## Recent Improvements

- **Enhanced Error Handling**: Comprehensive exception handling across all modules
- **Performance Optimization**: Vectorized operations for large datasets
- **Modular Architecture**: Clean separation of concerns with domain-driven design
- **Advanced Visualization**: Plotly-based interactive charts and graphs
- **Data Validation**: Robust input validation using Pydantic
- **Configuration Management**: YAML-based configuration system
- **Monitoring**: Health checks and performance metrics
- **Type Safety**: Full type annotations and MyPy support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
