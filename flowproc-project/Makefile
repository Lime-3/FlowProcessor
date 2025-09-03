# FlowProcessor Makefile
# Common commands for development and installation

.PHONY: help install install-dev install-test clean test run setup venv pre-commit-setup pre-commit-run pre-commit-clean quick-test build build-wheel build-sdist check dist-clean format lint type-check pyinstaller pyinstaller-clean build-prod build-prod-wheel build-prod-sdist pyinstaller-prod

# Default target
help:
	@echo "FlowProcessor vV1 - Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install      - Install the package"
	@echo "  install-dev  - Install with development dependencies"
	@echo "  install-test - Install with test dependencies"
	@echo "  setup        - Full setup with virtual environment"
	@echo "  venv         - Create virtual environment"
	@echo ""
	@echo "Development:"
	@echo "  test         - Run tests with safety checks"
	@echo "  test-safe    - Run tests with comprehensive safety checks"
	@echo "  test-integration - Run integration tests with safety checks"
	@echo "  test-unit    - Run unit tests with safety checks"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  test-selenium - Test Selenium image export"
	@echo "  health-check - Run system health check"
	@echo "  quick-test   - Quick test suite (tests + linting + type checking)"
	@echo "  clean        - Clean build artifacts"
	@echo "  run          - Run the application"
	@echo ""
	@echo "Code Quality:"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run flake8 linting"
	@echo "  type-check   - Run mypy type checking"
	@echo "  check        - Run all code quality checks"
	@echo ""
	@echo "Building:"
	@echo "  build        - Build the package"
	@echo "  build-wheel  - Build wheel distribution"
	@echo "  build-sdist  - Build source distribution"
	@echo "  dist-clean   - Clean distribution files"
	@echo "  pyinstaller  - Build standalone executable with PyInstaller"
	@echo "  pyinstaller-clean - Clean PyInstaller build artifacts"
	@echo ""
	@echo "Production Building (No Tests):"
	@echo "  build-prod   - Build production package (no tests)"
	@echo "  build-prod-quick - Quick production build (no tests, no checks)"
	@echo "  build-prod-wheel - Build production wheel (no tests)"
	@echo "  build-prod-sdist - Build production source dist (no tests)"
	@echo "  pyinstaller-prod - Build production executable (no tests)"
	@echo ""
	@echo "Pre-commit:"
	@echo "  pre-commit-setup - Setup pre-commit hooks"
	@echo "  pre-commit-run   - Run pre-commit hooks"
	@echo "  pre-commit-clean - Clean pre-commit cache"
	@echo ""
	@echo "Examples:"
	@echo "  make install-dev  # Install with dev dependencies"
	@echo "  make setup        # Full setup"
	@echo "  make test         # Run tests"
	@echo "  make quick-test   # Quick test before committing"
	@echo "  make format       # Format code"
	@echo "  make build        # Build package"
	@echo "  make build-prod   # Build production package (no tests)"
	@echo "  make build-prod-quick # Quick production build"
	@echo "  make pyinstaller  # Build standalone executable"
	@echo "  make pyinstaller-prod # Build production executable (no tests)"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-test:
	pip install -e ".[test]"

install-all:
	pip install -e ".[dev,test]"

# Setup targets
setup: venv
	@echo "Setting up FlowProcessor vV1..."
	@source venv/bin/activate && pip install --upgrade pip
	@source venv/bin/activate && pip install -e ".[dev]"
	@echo "Setup complete! Activate with: source venv/bin/activate"

venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Development targets
test:
	@echo "Running tests with safety checks..."
	@python scripts/safe_test_runner_v2.py all

test-cov:
	@echo "Running tests with coverage and safety checks..."
	@pytest --cov=flowproc --cov-report=html --cov-report=term-missing

test-selenium:
	@echo "Testing Selenium image export functionality..."
	@python -c "from flowproc.domain.visualization.plotly_renderer import PlotlyRenderer; import plotly.graph_objects as go; fig = go.Figure(data=go.Scatter(x=[1,2,3], y=[1,2,3])); renderer = PlotlyRenderer(); renderer.export_to_png_selenium(fig, 'test_selenium.png'); import os; os.remove('test_selenium.png'); print('✅ Selenium export test passed')"

test-safe:
	@echo "Running tests with comprehensive safety checks..."
	@python scripts/safe_test_runner_v2.py all

test-safe-only:
	@echo "Running only safe tests..."
	@python scripts/safe_test_runner_v2.py safe

test-integration:
	@echo "Running integration tests with safety checks..."
	@python scripts/safe_test_runner.py integration

test-unit:
	@echo "Running unit tests with safety checks..."
	@python scripts/safe_test_runner.py unit

health-check:
	@echo "Running system health check..."
	@python scripts/system_health_check.py

quick-test:
	@echo "Running quick test suite..."
	@./scripts/quick-test.sh

# Code quality targets
format:
	@echo "Formatting code with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

lint:
	@echo "Running flake8 linting..."
	flake8 flowproc tests

type-check:
	@echo "Running mypy type checking..."
	mypy flowproc

check: format lint type-check test
	@echo "✅ All code quality checks passed!"

# Build targets
build:
	@echo "Building FlowProcessor package..."
	python -m build

build-wheel:
	@echo "Building wheel distribution..."
	python -m build --wheel

build-sdist:
	@echo "Building source distribution..."
	python -m build --sdist

# Production build targets (no tests)
build-prod:
	@echo "Building FlowProcessor production package (no tests)..."
	@./scripts/build_production.sh

build-prod-quick:
	@echo "Quick production build (no tests, no checks)..."
	@python -m build

build-prod-wheel:
	@echo "Building production wheel distribution (no tests)..."
	python -m build --wheel

build-prod-sdist:
	@echo "Building production source distribution (no tests)..."
	python -m build --sdist

dist-clean:
	@echo "Cleaning distribution files..."
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

clean: dist-clean
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

run:
	python -m flowproc

# Pre-commit targets
pre-commit-setup:
	@echo "Setting up pre-commit hooks..."
	@./scripts/setup-pre-commit.sh

pre-commit-run:
	@echo "Running pre-commit hooks..."
	@pre-commit run --all-files

pre-commit-clean:
	@echo "Cleaning pre-commit cache..."
	@pre-commit clean

# Quick install scripts
quick-install:
	./pip-install.sh

interactive-install:
	./install.sh

setup-script:
	./setup.sh 

# PyInstaller targets
pyinstaller:
	@echo "Building standalone executable with PyInstaller..."
	@./scripts/build_pyinstaller.sh

pyinstaller-prod:
	@echo "Building production standalone executable with PyInstaller (no tests)..."
	@./scripts/build_pyinstaller.sh --no-checks

pyinstaller-clean:
	@echo "Cleaning PyInstaller build artifacts..."
	@rm -rf build/pyinstaller/
	@rm -rf dist/pyinstaller/
	@echo "PyInstaller build artifacts cleaned" 