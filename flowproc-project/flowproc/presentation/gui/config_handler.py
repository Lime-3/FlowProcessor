# flowproc/gui/config_handler.py
import json
from pathlib import Path
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

CONFIG_FILE = Path.home() / ".flowproc" / "config.json"

def load_last_output_dir() -> str:
    """
    Load the last used output directory from config.

    Returns:
        str: Path to last output directory or default to Desktop.
    """
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("last_output_dir", str(Path.home() / "Desktop"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load config: {str(e)} - Using default directory")
        return str(Path.home() / "Desktop")

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