# flowproc/logging_config.py
import logging
import os
import shutil
from pathlib import Path
from datetime import datetime
import sys
import atexit
from typing import Literal, Optional
from .resource_utils import get_data_path, ensure_writable_dir

def setup_logging(
    filemode: Literal['a', 'w'] = 'a',
    max_size_mb: int = 10,
    keep_backups: int = 3,
    project_root: Optional[Path] = None,
    simulate_raise: bool = False  # Added for testing: Simulate OSError in mkdir
) -> bool:
    """
    Setup logging with console and file handlers, ensuring logs are written to disk.

    Args:
        filemode (Literal['a', 'w']): File mode for logging ('w' for write, 'a' for append). Defaults to 'a'.
        max_size_mb (int): Maximum log file size in MB before clearing. Defaults to 10.
        keep_backups (int): Number of backup log files to keep. Defaults to 3.
        project_root (Optional[Path]): Optional override for project root (for testing).
        simulate_raise (bool): Simulate OSError in mkdir for testing. Defaults to False.

    Returns:
        bool: True if setup succeeds.

    Raises:
        OSError: If log directory creation or file operations fail (or simulated).
    """
    root = logging.getLogger()
    if any(isinstance(h, logging.FileHandler) for h in root.handlers):
        return True  # Already configured

    # Respect existing level if set; default to INFO, elevate to DEBUG only for development
    if root.level == logging.NOTSET:
        root.setLevel(logging.INFO)
    # Do not blindly clear all handlers; add ours alongside console handler

    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(fmt)
    root.addHandler(console)

    try:
        project_root_str = os.getenv('FLOWPROC_LOG_ROOT')
        if project_root_str:
            log_path = Path(project_root_str).resolve() / 'logs'
        elif project_root is not None:
            log_path = project_root / 'data' / 'logs'
        else:
            # Use PyInstaller-compatible path resolution
            log_path = get_data_path('logs')
        
        if simulate_raise:
            raise OSError("Simulated permission denied for testing")
        ensure_writable_dir(log_path)

        log_file = log_path / 'processing.log'

        root.debug(f"Resolved log directory: {log_path}")
        root.debug(f"Resolved log file path: {log_file}")

        if log_file.exists():
            file_size_mb = log_file.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = log_path / f'processing_{timestamp}.log'
                shutil.copy2(log_file, backup_file)
                with open(log_file, 'w') as f:
                    pass
                root.debug(f"Log file cleared (was {file_size_mb:.1f}MB) - backup saved as {backup_file.name}")

        file_handler = logging.FileHandler(log_file, mode=filemode, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)

        def custom_flush():
            try:
                for handler in root.handlers:
                    if isinstance(handler, logging.FileHandler):
                        try:
                            handler.flush()
                            with open(log_file, 'a') as f:
                                f.flush()
                                os.fsync(f.fileno())
                        except (OSError, ValueError) as e:
                            # File handler might be closed, ignore the error
                            pass
                root.debug("Forced flush of file handler")
                print("Forced flush of file handler", file=sys.stderr)
            except Exception as e:
                # Ignore any errors during flush
                pass

        custom_flush()

        def on_shutdown():
            try:
                custom_flush()
                for handler in root.handlers[:]:
                    if isinstance(handler, logging.FileHandler):
                        try:
                            handler.close()
                            root.removeHandler(handler)
                        except (OSError, ValueError) as e:
                            # Handler might already be closed, ignore the error
                            pass
                root.debug("Shutdown logging handlers closed")
                print("Shutdown logging handlers closed", file=sys.stderr)
            except Exception as e:
                # Ignore any errors during shutdown
                pass

        atexit.register(on_shutdown)

        root.debug("Logging initialized ✅")
        print("Logging initialized ✅", file=sys.stderr)
        return True
    except OSError as e:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        logging.error(f"Failed to set up file logging: {e}", exc_info=True)
        raise