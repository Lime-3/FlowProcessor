#!/usr/bin/env python3
"""
Setup script for FlowProcessor
This provides traditional pip installation support alongside pyproject.toml
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "A tool for processing flow cytometry CSV data"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

setup(
    name="flowproc",
    version="1.0.41",
    description="A tool for processing flow cytometry CSV data",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="FlowProcessor Team",
    author_email="",
    url="https://github.com/yourusername/FlowProcessor",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy>=1.26.4",
        "pandas>=2.3.1",
        "openpyxl>=3.1.5",
        "PySide6>=6.7.0",
        "plotly>=5.18.0",
        "kaleido>=1.0.0",  # For static image export in plotly (PNG, PDF, SVG)
        "scikit-learn>=1.7.0",
        "PyYAML>=6.0.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-qt>=4.3.0",
            "pytest-cov>=6.0.0",
            "pytest-mock>=3.13.0",
        ],
        "test": [
            "pytest>=8.0",
            "pytest-qt>=4.3.0",
            "pytest-cov>=6.0.0",
            "pytest-mock>=3.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flowproc=flowproc.presentation.gui.main:main",
        ],
    },
    python_requires=">=3.13",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    keywords="flow cytometry, data processing, bioinformatics, csv, excel",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/FlowProcessor/issues",
        "Source": "https://github.com/yourusername/FlowProcessor",
    },
) 