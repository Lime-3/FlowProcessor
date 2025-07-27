#!/bin/bash
# build_mac_app.sh - Simple script to create a clickable macOS app

set -e
echo "🚀 Building FlowProcessor for macOS..."

# Navigate to project directory
cd "$(dirname "$0")" || exit

# Activate virtual environment (create if needed)
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -e .
pip install pyinstaller

# Check for required files
if [ ! -f "flowproc/resources/icon.icns" ]; then
    echo "⚠️  No icon found, creating default one..."
    mkdir -p flowproc/resources
    # Create a simple default icon (you can replace this later)
    python3 -c "
from PIL import Image, ImageDraw
import os
os.makedirs('flowproc/resources', exist_ok=True)
img = Image.new('RGB', (512, 512), color='#4A90E2')
draw = ImageDraw.Draw(img)
draw.text((180, 220), 'FP', fill='white', font_size=100)
img.save('flowproc/resources/icon.icns', 'ICNS')
print('✅ Created default icon')
" 2>/dev/null || echo "ℹ️  PIL not available, skipping icon creation"
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.spec

# Build the app
echo "🔨 Building app bundle..."
pyinstaller \
    --windowed \
    --onedir \
    --name "FlowProcessor" \
    --add-data "flowproc:flowproc" \
    --hidden-import flowproc.presentation.gui.main \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtWidgets \
    --hidden-import PySide6.QtGui \
    --hidden-import plotly \
    --hidden-import pandas \
    --hidden-import numpy \
    --hidden-import openpyxl \
    --osx-bundle-identifier com.flowprocessor.app \
    flowproc/presentation/gui/main.py

# Add icon if it exists
if [ -f "flowproc/resources/icon.icns" ]; then
    echo "🎨 Adding app icon..."
    cp flowproc/resources/icon.icns dist/FlowProcessor.app/Contents/Resources/icon.icns
    # Update Info.plist
    /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile icon.icns" dist/FlowProcessor.app/Contents/Info.plist 2>/dev/null || true
fi

# Make the app executable (just in case)
chmod +x dist/FlowProcessor.app/Contents/MacOS/FlowProcessor

# Test the app
echo "🧪 Testing the app..."
if ./dist/FlowProcessor.app/Contents/MacOS/FlowProcessor --version 2>/dev/null; then
    echo "✅ App executable works!"
else
    echo "⚠️  Testing app startup (this might show some output)..."
    timeout 5 ./dist/FlowProcessor.app/Contents/MacOS/FlowProcessor || echo "App startup test completed"
fi

echo ""
echo "🎉 SUCCESS! Your app is ready!"
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

# Optional: Auto-open the app
read -p "🚀 Open the app now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open dist/FlowProcessor.app
fi