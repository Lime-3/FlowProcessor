# flowproc/cli.py
import argparse
from pathlib import Path
from .gui import create_gui
from .writer import process_csv, process_directory
from .logging_config import setup_logging
import logging

def main():
    # Setup logging with logs directory
    setup_logging(filemode='a', max_size_mb=10, keep_backups=3)  # Larger size for CLI, more backups
    logging.debug("CLI started")
    
    parser = argparse.ArgumentParser(description="Process flow cytometry CSV files.")
    parser.add_argument('--input-dir', type=str, help="Input directory containing CSV files")
    parser.add_argument('--output-dir', type=str, help="Output directory for processed Excel files")
    parser.add_argument('--recursive', action='store_true', help="Process subdirectories")
    parser.add_argument('--time-course-mode', action='store_true', help="Enable Time Course output format")

    args = parser.parse_args()

    if args.input_dir and args.output_dir:
        process_directory(Path(args.input_dir), Path(args.output_dir), recursive=args.recursive, time_course_mode=args.time_course_mode)
    else:
        create_gui()

if __name__ == "__main__":
    main()