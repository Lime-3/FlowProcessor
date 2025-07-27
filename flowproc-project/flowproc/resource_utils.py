# flowproc/resource_utils.py
"""
Enhanced resource utilities for PyInstaller-compatible resource discovery.
Includes fallback mechanisms and comprehensive error handling.
"""
import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Union

logger = logging.getLogger(__name__)


def is_pyinstaller() -> bool:
    """Check if running in PyInstaller bundle."""
    return hasattr(sys, '_MEIPASS')


def is_briefcase() -> bool:
    """Check if running in Briefcase bundle."""
    return hasattr(sys, '_MEIPASS2')


def get_package_root() -> Path:
    """
    Get the package root directory.
    
    Returns:
        Path to the package root directory
    """
    try:
        if is_pyinstaller():
            # PyInstaller bundle
            return Path(sys._MEIPASS)
        elif is_briefcase():
            # Briefcase bundle
            return Path(sys._MEIPASS2)
        else:
            # Development mode
            return Path(__file__).parent.resolve()
    except Exception as e:
        logger.warning(f"Error determining package root: {e}")
        return Path(__file__).parent.resolve()


def get_resource_path(relative_path: str) -> Path:
    """
    Get path to read-only resources with fallback mechanisms.
    
    Args:
        relative_path: Path relative to the package root
        
    Returns:
        Resolved path to the resource
        
    Example:
        >>> path = get_resource_path("resources/icon.icns")
        >>> assert path.exists()
    """
    try:
        # Primary location
        base_path = get_package_root()
        resource_path = base_path / relative_path
        
        # Verify resource exists
        if resource_path.exists():
            return resource_path.resolve()
        
        # Try fallback locations
        fallback_locations = _get_fallback_locations(relative_path)
        
        for location in fallback_locations:
            if location.exists():
                logger.info(f"Found resource at fallback location: {location}")
                return location.resolve()
        
        # Log warning but return the expected path
        logger.warning(f"Resource not found: {relative_path}. Checked {len(fallback_locations) + 1} locations.")
        return resource_path.resolve()
        
    except Exception as e:
        logger.error(f"Error resolving resource path '{relative_path}': {e}")
        # Return a safe fallback
        return Path(relative_path).resolve()


def get_data_path(relative_path: str = "") -> Path:
    """
    Get path for writable data files with automatic directory creation.
    
    Args:
        relative_path: Path relative to the data directory
        
    Returns:
        Resolved path to the data location
        
    Example:
        >>> log_path = get_data_path("logs/processing.log")
        >>> assert log_path.parent.exists()  # Directory created automatically
    """
    try:
        if is_pyinstaller() or is_briefcase():
            # For bundled apps, use directory next to executable
            if sys.platform == "darwin":
                # macOS: Place data outside .app bundle
                executable_path = Path(sys.executable)
                if ".app" in str(executable_path):
                    # Find the .app directory
                    app_path = executable_path
                    while app_path.suffix != '.app' and app_path.parent != app_path:
                        app_path = app_path.parent
                    data_dir = app_path.parent / "data"
                else:
                    data_dir = executable_path.parent / "data"
            else:
                # Windows/Linux: Next to executable
                data_dir = Path(sys.executable).parent / "data"
        else:
            # Development mode: Use package directory
            data_dir = get_package_root() / "data"
        
        # Create full path
        if relative_path:
            full_path = data_dir / relative_path
        else:
            full_path = data_dir
        
        # Ensure parent directories exist
        if relative_path and not str(relative_path).endswith(('.log', '.txt', '.json', '.yaml', '.yml')):
            # It's a directory path
            ensure_writable_dir(full_path)
        else:
            # It's a file path
            ensure_writable_dir(full_path.parent)
        
        return full_path.resolve()
        
    except Exception as e:
        logger.error(f"Error resolving data path '{relative_path}': {e}")
        # Fallback to current directory
        fallback = Path.cwd() / "data" / relative_path if relative_path else Path.cwd() / "data"
        ensure_writable_dir(fallback.parent)
        return fallback.resolve()


