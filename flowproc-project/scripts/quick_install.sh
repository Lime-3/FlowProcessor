#!/bin/bash

# Quick Install Script for FlowProcessor
# Fast installation for development environments

set -e  # Exit on any error

echo "🚀 Quick pip install for FlowProcessor"
echo "======================================"
echo ""

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   Consider creating one with: python3 -m venv venv && source venv/bin/activate"
    echo ""
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# Install the package
echo "📦 Installing FlowProcessor..."
pip install -e .

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To run FlowProcessor:"
echo "  python -m flowproc"
echo ""
echo "Or use the command:"
echo "  flowproc" 