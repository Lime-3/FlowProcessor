#!/bin/bash

# Setup script for pre-commit hooks
# This script installs pre-commit and configures the testing hooks

set -e  # Exit on any error

echo "🔧 Setting up pre-commit hooks for FlowProcessor..."

# Change to the project directory
cd "$(dirname "$0")/.."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Error: Virtual environment not activated!"
    echo "   Please activate your virtual environment first:"
    echo "   source venv/bin/activate"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
else
    echo "✅ pre-commit already installed"
fi

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Install additional dependencies for hooks
echo "📚 Installing hook dependencies..."
pip install black flake8 isort mypy pytest-cov

# Verify installation
echo "🔍 Verifying pre-commit installation..."
pre-commit --version

echo "✅ Pre-commit hooks setup complete!"
echo ""
echo "📋 Available commands:"
echo "   pre-commit run --all-files    # Run all hooks on all files"
echo "   pre-commit run                # Run hooks on staged files"
echo "   pre-commit run pytest         # Run only pytest hook"
echo "   pre-commit run test-coverage  # Run only coverage hook"
echo ""
echo "🚀 Now when you commit, the testing suite will run automatically!" 