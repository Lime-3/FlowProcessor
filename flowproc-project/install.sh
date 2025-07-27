#!/bin/bash

# FlowProcessor Installation Script
# Provides multiple installation options for pip

set -e  # Exit on any error

echo "🚀 FlowProcessor Installation Options"
echo "====================================="
echo ""

# Function to check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed. Please install Python 3.13 or later."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.13"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        echo "❌ Python version $PYTHON_VERSION is too old. Please install Python $REQUIRED_VERSION or later."
        exit 1
    fi
    
    echo "✅ Python $PYTHON_VERSION detected"
}

# Function to create and activate virtual environment
setup_venv() {
    local venv_dir="$1"
    
    if [ ! -d "$venv_dir" ]; then
        echo "🔧 Creating virtual environment at $venv_dir..."
        python3 -m venv "$venv_dir"
    else
        echo "✅ Virtual environment already exists at $venv_dir"
    fi
    
    echo "🔧 Activating virtual environment..."
    source "$venv_dir/bin/activate"
    
    echo "⬆️  Upgrading pip..."
    python -m pip install --upgrade pip
}

# Function to install from requirements.txt
install_from_requirements() {
    echo "📦 Installing from requirements.txt..."
    pip install -r requirements.txt
}

# Function to install in development mode
install_dev_mode() {
    echo "📦 Installing in development mode..."
    pip install -e .
}

# Function to install from pyproject.toml
install_from_pyproject() {
    echo "📦 Installing from pyproject.toml..."
    pip install .
}

# Function to install with setup.py
install_with_setup() {
    echo "📦 Installing with setup.py..."
    pip install .
}

# Function to install with extra dependencies
install_with_extras() {
    local extras="$1"
    echo "📦 Installing with extras: $extras..."
    pip install -e ".[$extras]"
}

# Function to verify installation
verify_installation() {
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
}

# Main installation menu
show_menu() {
    echo "Choose an installation method:"
    echo "1) Quick install (from requirements.txt)"
    echo "2) Development install (editable mode)"
    echo "3) Install from pyproject.toml"
    echo "4) Install with setup.py"
    echo "5) Install with development extras"
    echo "6) Install with test extras"
    echo "7) Full setup (virtual environment + development install)"
    echo "8) Exit"
    echo ""
    read -p "Enter your choice (1-8): " choice
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Check Python
check_python
echo ""

# Show menu and handle choice
while true; do
    show_menu
    
    case $choice in
        1)
            echo ""
            echo "🚀 Quick install from requirements.txt"
            install_from_requirements
            verify_installation
            break
            ;;
        2)
            echo ""
            echo "🚀 Development install (editable mode)"
            install_dev_mode
            verify_installation
            break
            ;;
        3)
            echo ""
            echo "🚀 Install from pyproject.toml"
            install_from_pyproject
            verify_installation
            break
            ;;
        4)
            echo ""
            echo "🚀 Install with setup.py"
            install_with_setup
            verify_installation
            break
            ;;
        5)
            echo ""
            echo "🚀 Install with development extras"
            install_with_extras "dev"
            verify_installation
            break
            ;;
        6)
            echo ""
            echo "🚀 Install with test extras"
            install_with_extras "test"
            verify_installation
            break
            ;;
        7)
            echo ""
            echo "🚀 Full setup with virtual environment"
            VENV_DIR="$PROJECT_DIR/venv"
            setup_venv "$VENV_DIR"
            install_dev_mode
            verify_installation
            break
            ;;
        8)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please enter a number between 1 and 8."
            echo ""
            ;;
    esac
done

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To run FlowProcessor:"
echo "  python -m flowproc"
echo ""
echo "Or if you used option 7 (full setup):"
echo "  source venv/bin/activate"
echo "  python -m flowproc" 