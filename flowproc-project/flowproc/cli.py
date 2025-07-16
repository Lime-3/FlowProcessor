# flowproc/cli.py
import argparse
from pathlib import Path
from .gui import create_gui
from .writer import process_csv, process_directory
from .logging_config import setup_logging
from .setup import ensure_setup
import logging

def main():
    # Setup logging
    setup_logging(filemode='a', max_size_mb=10, keep_backups=3)
    logging.debug("CLI started")

    # Ensure environment is set up
    ensure_setup()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Process flow cytometry CSV files.")
    parser.add_argument('--input-dir', type=str, help="Input directory containing CSV files")
    parser.add_argument('--output-dir', type=str, help="Output directory for processed Excel files")
    parser.add_argument('--recursive', action='store_true', help="Process subdirectories")
    parser.add_argument('--time-course-mode', action='store_true', help="Enable Time Course output format")

    args = parser.parse_args()

    # If no arguments are provided, launch GUI
    if not any(vars(args).values()):
        logging.info("No CLI arguments provided, launching GUI")
        create_gui()
    else:
        # Validate CLI arguments
        if not args.input_dir or not args.output_dir:
            logging.error("Both --input-dir and --output-dir are required for CLI mode")
            parser.error("Both --input-dir and --output-dir are required")
        process_directory(
            Path(args.input_dir),
            Path(args.output_dir),
            recursive=args.recursive,
            time_course_mode=args.time_course_mode
        )

if __name__ == "__main__":
    main()