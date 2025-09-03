# FlowProcessor Project Structure

## Overview

FlowProcessor is a high-performance Python application for processing flow cytometry CSV data with async GUI support and vectorized data aggregation. The project follows a clean architecture pattern with clear separation of concerns across multiple layers.

## Project Architecture

The project implements a **Clean Architecture** pattern with the following layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│                 (GUI, CLI, Web Interfaces)                  │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                        │
│              (Use Cases, Workflows, Handlers)               │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                            │
│           (Business Logic, Core Entities, Services)         │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                       │
│            (External Dependencies, Persistence)             │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

### Root Level
```
flowproc-project/
├── flowproc/                 # Main application package
├── tests/                    # Test suite
├── config/                   # Configuration files
├── scripts/                  # Build and utility scripts
├── docs/                     # Documentation
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── pyproject.toml           # Project configuration
├── Makefile                 # Build automation
└── dev-run.sh               # Development runner script
```

### Core Application Package (`flowproc/`)

#### Main Entry Points
- `__main__.py` - CLI entry point (`python -m flowproc`)
- `__init__.py` - Package initialization and version info
- `config.py` - Configuration management
- `logging_config.py` - Logging configuration
- `resource_utils.py` - Resource management utilities
- `setup_dependencies.py` - Dependency setup and validation

#### Application Layer (`application/`)
```
application/
├── __init__.py
├── container.py              # Dependency injection container
├── exceptions.py             # Application-specific exceptions
├── handlers/                 # Event and error handlers
│   ├── __init__.py
│   ├── error_handler.py
│   └── event_handler.py
└── workflows/                # Business process workflows
    ├── __init__.py
    ├── data_processing.py    # Data processing workflows
    └── visualization.py      # Visualization workflows
```

#### Core Layer (`core/`)
```
core/
├── __init__.py
├── constants.py              # Application constants
├── exceptions.py             # Core exceptions
├── models.py                 # Core data models
├── protocols.py              # Abstract base classes
└── validation.py             # Core validation logic
```

#### Domain Layer (`domain/`)
The domain layer contains the core business logic organized by functionality:

```
domain/
├── __init__.py
├── aggregation/              # Data aggregation services
│   ├── __init__.py
│   ├── core.py              # Aggregation algorithms
│   ├── service.py           # Aggregation service
│   └── README.md
├── export/                   # Data export functionality
│   ├── __init__.py
│   ├── excel_exporter.py    # Excel export service
│   ├── pdf_exporter.py      # PDF export service
│   └── [additional export modules]
├── parsing/                  # Data parsing and loading
│   ├── __init__.py
│   ├── csv_parser.py        # CSV parsing logic
│   ├── data_loader.py       # Data loading utilities
│   └── [additional parsing modules]
├── processing/               # Data processing operations
│   ├── __init__.py
│   ├── data_processor.py    # Main processing logic
│   └── [additional processing modules]
├── validation/               # Data validation
│   ├── __init__.py
│   └── input_validator.py   # Input validation logic
└── visualization/            # Data visualization
    ├── __init__.py
    ├── flow_cytometry_visualizer.py  # Main visualization
    ├── plot_generator.py    # Plot generation utilities
    └── [additional visualization modules]
```

#### Infrastructure Layer (`infrastructure/`)
```
infrastructure/
├── __init__.py
├── config/                   # Infrastructure configuration
│   ├── __init__.py
│   └── settings.py
├── monitoring/               # Application monitoring
│   ├── __init__.py
│   ├── performance.py       # Performance monitoring
│   └── health.py            # Health checks
└── persistence/              # Data persistence
    ├── __init__.py
    └── storage.py           # Storage abstractions
```

#### Presentation Layer (`presentation/`)
```
presentation/
├── __init__.py
├── cli/                     # Command-line interface
│   ├── __init__.py
│   └── cli.py              # CLI implementation
└── gui/                     # Graphical user interface
    ├── __init__.py
    ├── main.py              # Main GUI entry point
    ├── main_window.py       # Main window implementation
    ├── dialogs/             # Dialog windows
    ├── widgets/             # Custom widgets
    ├── models/              # GUI data models
    ├── views/               # View implementations
    ├── controllers/         # GUI controllers
    └── utils/               # GUI utilities
```

