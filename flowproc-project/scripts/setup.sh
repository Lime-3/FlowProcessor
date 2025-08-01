#!/bin/bash

# FlowProcessor Setup Script
# This script sets up the virtual environment and installs dependencies

set -e  # Exit on any error

echo "🚀 Setting up FlowProcessor..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $PROJECT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.13 or later."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.13"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python version $PYTHON_VERSION is too old. Please install Python $REQUIRED_VERSION or later."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created at $VENV_DIR"
else
    echo "✅ Virtual environment already exists at $VENV_DIR"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# Install the package in development mode
echo "📦 Installing FlowProcessor in development mode..."
pip install -e .

# Install additional development dependencies if needed
echo "📦 Installing development dependencies..."
pip install pytest pytest-qt pytest-cov pytest-mock

# Verify installation
echo "🔍 Verifying installation..."
python -c "
import sys
import importlib

required_packages = [
    'numpy', 'pandas', 'openpyxl', 'PySide6', 
    'plotly', 'scikit-learn', 'PyYAML', 'pydantic'
]

missing_packages = []
for package in required_packages:
    try:
        importlib.import_module(package)
        print(f'✅ {package} is installed')
    except ImportError:
        missing_packages.append(package)
        print(f'❌ {package} is missing')

if missing_packages:
    print(f'\\n❌ Missing packages: {missing_packages}')
    sys.exit(1)
else:
    print('\\n🎉 All required packages are installed!')
"

# Test the installation
echo "🧪 Testing the installation..."
python -c "
try:
    from flowproc.presentation.gui.main import main
    print('✅ FlowProcessor can be imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "🎉 Setup complete! To run FlowProcessor:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the application: python -m flowproc"
echo ""
echo "Or use the run script: ./run.sh"