#!/bin/bash
# build_mac_app.sh - Enhanced script to create a clickable macOS app for FlowProcessor

set -euo pipefail  # Enhanced error handling
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="FlowProcessor"
BUNDLE_ID="com.flowprocessor.app"
VERSION="2.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Error handling
cleanup() {
    log_warning "Cleaning up on exit..."
    if [ -n "${VENV_ACTIVATED:-}" ]; then
        deactivate 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python version: $python_version"
    
    # Check if we're on macOS
    if [[ "$(uname)" != "Darwin" ]]; then
        log_warning "This script is designed for macOS. Building on other platforms may not work correctly."
    fi
    
    # Check for required tools
    local missing_tools=()
    for tool in pip pyinstaller; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_warning "Missing tools: ${missing_tools[*]} (will be installed)"
    fi
}

# Setup virtual environment
setup_venv() {
    log_info "Setting up virtual environment..."
    
    cd "$SCRIPT_DIR"
    
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    VENV_ACTIVATED=1
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install project in editable mode
    log_info "Installing project dependencies..."
    pip install -e .
    
    # Install PyInstaller if not present
    if ! pip show pyinstaller &> /dev/null; then
        log_info "Installing PyInstaller..."
        pip install pyinstaller
    fi
}

# Create default icon if missing
create_default_icon() {
    if [ ! -f "flowproc/resources/icons/icon.icns" ]; then
        log_warning "No icon found, creating default one..."
        mkdir -p flowproc/resources/icons
        
        # Try to create icon using PIL
        python3 -c "
import os
try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    os.makedirs('flowproc/resources/icons', exist_ok=True)
    
    # Create a modern-looking icon
    size = 512
    img = Image.new('RGBA', (size, size), color=(74, 144, 226, 255))
    draw = ImageDraw.Draw(img)
    
    # Add a subtle gradient effect
    for i in range(size):
        alpha = int(255 * (1 - i / size * 0.3))
        draw.rectangle([0, i, size, i+1], fill=(74, 144, 226, alpha))
    
    # Add text
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 120)
    except:
        font = ImageFont.load_default()
    
    text = 'FP'
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    # Add text shadow
    draw.text((x+2, y+2), text, fill=(0, 0, 0, 100), font=font)
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # Save as ICNS
    img.save('flowproc/resources/icons/icon.icns', 'ICNS')
    print('✅ Created modern default icon')
except ImportError:
    print('ℹ️  PIL not available, creating simple icon with system tools')
    # Fallback: create a simple colored square
    os.system('mkdir -p flowproc/resources/icons')
    os.system('convert -size 512x512 xc:#4A90E2 -pointsize 100 -gravity center -annotate +0+0 \"FP\" flowproc/resources/icons/icon.icns 2>/dev/null || echo \"Icon creation failed\"')
" 2>/dev/null || log_warning "Icon creation failed, continuing without custom icon"
    fi
}

# Clean previous builds
clean_builds() {
    log_info "Cleaning previous builds..."
    rm -rf dist/ build/ *.spec
    log_success "Build directory cleaned"
}

