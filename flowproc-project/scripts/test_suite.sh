#!/bin/bash

# Test Suite Runner for FlowProcessor
# This script runs the complete testing suite for validation

set -e  # Exit on any error

echo "🧪 Running FlowProcessor test suite..."

# Change to the project directory
cd "$(dirname "$0")/.."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected. Tests may fail."
    echo "   Activate your virtual environment: source venv/bin/activate"
fi

# Run unit tests
echo "📋 Running unit tests..."
if ! pytest tests/unit/ -v --tb=short; then
    echo "❌ Unit tests failed!"
    exit 1
fi

# Run integration tests
echo "🔗 Running integration tests..."
if ! pytest tests/integration/ -v --tb=short; then
    echo "❌ Integration tests failed!"
    exit 1
fi

# Run performance tests (if they exist)
if [ -d "tests/performance" ]; then
    echo "⚡ Running performance tests..."
    if ! pytest tests/performance/ -v --tb=short; then
        echo "❌ Performance tests failed!"
        exit 1
    fi
fi

# Run coverage report
echo "📊 Generating coverage report..."
if ! pytest --cov=flowproc --cov-report=term-missing --tb=short; then
    echo "❌ Coverage test failed!"
    exit 1
fi

# Run specific test files if they exist
if [ -f "test_exception_handling.py" ]; then
    echo "🛡️  Running exception handling tests..."
    if ! pytest test_exception_handling.py -v --tb=short; then
        echo "❌ Exception handling tests failed!"
        exit 1
    fi
fi

if [ -f "test_metric_selector.py" ]; then
    echo "📈 Running metric selector tests..."
    if ! pytest test_metric_selector.py -v --tb=short; then
        echo "❌ Metric selector tests failed!"
        exit 1
    fi
fi

if [ -f "test_dialog_width.py" ]; then
    echo "📐 Running dialog width tests..."
    if ! pytest test_dialog_width.py -v --tb=short; then
        echo "❌ Dialog width tests failed!"
        exit 1
    fi
fi

if [ -f "test_timecourse_width.py" ]; then
    echo "⏱️  Running timecourse width tests..."
    if ! pytest test_timecourse_width.py -v --tb=short; then
        echo "❌ Timecourse width tests failed!"
        exit 1
    fi
fi

echo "✅ All tests passed successfully!"
echo "🚀 Ready to commit!" 