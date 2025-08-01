# flowproc/gui/config_handler.py
import json
from pathlib import Path
from typing import Optional
import logging
import os
import platform

logger = logging.getLogger(__name__)

CONFIG_FILE = Path.home() / ".flowproc" / "config.json"

def get_user_desktop() -> str:
    """
    Get the user's desktop directory path across different operating systems.
    
    Returns:
        str: Path to the user's desktop directory
    """
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        # macOS typically has Desktop in the user's home directory
        desktop_path = Path.home() / "Desktop"
        if desktop_path.exists():
            return str(desktop_path)
        
        # Fallback: check if Desktop is in a different location
        # Some users might have moved it or have a different setup
        possible_paths = [
            Path.home() / "Desktop",
            Path.home() / "デスクトップ",  # Japanese
            Path.home() / "Escritorio",   # Spanish
            Path.home() / "Bureau",       # French
            Path.home() / "Schreibtisch", # German
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # If no desktop found, use home directory
        logger.warning("Desktop directory not found, using home directory")
        return str(Path.home())
        
    elif system == "windows":
        # Windows desktop is typically in the user's profile
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                desktop_path = winreg.QueryValueEx(key, "Desktop")[0]
                return desktop_path
        except (ImportError, OSError, FileNotFoundError):
            # Fallback for Windows
            desktop_path = Path.home() / "Desktop"
            if desktop_path.exists():
                return str(desktop_path)
            else:
                return str(Path.home())
                
    elif system == "linux":
        # Linux desktop locations can vary by distribution
        possible_paths = [
            Path.home() / "Desktop",
            Path.home() / "Рабочий стол",  # Russian
            Path.home() / "Escritorio",   # Spanish
            Path.home() / "Bureau",       # French
            Path.home() / "Schreibtisch", # German
            Path.home() / "桌面",         # Chinese
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # Check XDG user directories
        try:
            xdg_config = Path.home() / ".config" / "user-dirs.dirs"
            if xdg_config.exists():
                with open(xdg_config, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('XDG_DESKTOP_DIR='):
                            desktop_path = line.split('=', 1)[1].strip().strip('"')
                            # Replace $HOME with actual home path
                            desktop_path = desktop_path.replace('$HOME', str(Path.home()))
                            if Path(desktop_path).exists():
                                return desktop_path
        except Exception:
            pass
        
        # Fallback to home directory
        return str(Path.home())
    
    else:
        # Unknown system, use home directory as fallback
        logger.warning(f"Unknown operating system: {system}, using home directory")
        return str(Path.home())

def load_last_output_dir() -> str:
    """
    Load the last used output directory from config.

    Returns:
        str: Path to last output directory or default to Desktop.
    """
    desktop_path = get_user_desktop()
    
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            config = json.load(f)
            saved_dir = config.get("last_output_dir", desktop_path)
            
            # Validate the saved directory
            saved_path = Path(saved_dir)
            if saved_path.exists() and saved_path.is_dir() and os.access(saved_path, os.W_OK):
                return saved_dir
            else:
                logger.warning(f"Saved output directory '{saved_dir}' is invalid or not writable, using Desktop")
                return desktop_path
                
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load config: {str(e)} - Using default directory")
        return desktop_path

def save_last_output_dir(output_dir: str) -> None:
    """
    Save the last used output directory to config.

    Args:
        output_dir: Directory path to save.

    Raises:
        ValueError: If the output directory is not writable.
        IOError: If the config file cannot be written.
    """
    output_path = Path(output_dir)
    if not output_path.is_dir() or not os.access(output_path, os.W_OK):
        logger.error(f"Output directory '{output_dir}' is not writable")
        raise ValueError(f"Output directory '{output_dir}' is not writable")
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        config = {"last_output_dir": output_dir}
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(config, f)
        logger.debug(f"Saved last output directory: {output_dir}")
    except IOError as e:
        logger.error(f"Failed to save config: {str(e)}")
        raise