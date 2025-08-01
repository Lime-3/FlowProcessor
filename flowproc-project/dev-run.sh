#!/bin/bash

# Development run script for FlowProcessor
# This script activates the virtual environment and runs the application

set -e  # Exit on any error

# Navigate to the script's directory
cd "$(dirname "$0")" || exit

echo "🚀 Starting FlowProcessor Development Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'make setup' first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if package is installed
if ! python -c "import flowproc" 2>/dev/null; then
    echo "📦 Installing package in development mode..."
    pip install -e .
fi

# Run the application
echo "🎯 Launching FlowProcessor..."
python -m flowproc 