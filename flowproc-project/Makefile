# FlowProcessor Makefile
# Common commands for development and installation

.PHONY: help install install-dev install-test clean test run setup venv pre-commit-setup pre-commit-run pre-commit-clean quick-test build build-wheel build-sdist check dist-clean format lint type-check

# Default target
help:
	@echo "FlowProcessor v2.0.0 - Available commands:"
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
	@echo "  test-kaleido - Test Kaleido image export"
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
	@echo "Setting up FlowProcessor v2.0.0..."
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

test-kaleido:
	@echo "Testing Kaleido image export functionality..."
	@python -c "import plotly.graph_objects as go; import plotly.io as pio; fig = go.Figure(data=go.Scatter(x=[1,2,3], y=[1,2,3])); fig.write_image('test_kaleido.png'); import os; os.remove('test_kaleido.png'); print('✅ Kaleido export test passed')"

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