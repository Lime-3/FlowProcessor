#!/bin/bash

# FlowProcessor PyInstaller Build Script
# Creates standalone executable with PyInstaller - Production Build (No Tests)

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
    
    # Check if PyInstaller is installed
    if ! python3 -c "import PyInstaller" &> /dev/null; then
        print_error "PyInstaller is not installed. Please install it first: pip install pyinstaller"
        exit 1
    fi
    
    print_success "PyInstaller is available"
    print_success "Project structure verified"
}

# Function to clean previous PyInstaller builds
clean_pyinstaller_builds() {
    print_status "Cleaning previous PyInstaller builds..."
    
    if [ -d "build/pyinstaller" ]; then
        rm -rf build/pyinstaller/
        print_success "Removed build/pyinstaller/ directory"
    fi
    
    if [ -d "dist/pyinstaller" ]; then
        rm -rf dist/pyinstaller/
        print_success "Removed dist/pyinstaller/ directory"
    fi
    
    # Clean PyInstaller cache
    if [ -d "__pycache__" ]; then
        rm -rf __pycache__/
        print_success "Removed __pycache__ directory"
    fi
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Function to run basic quality checks (no tests)
run_basic_checks() {
    print_status "Running basic quality checks..."
    
    # Check if ruff is available
    if command -v ruff &> /dev/null; then
        print_status "Running ruff checks..."
        ruff check flowproc
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
}

# Function to build with PyInstaller
build_pyinstaller() {
    print_status "Building with PyInstaller..."
    
    # Create build directories
    mkdir -p build/pyinstaller
    mkdir -p dist/pyinstaller
    
    # Generate spec file if it doesn't exist or is outdated
    if [ ! -f "FlowProcessor.spec" ] || [ "flowproc.spec" -nt "FlowProcessor.spec" ]; then
        print_status "Generating PyInstaller spec file..."
        python3 -m PyInstaller --name FlowProcessor --onedir --windowed --icon=flowproc/resources/icons/icon.icns --specpath . flowproc/__main__.py
        print_success "Spec file generated"
    fi
    
    # Run PyInstaller with the generated spec
    python3 -m PyInstaller FlowProcessor.spec \
        --workpath=build/pyinstaller \
        --distpath=dist/pyinstaller \
        --clean \
        --noconfirm
    
    print_success "PyInstaller build completed"
}

# Function to verify the build
verify_build() {
    print_status "Verifying the build..."
    
    # Check if executable was created
    if [ -f "dist/pyinstaller/FlowProcessor/FlowProcessor" ]; then
        print_success "Executable created: dist/pyinstaller/FlowProcessor/FlowProcessor"
    elif [ -f "dist/pyinstaller/FlowProcessor/FlowProcessor.exe" ]; then
        print_success "Executable created: dist/pyinstaller/FlowProcessor/FlowProcessor.exe"
    elif [ -f "dist/FlowProcessor" ]; then
        print_success "Executable created: dist/FlowProcessor"
    else
        print_error "Executable not found in expected location"
        exit 1
    fi
    
    # Check if .app bundle was created (macOS)
    if [ -d "dist/pyinstaller/FlowProcessor.app" ]; then
        print_success "macOS app bundle created: dist/pyinstaller/FlowProcessor.app"
    elif [ -d "dist/FlowProcessor.app" ]; then
        print_success "macOS app bundle created: dist/FlowProcessor.app"
    fi
    
    # Show file sizes
    print_status "Build artifacts:"
    ls -lh dist/
    if [ -d "dist/pyinstaller" ]; then
        ls -lh dist/pyinstaller/
    fi
}

# Function to test the executable
test_executable() {
    print_status "Testing the executable..."
    
    # Test if executable runs without crashing
    if [ -f "dist/pyinstaller/FlowProcessor/FlowProcessor" ]; then
        print_status "Testing executable (will start GUI - close it to continue)..."
        timeout 10s dist/pyinstaller/FlowProcessor/FlowProcessor || true
        print_success "Executable test completed"
    elif [ -f "dist/pyinstaller/FlowProcessor/FlowProcessor.exe" ]; then
        print_status "Testing Windows executable (will start GUI - close it to continue)..."
        timeout 10s dist/pyinstaller/FlowProcessor/FlowProcessor.exe || true
        print_success "Executable test completed"
    fi
}

# Function to show build information
show_build_info() {
    print_success "PyInstaller build completed successfully!"
    echo ""
    echo "Build artifacts:"
    echo "  - Executable: dist/pyinstaller/FlowProcessor/"
    if [ -d "dist/pyinstaller/FlowProcessor.app" ]; then
        echo "  - macOS App: dist/pyinstaller/FlowProcessor.app"
    fi
    echo ""
    echo "To run the application:"
    if [ -f "dist/pyinstaller/FlowProcessor/FlowProcessor" ]; then
        echo "  ./dist/pyinstaller/FlowProcessor/FlowProcessor"
    elif [ -f "dist/pyinstaller/FlowProcessor/FlowProcessor.exe" ]; then
        echo "  dist\\pyinstaller\\FlowProcessor\\FlowProcessor.exe"
    fi
    echo ""
    echo "To distribute:"
    echo "  - Copy the entire FlowProcessor directory"
    echo "  - Or distribute the .app bundle (macOS)"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --clean-only     Only clean previous builds"
    echo "  --no-checks      Skip running quality checks before building"
    echo "  --no-test-exe    Skip testing the executable after building"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0               # Full build with quality checks"
    echo "  $0 --no-checks    # Build without quality checks"
    echo "  $0 --clean-only   # Only clean previous builds"
}

# Parse command line arguments
CLEAN_ONLY=false
RUN_CHECKS=true
TEST_EXECUTABLE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean-only)
            CLEAN_ONLY=true
            shift
            ;;
        --no-checks)
            RUN_CHECKS=false
            shift
            ;;
        --no-test-exe)
            TEST_EXECUTABLE=false
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "🚀 FlowProcessor PyInstaller Builder (Production)"
    echo "================================================="
    echo ""
    
    check_prerequisites
    clean_pyinstaller_builds
    
    if [ "$CLEAN_ONLY" = true ]; then
        print_success "Clean completed"
        exit 0
    fi
    
    install_dependencies
    
    if [ "$RUN_CHECKS" = true ]; then
        run_basic_checks
    fi
    
    build_pyinstaller
    verify_build
    
    if [ "$TEST_EXECUTABLE" = true ]; then
        test_executable
    fi
    
    show_build_info
}

# Run main function
main "$@"
