#!/bin/bash

# FlowProcessor Package Build Script
# Modern packaging and distribution script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    REQUIRED_VERSION="3.11"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python version $PYTHON_VERSION is too old. Required: $REQUIRED_VERSION+"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
    
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    fi
    
    print_success "Project structure verified"
}

# Function to clean previous builds
clean_builds() {
    print_status "Cleaning previous builds..."
    
    if [ -d "dist" ]; then
        rm -rf dist/
        print_success "Removed dist/ directory"
    fi
    
    if [ -d "build" ]; then
        rm -rf build/
        print_success "Removed build/ directory"
    fi
    
    if [ -d "*.egg-info" ]; then
        rm -rf *.egg-info/
        print_success "Removed egg-info directories"
    fi
}

# Function to install build dependencies
install_build_deps() {
    print_status "Installing build dependencies..."
    
    python3 -m pip install --upgrade pip
    python3 -m pip install build twine setuptools-scm[toml]
    
    print_success "Build dependencies installed"
}

# Function to run quality checks
run_quality_checks() {
    print_status "Running quality checks..."
    
    # Check if ruff is available
    if command -v ruff &> /dev/null; then
        print_status "Running ruff checks..."
        ruff check flowproc tests
        print_success "Ruff checks passed"
    else
        print_warning "Ruff not found, skipping ruff checks"
    fi
    
    # Check if mypy is available
    if command -v mypy &> /dev/null; then
        print_status "Running mypy type checks..."
        mypy flowproc
        print_success "Type checks passed"
    else
        print_warning "MyPy not found, skipping type checks"
    fi
    
    # Check if pytest is available
    if command -v pytest &> /dev/null; then
        print_status "Running quick tests..."
        pytest -x --tb=short -q
        print_success "Tests passed"
    else
        print_warning "Pytest not found, skipping tests"
    fi
}

# Function to build the package
build_package() {
    print_status "Building package..."
    
    # Build both wheel and source distribution
    python3 -m build
    
    print_success "Package built successfully"
}

# Function to check the package
check_package() {
    print_status "Checking package..."
    
    # Check the built package
    twine check dist/*
    
    print_success "Package validation passed"
}

# Function to show package info
show_package_info() {
    print_status "Package information:"
    
    echo ""
    echo "Built packages:"
    ls -la dist/
    
    echo ""
    echo "Package contents (wheel):"
    if [ -f "dist/*.whl" ]; then
        python3 -m zipfile -l dist/*.whl | head -20
    fi
    
    echo ""
    echo "Package contents (source):"
    if [ -f "dist/*.tar.gz" ]; then
        tar -tzf dist/*.tar.gz | head -20
    fi
}

# Function to test installation
test_installation() {
    print_status "Testing package installation..."
    
    # Create a temporary virtual environment for testing
    TEMP_VENV="temp_test_venv"
    
    python3 -m venv "$TEMP_VENV"
    source "$TEMP_VENV/bin/activate"
    
    # Install the package
    pip install dist/*.whl
    
    # Test import
    python3 -c "import flowproc; print('✅ Package imports successfully')"
    
    # Clean up
    deactivate
    rm -rf "$TEMP_VENV"
    
    print_success "Installation test passed"
}

# Function to show next steps
show_next_steps() {
    print_success "Build completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review the built packages in dist/"
    echo "2. Test the package: make test-install"
    echo "3. Upload to PyPI test: make publish"
    echo "4. Upload to PyPI: make publish-prod"
    echo ""
    echo "Commands:"
    echo "  make publish      # Upload to PyPI test"
    echo "  make publish-prod # Upload to PyPI"
    echo "  make dist-clean  # Clean build artifacts"
}

# Main execution
main() {
    echo "🚀 FlowProcessor Package Builder"
    echo "================================"
    echo ""
    
    check_prerequisites
    clean_builds
    install_build_deps
    
    # Ask user if they want to run quality checks
    read -p "Run quality checks before building? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_quality_checks
    fi
    
    build_package
    check_package
    show_package_info
    
    # Ask user if they want to test installation
    read -p "Test package installation? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_installation
    fi
    
    show_next_steps
}

# Run main function
main "$@"
