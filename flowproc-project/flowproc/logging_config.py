# flowproc/logging_config.py
import logging
import os
import shutil
from pathlib import Path
from datetime import datetime

def setup_logging(filemode='w', max_size_mb=10, keep_backups=3):
    """Setup logging with a logs directory that gets created if it doesn't exist.
    
    Args:
        filemode (str): File mode for logging ('w' for write, 'a' for append)
        max_size_mb (int): Maximum log file size in MB before clearing
        keep_backups (int): Number of backup log files to keep
    """
    # Create logs directory relative to the current working directory
    logs_dir = Path.cwd() / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "processing.log"
    
    # Check if log file exists and is too large
    if log_file.exists():
        file_size_mb = log_file.stat().st_size / (1024 * 1024)  # Convert bytes to MB
        if file_size_mb > max_size_mb:
            # Create backup of current log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = logs_dir / f"processing_{timestamp}.log"
            shutil.copy2(log_file, backup_file)
            
            # Clear the log file by truncating it
            log_file.write_text("")
            
            # Clean up old backup files if we have too many
            backup_files = sorted(logs_dir.glob("processing_*.log"), key=lambda x: x.stat().st_mtime)
            if len(backup_files) > keep_backups:
                for old_backup in backup_files[:-keep_backups]:
                    old_backup.unlink()
            
            print(f"Log file cleared (was {file_size_mb:.1f}MB) - backup saved as {backup_file.name}")
    
    logging.basicConfig(
        level=logging.DEBUG,
        filename=str(log_file),
        filemode=filemode,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured - log file: {log_file} (max size: {max_size_mb}MB, backups: {keep_backups})") 