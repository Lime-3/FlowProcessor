# flowproc/resource_utils.py
"""
Resource path utilities for PyInstaller compatibility.
Handles resource discovery for both development and packaged executable environments.
"""
import sys
from pathlib import Path
from typing import Union


def get_resource_path(relative_path: Union[str, Path]) -> Path:
    """
    Get absolute path to resource, works for dev and PyInstaller.
    
    Args:
        relative_path: Path relative to the package root
        
    Returns:
        Absolute path to the resource
    """
    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        return Path(sys._MEIPASS) / relative_path
    
    # Development mode - use package directory
    package_root = Path(__file__).parent
    return package_root / relative_path


def get_data_path(relative_path: Union[str, Path] = "") -> Path:
    """
    Get path for data files (logs, etc.) with PyInstaller compatibility.
    
    Args:
        relative_path: Path relative to data directory
        
    Returns:
        Absolute path to the data location
    """
    if hasattr(sys, '_MEIPASS'):
        # In PyInstaller bundle, use a writable location
        # Use the directory containing the executable for data
        executable_dir = Path(sys.executable).parent
        if sys.platform == 'darwin' and str(executable_dir).endswith('.app/Contents/MacOS'):
            # On macOS, go up to the .app directory level
            executable_dir = executable_dir.parent.parent.parent
        data_dir = executable_dir / 'data'
    else:
        # Development mode - use package directory
        data_dir = Path(__file__).parent / 'data'
    
    if relative_path:
        return data_dir / relative_path
    return data_dir


def get_package_root() -> Path:
    """
    Get the package root directory with PyInstaller compatibility.
    
    Returns:
        Path to package root
    """
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def ensure_writable_dir(dir_path: Path) -> None:
    """
    Ensure a directory exists and is writable.
    
    Args:
        dir_path: Directory path to create
        
    Raises:
        OSError: If directory cannot be created or is not writable
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(f"Cannot create directory {dir_path}: {e}")
    
    if not dir_path.is_dir():
        raise OSError(f"Path exists but is not a directory: {dir_path}") 