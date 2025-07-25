#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")" || exit

# Activate or create virtual environment
source venv/bin/activate || { echo "Creating venv..."; python3 -m venv venv; source venv/bin/activate; }

# Install dependencies
pip install . || { echo "Dependency installation failed"; exit 1; }
brew install qt6 || { echo "Qt6 installation failed (required for PySide6)"; exit 1; }
pip install "PySide6>=6.5.0,<7.0.0" "pandas>=2.0.0,<3.0.0" "numpy>=1.24.0,<2.0.0" "openpyxl>=3.1.0,<4.0.0" "pyinstaller" "scikit-learn" "pyyaml" "pydantic" || { echo "PyInstaller or dependencies failed"; exit 1; }

# Create logs directory if it doesn't exist
mkdir -p logs

# Package the application with PyInstaller
echo "Packaging application with PyInstaller..."
pyinstaller --windowed \
            --add-data "$(pwd)/flowproc:flowproc" \
            --add-data "$(pwd)/flowproc/resources:flowproc/resources" \
            --add-data "$(pwd)/logs:logs" \
            --hidden-import flowproc.config \
            --hidden-import flowproc.writer \
            --hidden-import flowproc.parsing \
            --hidden-import flowproc.logging_config \
            --hidden-import flowproc.transform \
            --hidden-import flowproc.resource_utils \
            --hidden-import flowproc.domain.visualization.visualize \
            --hidden-import flowproc.domain.processing.vectorized_aggregator \
            --hidden-import flowproc.domain.parsing.parsing_utils \
            --hidden-import flowproc.infrastructure.config.settings \
            --hidden-import flowproc.core.models \
            --hidden-import sklearn.preprocessing \
            --hidden-import yaml \
            --hidden-import pydantic \
            --paths "$(pwd)/flowproc" \
            --name "FlowCytometryProcessor" \
            flowproc/presentation/gui/main.py || { echo "PyInstaller packaging failed"; exit 1; }

# No move to Desktop or build, app stays in dist
echo "Packaging complete. The executable is at /Users/franklin.lime/Documents/GitHub/FlowProcessor/flowproc-project/dist/FlowCytometryProcessor.app"