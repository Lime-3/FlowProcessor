# FlowProcessor Makefile
# Common commands for development and installation

.PHONY: help install install-dev install-test clean test run setup venv

# Default target
help:
	@echo "FlowProcessor - Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install      - Install the package"
	@echo "  install-dev  - Install with development dependencies"
	@echo "  install-test - Install with test dependencies"
	@echo "  setup        - Full setup with virtual environment"
	@echo "  venv         - Create virtual environment"
	@echo ""
	@echo "Development:"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  test-kaleido - Test Kaleido image export"
	@echo "  clean        - Clean build artifacts"
	@echo "  run          - Run the application"
	@echo ""
	@echo "Examples:"
	@echo "  make install-dev  # Install with dev dependencies"
	@echo "  make setup        # Full setup"
	@echo "  make test         # Run tests"

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
	@echo "Setting up FlowProcessor..."
	@source venv/bin/activate && pip install --upgrade pip
	@source venv/bin/activate && pip install -e ".[dev]"
	@echo "Setup complete! Activate with: source venv/bin/activate"

venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Development targets
test:
	pytest

test-cov:
	pytest --cov=flowproc --cov-report=html

test-kaleido:
	@echo "Testing Kaleido image export functionality..."
	@python -c "import plotly.graph_objects as go; import plotly.io as pio; fig = go.Figure(data=go.Scatter(x=[1,2,3], y=[1,2,3])); fig.write_image('test_kaleido.png'); import os; os.remove('test_kaleido.png'); print('✅ Kaleido export test passed')"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run:
	python -m flowproc

# Quick install scripts
quick-install:
	./pip-install.sh

interactive-install:
	./install.sh

setup-script:
	./setup.sh 