#### Resources (`resources/`)
```
resources/
├── icons/                   # Application icons
│   ├── icon.icns           # macOS icon
│   └── icon.backup         # Backup icon file
└── entitlements.plist       # macOS entitlements
```

### Test Suite (`tests/`)
```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration
├── fixtures/                # Test fixtures
│   ├── __init__.py
│   └── test_flowproc.csv   # Test data
├── data/                    # Test data files
│   ├── __init__.py
│   └── [various CSV test files]
├── integration/             # Integration tests
│   ├── __init__.py
│   └── [integration test modules]
├── performance/             # Performance tests
│   ├── __init__.py
│   └── benchmark_performance.py
├── unit/                    # Unit tests
│   ├── __init__.py
│   └── [unit test modules]
└── [additional test modules]
```

### Configuration (`config/`)
```
config/
├── config.json              # Application configuration
└── README.md                # Configuration documentation
```

### Scripts (`scripts/`)
```
scripts/
├── build_package.sh         # Package building script
├── project_setup.sh         # Project setup automation
├── quick_install.sh         # Quick installation script
├── safe_test_runner_v2.py   # Safe test execution
├── test_runner.py           # Test execution script
├── test_suite.sh            # Test suite runner
└── setup-pre-commit.sh      # Pre-commit hook setup
```

### Documentation (`docs/`)
```
docs/
├── README.md                # Main documentation
├── BROWSER_CACHING.md       # Browser caching guide
├── PDF_EXPORT.md            # PDF export documentation
├── REFACTORING_SUMMARY.md   # Refactoring documentation
└── VISUALIZATION_PERFORMANCE_OPTIMIZATIONS.md
```

## Key Dependencies

### Core Dependencies
- **Python**: 3.11+ (3.13 recommended)
- **NumPy**: >=1.24.0 - Numerical computing
- **Pandas**: >=2.0.0 - Data manipulation
- **PySide6**: >=6.5.0 - GUI framework
- **Plotly**: >=5.15.0 - Interactive visualizations

### Development Dependencies
- **pytest**: Testing framework
- **pytest-qt**: Qt testing utilities
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

## Build and Development Tools

### Makefile Targets
- `make setup` - Project setup and dependency installation
- `make test` - Run test suite
- `make format` - Format code with black
- `make lint` - Run linting checks
- `make type-check` - Run type checking
- `make check` - Run all quality checks
- `make build` - Build package
- `make clean` - Clean build artifacts

### Package Management
- **pyproject.toml**: Modern Python packaging configuration
- **Briefcase**: Cross-platform application packaging
- **setuptools**: Build system backend

## Entry Points

### GUI Application
```bash
flowproc                    # Main GUI application
flowproc-gui               # Alternative GUI entry point
```

### CLI Application
```bash
flowproc-cli               # Command-line interface
python -m flowproc         # Module execution
```

## Development Workflow

1. **Setup**: Use `make setup` for initial project setup
2. **Development**: Use `dev-run.sh` for development execution
3. **Testing**: Use `make test` for comprehensive testing
4. **Quality**: Use `make check` for code quality validation
5. **Building**: Use `make build` for package creation

## Architecture Principles

1. **Separation of Concerns**: Clear boundaries between layers
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Single Responsibility**: Each module has one clear purpose
4. **Interface Segregation**: Clients depend only on interfaces they use
5. **Open/Closed**: Open for extension, closed for modification

## Performance Characteristics

- **Vectorized Operations**: 5-10x performance improvement over iterative approaches
- **Async Processing**: Non-blocking GUI operations
- **Memory Efficient**: Optimized data structures and algorithms
- **Scalable**: Handles large datasets efficiently

## Platform Support

- **macOS**: Native application with entitlements
- **Windows**: Cross-platform compatibility
- **Linux**: Cross-platform compatibility
- **Offline Operation**: No external CDN dependencies

This structure provides a solid foundation for a maintainable, scalable flow cytometry data processing application with clear separation of concerns and modern Python development practices.