def ensure_writable_dir(dir_path: Union[str, Path]) -> bool:
    """
    Ensure a directory exists and is writable.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        True if directory is writable, False otherwise
    """
    try:
        path = Path(dir_path)
        
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        # Test if writable
        test_file = path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            logger.debug(f"Directory is writable: {path}")
            return True
        except (PermissionError, OSError) as e:
            logger.warning(f"Directory is not writable: {path} - {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error ensuring writable directory '{dir_path}': {e}")
        return False


def _get_fallback_locations(relative_path: str) -> List[Path]:
    """Get list of fallback locations to search for resources."""
    fallback_locations = []
    
    try:
        # Current working directory
        fallback_locations.append(Path.cwd() / relative_path)
        
        # Parent of package root
        package_root = get_package_root()
        fallback_locations.append(package_root.parent / relative_path)
        
        # Script directory (for frozen apps)
        if hasattr(sys, 'frozen'):
            script_dir = Path(sys.executable).parent
            fallback_locations.append(script_dir / relative_path)
        
        # Site-packages location (for installed packages)
        try:
            import site
            for site_dir in site.getsitepackages():
                fallback_locations.append(Path(site_dir) / "flowproc" / relative_path)
        except:
            pass
        
        # Environment-specific locations
        if 'FLOWPROC_RESOURCES' in os.environ:
            env_path = Path(os.environ['FLOWPROC_RESOURCES'])
            fallback_locations.append(env_path / relative_path)
            
    except Exception as e:
        logger.warning(f"Error generating fallback locations: {e}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_locations = []
    for location in fallback_locations:
        if location not in seen:
            seen.add(location)
            unique_locations.append(location)
    
    return unique_locations


def get_app_data_dir() -> Path:
    """
    Get platform-appropriate application data directory.
    
    Returns:
        Platform-specific application data directory
    """
    app_name = "FlowProcessor"
    
    if sys.platform == "win32":
        # Windows: %LOCALAPPDATA%\FlowProcessor
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / "AppData" / "Local"))
        return base / app_name
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/FlowProcessor
        return Path.home() / "Library" / "Application Support" / app_name
    else:
        # Linux/Unix: ~/.local/share/FlowProcessor
        xdg_data_home = os.environ.get('XDG_DATA_HOME', Path.home() / ".local" / "share")
        return Path(xdg_data_home) / app_name


def get_config_dir() -> Path:
    """
    Get platform-appropriate configuration directory.
    
    Returns:
        Platform-specific configuration directory
    """
    app_name = "FlowProcessor"
    
    if sys.platform == "win32":
        # Windows: %APPDATA%\FlowProcessor
        base = Path(os.environ.get('APPDATA', Path.home() / "AppData" / "Roaming"))
        return base / app_name
    elif sys.platform == "darwin":
        # macOS: ~/Library/Preferences/FlowProcessor
        return Path.home() / "Library" / "Preferences" / app_name
    else:
        # Linux/Unix: ~/.config/FlowProcessor
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME', Path.home() / ".config")
        return Path(xdg_config_home) / app_name


def get_cache_dir() -> Path:
    """
    Get platform-appropriate cache directory.
    
    Returns:
        Platform-specific cache directory
    """
    app_name = "FlowProcessor"
    
    if sys.platform == "win32":
        # Windows: %LOCALAPPDATA%\FlowProcessor\Cache
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / "AppData" / "Local"))
        return base / app_name / "Cache"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Caches/FlowProcessor
        return Path.home() / "Library" / "Caches" / app_name
    else:
        # Linux/Unix: ~/.cache/FlowProcessor
        xdg_cache_home = os.environ.get('XDG_CACHE_HOME', Path.home() / ".cache")
        return Path(xdg_cache_home) / app_name


# Initialize directories on import
def _initialize_directories():
    """Initialize standard directories on module import."""
    try:
        directories = [get_app_data_dir(), get_config_dir(), get_cache_dir()]
        for directory in directories:
            ensure_writable_dir(directory)
    except Exception as e:
        logger.warning(f"Failed to initialize directories: {e}")


# Initialize on import
_initialize_directories()