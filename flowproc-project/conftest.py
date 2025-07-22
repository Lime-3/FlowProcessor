# flowproc-project/conftest.py
import os
import sys

def pytest_configure():
    """Configure pytest to recognize the flowproc package."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)