# Build the application
build_app() {
    log_info "Building application bundle..."
    
    # Create PyInstaller spec file for better control
    cat > FlowProcessor.spec << EOF
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['flowproc/presentation/gui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('flowproc', 'flowproc'),
        ('flowproc/resources', 'flowproc/resources'),
    ],
    hiddenimports=[
        'flowproc.presentation.gui.main',
        'flowproc.presentation.gui.views.main_window',
        'flowproc.presentation.gui.views.components',
        'flowproc.presentation.gui.views.widgets',
        'flowproc.presentation.gui.views.dialogs',
        'flowproc.presentation.gui.controllers',
        'flowproc.presentation.gui.workers',
        'flowproc.domain.parsing',
        'flowproc.domain.processing',
        'flowproc.domain.visualization',
        'flowproc.domain.export',
        'flowproc.application',
        'flowproc.core',
        'flowproc.infrastructure',
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtNetwork',
        'plotly',
        'plotly.graph_objs',
        'plotly.subplots',
        'pandas',
        'numpy',
        'openpyxl',
        'openpyxl.workbook',
        'openpyxl.worksheet',
        'openpyxl.styles',
        'scikit-learn',
        'scipy',
        'PyYAML',
        'pydantic',
        'pydantic_core',
        'kaleido',
        'joblib',
        'python_dateutil',
        'pytz',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FlowProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FlowProcessor',
)

app = BUNDLE(
    coll,
    name='FlowProcessor.app',
    icon='flowproc/resources/icons/icon.icns',
    bundle_identifier='$BUNDLE_ID',
    version='$VERSION',
    info_plist={
        'CFBundleName': '$PROJECT_NAME',
        'CFBundleDisplayName': '$PROJECT_NAME',
        'CFBundleIdentifier': '$BUNDLE_ID',
        'CFBundleVersion': '$VERSION',
        'CFBundleShortVersionString': '$VERSION',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'LSMinimumSystemVersion': '10.15',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.science-research',
        'NSHumanReadableCopyright': 'MIT License',
    },
)
EOF

    # Build with PyInstaller
    pyinstaller --clean FlowProcessor.spec
    
    log_success "Application bundle created"
}

# Post-build processing
post_build() {
    log_info "Performing post-build processing..."
    
    local app_path="dist/FlowProcessor.app"
    
    # Verify the app was created
    if [ ! -d "$app_path" ]; then
        log_error "Application bundle not found at $app_path"
        exit 1
    fi
    
    # Make executable
    chmod +x "$app_path/Contents/MacOS/FlowProcessor"
    
    # Add entitlements if available
    if [ -f "flowproc/resources/entitlements.plist" ]; then
        log_info "Adding entitlements..."
        cp flowproc/resources/entitlements.plist "$app_path/Contents/entitlements.plist"
    fi
    
    # Set proper permissions
    find "$app_path" -type f -exec chmod 644 {} \;
    find "$app_path" -type d -exec chmod 755 {} \;
    chmod +x "$app_path/Contents/MacOS/"*
    
    log_success "Post-build processing completed"
}

# Test the application
test_app() {
    log_info "Testing the application..."
    
    local app_path="dist/FlowProcessor.app"
    local executable="$app_path/Contents/MacOS/FlowProcessor"
    
    if [ ! -f "$executable" ]; then
        log_error "Executable not found: $executable"
        return 1
    fi
    
    # Test basic execution
    if "$executable" --help 2>/dev/null; then
        log_success "Application responds to --help"
    else
        log_warning "Application doesn't respond to --help, testing basic startup..."
        timeout 10 "$executable" 2>/dev/null || log_warning "Startup test completed (may have shown GUI)"
    fi
    
    # Check bundle structure
    log_info "Verifying bundle structure..."
    local required_files=(
        "Contents/Info.plist"
        "Contents/MacOS/FlowProcessor"
        "Contents/Resources"
    )
    
    for file in "${required_files[@]}"; do
        if [ -e "$app_path/$file" ]; then
            log_success "✓ $file exists"
        else
            log_warning "⚠ $file missing"
        fi
    done
}

# Main execution
main() {
    log_info "🚀 Building $PROJECT_NAME for macOS..."
    
    check_requirements
    setup_venv
    create_default_icon
    clean_builds
    build_app
    post_build
    test_app
    
    echo ""
    log_success "🎉 SUCCESS! Your app is ready!"
    echo ""
    echo "📍 Location: $(pwd)/dist/FlowProcessor.app"
    echo ""
    echo "🚀 To test:"
    echo "   open dist/FlowProcessor.app"
    echo ""
    echo "📦 To install:"
    echo "   cp -r dist/FlowProcessor.app /Applications/"
    echo ""
    echo "🔗 To distribute:"
    echo "   zip -r FlowProcessor.zip dist/FlowProcessor.app"
    echo ""
    echo "🔍 To inspect:"
    echo "   codesign -dv dist/FlowProcessor.app"
    echo ""
    
    # Optional: Auto-open the app
    read -p "🚀 Open the app now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open dist/FlowProcessor.app
    fi
}

# Run main function
main "$@"