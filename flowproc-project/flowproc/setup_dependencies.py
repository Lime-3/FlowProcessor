# flowproc/setup_dependencies.py
import os
import subprocess
import sys
import importlib.util
from typing import List
from pathlib import Path

def install_flowproc_dependencies(dependencies: List[str] = None, upgrade: bool = False) -> bool:
    """
    Install or upgrade required dependencies for the flowproc project in the active virtual environment.

    This function checks if a virtual environment is active, installs the specified dependencies (e.g., numpy, pandas,
    openpyxl, PySide6 for the GUI), verifies their availability. It provides detailed feedback for debugging and ensures
    the flowproc project runs correctly with PySide6.

    Args:
        dependencies (List[str], optional): List of package names to install. Defaults to flowproc requirements including PySide6.
        upgrade (bool, optional): If True, upgrades existing packages. Defaults to False.

    Returns:
        bool: True if installation and verification succeed, False otherwise.

    Raises:
        RuntimeError: If no virtual environment is active or if pip is not found.

    Example:
        >>> install_flowproc_dependencies()
        True
    """
    # Default dependencies for flowproc with PySide6 (removed Toga for compatibility)
    if dependencies is None:
        dependencies = [
            'numpy>=1.26.4',      # For numerical operations
            'pandas>=2.3.1',      # For DataFrame handling
            'openpyxl>=3.1.5',    # For Excel output
            'PySide6>=6.7.2',     # For PySide6-based GUI (latest stable as of July 2025)
            'plotly>=5.23.0',     # For visualization (added for visualize.py compatibility)
            'kaleido>=0.2.1',     # For static image export in plotly if needed
            'pytest>=8.3.4',      # For testing (added for test_logging.py compatibility) 
            
        ]

    # Check if running in a virtual environment
    venv_path = os.environ.get('VIRTUAL_ENV')
    if not venv_path:
        print("Error: No virtual environment detected. Run 'source venv/bin/activate' first.", file=sys.stderr)
        raise RuntimeError("No active virtual environment. Activate your venv with 'source venv/bin/activate'.")

    print(f"Virtual environment active: {venv_path}")

    # Build pip install command
    pip_cmd = [sys.executable, '-m', 'pip', 'install']
    if upgrade:
        pip_cmd.append('--upgrade')
    pip_cmd.extend(dependencies)

    try:
        # Install dependencies
        print(f"Installing dependencies: {', '.join(dependencies)}")
        result = subprocess.run(pip_cmd, check=True, capture_output=True, text=True)
        print(f"Installation output:\n{result.stdout}")

        # Verify installations
        for package in [dep.split('>=')[0] for dep in dependencies]:  # Strip version specifiers
            if importlib.util.find_spec(package) is None:
                print(f"Error: Package '{package}' not found after installation.", file=sys.stderr)
                return False
            print(f"Verified: '{package}' is installed.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies. Error: {e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: pip not found. Ensure Python and pip are correctly installed.", file=sys.stderr)
        raise RuntimeError("pip not found. Ensure Python is installed correctly.")

def main():
    """Run the dependency installation and verify setup."""
    try:
        if install_flowproc_dependencies():
            print("All dependencies installed successfully. Try running 'python -m flowproc' again.")
        else:
            print("Installation failed. Check error messages above.", file=sys.stderr)
            sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()