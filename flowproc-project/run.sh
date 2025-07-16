#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")" || exit

# Activate or create virtual environment
source venv/bin/activate || { echo "Creating venv..."; python3 -m venv venv; source venv/bin/activate; }

# Install dependencies
pip install . || { echo "Dependency installation failed"; exit 1; }
brew install qt6 || { echo "Qt6 installation failed (required for PySide6)"; exit 1; }
pip install "PySide6>=6.5.0,<7.0.0" "pandas>=2.0.0,<3.0.0" "numpy>=1.24.0,<2.0.0" "openpyxl>=3.1.0,<4.0.0" "pyinstaller" || { echo "PyInstaller or dependencies failed"; exit 1; }

# Package the application with PyInstaller
echo "Packaging application with PyInstaller..."
pyinstaller --windowed \
            --add-data "$(pwd)/flowproc:flowproc" \
            --add-data "$(pwd)/logs:logs" \
            --hidden-import flowproc.config \
            --hidden-import flowproc.writer \
            --hidden-import flowproc.parsing \
            --hidden-import flowproc.logging_config \
            --hidden-import flowproc.transform \
            --paths "$(pwd)/flowproc" \
            --name "FlowCytometryProcessor" \
            flowproc/gui.py || { echo "PyInstaller packaging failed"; exit 1; }

# No move to Desktop or build, app stays in dist
echo "Packaging complete. The executable is at /Users/franklin.lime/Documents/GitHub/FlowProcessor/flowproc-project/dist/FlowCytometryProcessor.app"