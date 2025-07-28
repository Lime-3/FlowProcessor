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
    return "A high-performance tool for processing flow cytometry CSV data with async GUI support and vectorized data aggregation"

setup(
    name="flowproc",
    version="2.0.0",
    description="A high-performance tool for processing flow cytometry CSV data with async GUI support and vectorized data aggregation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="FlowProcessor Team",
    author_email="",
    url="https://github.com/yourusername/FlowProcessor",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.13",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    keywords="flow cytometry, data processing, bioinformatics, csv, excel, visualization, async, vectorized",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/FlowProcessor/issues",
        "Source": "https://github.com/yourusername/FlowProcessor",
        "Documentation": "https://github.com/yourusername/FlowProcessor#readme",
    },
) 