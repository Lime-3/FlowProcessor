# flowproc/gui.py
import os
import sys
import logging
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Tuple, Optional

# Handle standalone execution
if __name__ == "__main__" and __package__ is None:
    # Use PyInstaller-compatible path resolution
    if not hasattr(sys, '_MEIPASS'):
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
    __package__ = "flowproc"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QCheckBox, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QGroupBox,
    QFormLayout, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QFont, QDragEnterEvent, QDropEvent, QScreen
from .config import USER_GROUPS, USER_REPLICATES, AUTO_PARSE_GROUPS, USER_GROUP_LABELS, parse_range_or_list
from .writer import process_csv, process_directory
from .parsing import load_and_parse_df
from .logging_config import setup_logging

# Global variable to store preview paths
preview_paths = []

def update_preview_paths(file_paths: list[str]) -> None:
    """Update the list of previewable paths with global scope."""
    global preview_paths
    logging.debug(f"Attempting to update preview paths with: {file_paths}")
    preview_paths = [p for p in file_paths if Path(p).is_file() and Path(p).suffix.lower() == '.csv']
    logging.debug(f"Updated preview paths: {preview_paths}")
    if not preview_paths:
        logging.warning("No valid CSV files found in provided paths")

class DropLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        logging.debug("DropLineEdit initialized")

    def dragEnterEvent(self, event: QDragEnterEvent):
        logging.debug("Drag enter event on input field received")
        if event.mimeData().hasUrls():
            logging.debug(f"Mime data URLs: {event.mimeData().urls()}")
            event.acceptProposedAction()
        else:
            logging.debug("No URLs in mime data")
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        logging.debug("Drop event on input field received")
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            file_paths = [url.toLocalFile() for url in mime_data.urls()]
            logging.debug(f"Raw dropped paths: {file_paths}")
            valid_paths = []
            for path in file_paths:
                p = Path(path)
                if p.is_dir() or p.suffix.lower() == '.csv':
                    valid_paths.append(path)
            if valid_paths:
                existing_paths = self.text().split("; ") if self.text() else []
                all_paths = existing_paths + valid_paths
                all_paths = list(dict.fromkeys(all_paths))  # Remove duplicates
                self.setText("; ".join(all_paths))
                logging.debug(f"Accepted paths: {valid_paths}")
                update_preview_paths(all_paths)  # Update preview paths on drop
                event.acceptProposedAction()
            else:
                logging.debug("No valid paths dropped")
                QMessageBox.warning(self.parent(), "Invalid Drop", "Please drop only CSV files or folders.")
                event.ignore()
        else:
            logging.debug("No mime data with URLs")
            event.ignore()

def create_gui():
    """Create the main GUI window with resizable layout and table-based summary preview for multiple files."""
    setup_logging(filemode='w', max_size_mb=5, keep_backups=2)
    logging.debug("GUI creation started - logging configured")

    app = QApplication([])
    app.setStyle('Fusion')

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(15, 15, 15))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.Text, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Button, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Highlight, QColor(0, 100, 255))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(dark_palette)

    app.setStyleSheet("""
        QMainWindow, QWidget { 
            background-color: #0F0F0F; 
            border-radius: 8px;
        }
        QLabel { 
            color: #F0F0F0; 
            font-size: 14px; 
            font-family: 'Arial', sans-serif;
        }
        QLineEdit { 
            background-color: #191919; 
            color: #F0F0F0; 
            border: 1px solid #303030; 
            padding: 4px;  /* Reduced padding to prevent cutoff */
            border-radius: 4px;
            min-height: 40px;  /* Increased to prevent cutoff */
            max-width: 480px;
        }
        QLineEdit#groupEntry {
            min-height: 40px;  /* Ensure consistency with other QLineEdits */
        }
        QPushButton { 
            border: none; 
            background-color: #007BFF; 
            color: white; 
            padding: 8px 16px; 
            border-radius: 4px; 
            font-size: 12px; 
            min-height: 30px;  /* Match QLineEdit height */
            font-weight: 600;
        }
        QPushButton:hover { 
            background-color: #0056b3; 
        }
        QCheckBox { 
            color: #FFFFFF; 
            font-size: 12px; 
            spacing: 8px; 
            padding: 4px; 
            background-color: transparent; 
            border-radius: 3px;
        }
        QCheckBox::indicator { 
            width: 16px; 
            height: 16px; 
            border: 2px solid #0064FF; 
            background-color: #1A1A1A; 
            border-radius: 3px;
        }
        QCheckBox::indicator:checked { 
            background-color: #0064FF; 
            border: 2px solid #0064FF;
            image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAdUlEQVQYV2NkYGBg+P//PwO2gYGBISHBgP8/A4j3798Z4D9//gT+//8fQ2kQJycnGfD///8M6O7uZqCvr28Gtm/fZqC3t7cZ6OvrZwC4uLiA4eHhAobRaCQAe/fuZqCnpycD9+7dA4hGo2kA7O3tZqC7u/sMABkKeg1K9n2GAAAAAElFTkSuQmCC);
        }
        QCheckBox::indicator:hover { 
            background-color: #252525;
        }
        QCheckBox::indicator:checked:hover { 
            background-color: #004CCC;
        }
        QGroupBox { 
            border: 1px solid #303030; 
            margin-top: 0px;  /* Removed margin to align with labels */
            color: #F0F0F0; 
            padding: 10px;
            /* Removed background-color: #181818 for Input / Output to keep clean */
            border-radius: 6px;
        }
        QGroupBox::title { 
            subcontrol-origin: margin; 
            padding: 0 8px; 
            font-size: 16px; 
            font-weight: 600;
            color: #0064FF;
        }
        QProgressBar {
            background-color: #222222;
            color: #F0F0F0;
            border-radius: 4px;
            text-align: center;
            min-height: 30px;
        }
        QTableWidget {
            background-color: #191919;
            color: #F0F0F0;
            border: 1px solid #303030;
            gridline-color: #303030;
            selection-background-color: #0064FF;
            selection-color: #FFFFFF;
        }
        QTableWidget::item {
            padding: 4px;
        }
    """)

    window = QMainWindow()
    window.setWindowTitle("Flow Cytometry Processor")
    # Removed fixed size to allow resizing
    # window.setMinimumSize(600, 800)
    # window.resize(600, 800)

    screen = app.primaryScreen()
    screen_size = screen.size()
    window.move((screen_size.width() - window.width()) // 2, (screen_size.height() - window.height()) // 2)

    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(20, 20, 20, 20)  # Consistent margins
    main_layout.setSpacing(16)  # Consistent spacing
    main_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)  # Allow resizing

    # Options label above the group box
    options_label = QLabel("Options")
    options_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #0064FF;")
    main_layout.addWidget(options_label)
    options_group = QGroupBox()
    options_layout = QVBoxLayout(options_group)
    options_layout.setSpacing(10)
    time_course_checkbox = QCheckBox("Time Course Output Format")
    time_course_checkbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    manual_groups_checkbox = QCheckBox("Manually Define Groups and Replicates")
    manual_groups_checkbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # Horizontally align checkboxes
    checkbox_layout = QHBoxLayout()
    checkbox_layout.addWidget(manual_groups_checkbox)
    checkbox_layout.addStretch()  # Spacer to push Time Course to the right
    checkbox_layout.addWidget(time_course_checkbox)
    options_layout.addLayout(checkbox_layout)

    manual_widget = QWidget()
    manual_layout = QVBoxLayout(manual_widget)
    manual_layout.setContentsMargins(0, 0, 0, 0)
    manual_layout.setSpacing(10)

    # Horizontal layout for Group Numbers
    group_row = QWidget()
    group_layout = QHBoxLayout(group_row)
    group_layout.setContentsMargins(0, 0, 0, 0)
    group_label = QLabel("Group Numbers:")
    group_label.setAlignment(Qt.AlignRight)  # Right-align label text
    groups_entry = QLineEdit("1-10")
    groups_entry.setEnabled(False)
    groups_entry.setObjectName("groupEntry")  # For specific styling
    groups_entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    groups_entry.setFixedHeight(40)  # Increased to prevent cutoff
    groups_entry.setFixedWidth(400)  # Match other inputs
    group_layout.addWidget(group_label)
    group_layout.addSpacing(10)  # Space between label and entry
    group_layout.addWidget(groups_entry)

    # Horizontal layout for Replicate Numbers
    replicate_row = QWidget()
    replicate_layout = QHBoxLayout(replicate_row)
    replicate_layout.setContentsMargins(0, 0, 0, 0)
    replicate_label = QLabel("Replicate Numbers:")
    replicate_label.setAlignment(Qt.AlignRight)  # Right-align label text
    replicates_entry = QLineEdit("1-3")
    replicates_entry.setEnabled(False)
    replicates_entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    replicates_entry.setFixedHeight(40)  # Increased to prevent cutoff
    replicates_entry.setFixedWidth(400)  # Match Group width and other inputs
    replicate_layout.addWidget(replicate_label)
    replicate_layout.addSpacing(10)  # Space between label and entry
    replicate_layout.addWidget(replicates_entry)

    save_button = QPushButton("Save")
    save_button.setEnabled(False)
    save_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    save_button.setFixedHeight(30)  # Match QLineEdit height

    # Vertical stack with Save button on the right
    manual_row_layout = QHBoxLayout()
    left_layout = QVBoxLayout()
    left_layout.addWidget(group_row)
    left_layout.addWidget(replicate_row)
    right_layout = QVBoxLayout()
    right_layout.addStretch()  # Top spacer
    right_layout.addWidget(save_button)  # Centered vertically
    right_layout.addStretch()  # Bottom spacer
    manual_row_layout.addLayout(left_layout, stretch=1)
    manual_row_layout.addLayout(right_layout, stretch=0)
    manual_layout.addLayout(manual_row_layout)
    options_layout.addWidget(manual_widget)

    main_layout.addWidget(options_group)

    # Input / Output label above the group box
    io_label = QLabel("Input / Output")
    io_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #0064FF;")
    main_layout.addWidget(io_label)
    io_group = QGroupBox()
    io_layout = QFormLayout(io_group)
    io_layout.setSpacing(10)
    io_layout.setVerticalSpacing(10)  # Equal vertical distribution
    io_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)  # Align labels and boxes inline
    io_layout.setAlignment(Qt.AlignLeft)  # Ensure left alignment

    # Horizontal layout for Output Directory
    out_dir_widget = QWidget()
    out_dir_layout = QHBoxLayout(out_dir_widget)
    out_dir_layout.setContentsMargins(0, 0, 0, 0)
    out_dir_label = QLabel("Output Directory:")
    # Removed setAlignment(Qt.AlignRight) for natural centering
    out_dir_entry = QLineEdit(load_last_output_dir())  # Define here
    out_dir_entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    out_dir_entry.setFixedWidth(400)  # Same width as others
    def browse_output():
        folder = QFileDialog.getExistingDirectory(window, "Select Output Directory")
        if folder:
            out_dir_entry.setText(folder)
    out_dir_button = QPushButton("Browse")
    out_dir_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    # Add spacing to center the label over the 400px text box
    out_dir_layout.addSpacing(140)  # Approximate half the difference (400px - label width ~120px) / 2
    out_dir_layout.addWidget(out_dir_label)
    out_dir_layout.addSpacing(10)  # Space between label and entry
    out_dir_layout.addWidget(out_dir_entry)
    out_dir_layout.addStretch()  # Push button to the right
    out_dir_layout.addWidget(out_dir_button, alignment=Qt.AlignRight)
    io_layout.addRow(out_dir_widget)
    out_dir_button.clicked.connect(browse_output)
      
    # Horizontal layout for Group Labels
    group_labels_widget = QWidget()
    group_labels_layout = QHBoxLayout(group_labels_widget)
    group_labels_layout.setContentsMargins(0, 0, 0, 0)
    group_labels_layout.addWidget(QLabel("Group Labels (optional):"))
    group_labels_entry = QLineEdit()  # Define here
    group_labels_entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    group_labels_entry.setFixedWidth(400)  # Same width as others
    group_labels_entry.setPlaceholderText("Comma-separated group names")
    group_labels_layout.addStretch()  # Spacer to push entry box to the right
    group_labels_layout.addWidget(group_labels_entry)
    io_layout.addRow(group_labels_widget)

    # Horizontal layout for Input File/Folder
    input_widget = QWidget()
    input_layout = QHBoxLayout(input_widget)
    input_layout.setContentsMargins(0, 0, 0, 0)
    input_label = QLabel("Input File/Folder:")
    input_label.setAlignment(Qt.AlignRight)  # Right-align label text
    path_entry = DropLineEdit(window)  # Define here
    path_entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    path_entry.setFixedWidth(400)  # Same width as others
    def browse_input():
        files, _ = QFileDialog.getOpenFileNames(window, "Select CSV Files", "", "CSV files (*.csv)")
        if files:
            path_entry.setText("; ".join(files))
            update_preview_paths(files)
    browse_input_button = QPushButton("Browse")
    browse_input_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    preview_button = QPushButton("Preview CSV")
    preview_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    clear_button = QPushButton("Clear")
    clear_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    clear_button.clicked.connect(lambda: clear_input(path_entry))
    input_layout.addWidget(input_label)
    input_layout.addSpacing(10)  # Space between label and entry
    input_layout.addWidget(path_entry)
    input_layout.addStretch()  # Push buttons to the right
    input_layout.addWidget(browse_input_button)
    input_layout.addWidget(preview_button)
    input_layout.addWidget(clear_button)
    io_layout.addRow(input_widget)

    main_layout.addWidget(io_group)

    process_button = QPushButton("Process")
    process_button.setFixedWidth(160)
    process_button.setFixedHeight(48)
    process_button.setStyleSheet("border-radius: 10px; background-color: #007BFF; color: white;")
    process_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    process_layout = QHBoxLayout()
    process_layout.addStretch()
    process_layout.addWidget(process_button)
    process_layout.addStretch()
    main_layout.addLayout(process_layout)

    progress_bar = QProgressBar()
    progress_bar.setAlignment(Qt.AlignCenter)
    progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    progress_bar.setStyleSheet("QProgressBar { background-color: #222222; color: #F0F0F0; border-radius: 4px; text-align: center; }")
    main_layout.addWidget(progress_bar)

    status_label = QLabel("Ready")
    status_label.setAlignment(Qt.AlignCenter)
    status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    status_label.setStyleSheet("background-color: #222222; padding: 8px; border-radius: 4px; font-size: 14px; color: #A0A0A0;")
    main_layout.addWidget(status_label)
    main_layout.addStretch()

    def toggle_manual(state):
        global AUTO_PARSE_GROUPS, USER_GROUPS, USER_REPLICATES
        AUTO_PARSE_GROUPS = not bool(state)
        enabled = bool(state)
        groups_entry.setEnabled(enabled)
        replicates_entry.setEnabled(enabled)
        save_button.setEnabled(enabled)
        if not enabled:
            USER_GROUPS.clear()
            USER_REPLICATES.clear()
        status_label.setText("Manual group/replicate mode enabled." if enabled else "Automatic parsing enabled.")

    manual_groups_checkbox.stateChanged.connect(toggle_manual)

    def save_definitions():
        global USER_GROUPS, USER_REPLICATES
        try:
            USER_GROUPS = parse_range_or_list(groups_entry.text().strip())
            USER_REPLICATES = parse_range_or_list(replicates_entry.text().strip())
            if not USER_GROUPS or not USER_REPLICATES:
                raise ValueError("Groups and replicates cannot be empty.")
            status_label.setText("Groups and replicates saved.")
        except ValueError as e:
            QMessageBox.critical(window, "Input Error", str(e))

    save_button.clicked.connect(save_definitions)

    def update_preview_paths(file_paths: list[str]) -> None:
        """Update the list of previewable paths with global scope."""
        global preview_paths
        logging.debug(f"Attempting to update preview paths with: {file_paths}")
        preview_paths = [p for p in file_paths if Path(p).is_file() and Path(p).suffix.lower() == '.csv']
        logging.debug(f"Updated preview paths: {preview_paths}")
        if not preview_paths:
            logging.warning("No valid CSV files found in provided paths")

    preview_paths = []  # Global to store valid preview paths
    path_entry.textChanged.connect(lambda: update_preview_paths(path_entry.text().split("; ")))

    def setup_gui_preview(preview_button: QPushButton, window: QMainWindow, load_and_parse_df: Callable[[Path], Tuple[pd.DataFrame, str]]) -> None:
        """
        Set up the GUI preview functionality with detailed logging for table-based summary preview of multiple files.

        This function defines the preview_csv function to show a combined summary in a table for all valid CSV files,
        with unique values for Groups, Animal Range, Timepoint, and Tissue summarized by commas.

        Args:
            preview_button (QPushButton): The button that triggers the preview.
            window (QMainWindow): The main GUI window for parenting the preview window.
            load_and_parse_df (Callable[[Path], Tuple[pd.DataFrame, str]]): The function to load and parse the CSV file.

        Returns:
            None
        """
        def preview_csv():
            """Open a new window with a table-based combined summary preview of all valid CSV files."""
            global preview_paths
            logging.debug(f"Current preview paths before preview: {preview_paths}")
            if not preview_paths:
                logging.warning("No valid preview paths available.")
                QMessageBox.warning(window, "Invalid Input", "No valid CSV files available for preview.")
                return
            table = QTableWidget(len(preview_paths), 6)  # 6 columns: File, Samples, Groups, Animal Range, Timepoint, Tissue
            table.setHorizontalHeaderLabels(["File", "Samples", "Groups", "Animal Range", "Timepoint", "Tissue"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow resizing
            row = 0
            for selected_path in preview_paths:
                path_obj = Path(selected_path)
                logging.debug(f"Checking file: {path_obj}, exists: {path_obj.exists()}, is_file: {path_obj.is_file()}, suffix: {path_obj.suffix.lower()}")
                if not path_obj.exists() or not path_obj.is_file() or path_obj.suffix.lower() != '.csv':
                    logging.error(f"Invalid CSV file skipped: {selected_path}")
                    table.setItem(row, 0, QTableWidgetItem(f"{path_obj.name} - Error: Invalid file"))
                    row += 1
                    continue
                try:
                    logging.debug(f"Attempting to parse {selected_path}")
                    df, _ = load_and_parse_df(path_obj)
                    logging.debug(f"Parsed DataFrame shape: {df.shape}")
                    # Calculate summary for this file with unique values
                    num_samples = len(df)
                    unique_groups = ", ".join(map(str, sorted(df["Group"].dropna().unique()))) if "Group" in df.columns and not df["Group"].isna().all() else "N/A"
                    unique_animals = ", ".join(map(str, sorted(df["Animal"].dropna().unique()))) if "Animal" in df.columns and not df["Animal"].isna().all() else "N/A"
                    unique_timepoints = ", ".join(map(str, sorted(df["Timepoint"].dropna().unique()))) if "Timepoint" in df.columns and not df["Timepoint"].isna().all() else "N/A"
                    unique_tissues = ", ".join(map(str, sorted(df["Tissue"].dropna().unique()))) if "Tissue" in df.columns and not df["Tissue"].isna().all() else "N/A"
                    table.setItem(row, 0, QTableWidgetItem(path_obj.name))
                    table.setItem(row, 1, QTableWidgetItem(str(num_samples)))
                    table.setItem(row, 2, QTableWidgetItem(unique_groups))
                    table.setItem(row, 3, QTableWidgetItem(unique_animals))
                    table.setItem(row, 4, QTableWidgetItem(unique_timepoints))
                    table.setItem(row, 5, QTableWidgetItem(unique_tissues))
                    row += 1
                except Exception as e:
                    logging.error(f"Summary preview failed for {selected_path}: {str(e)}", exc_info=True)
                    table.setItem(row, 0, QTableWidgetItem(f"{path_obj.name} - Error: Failed to parse ({str(e)})"))
                    row += 1
            preview_window = QMainWindow(window)
            preview_window.setWindowTitle("Combined Summary Preview")
            preview_window.setMinimumSize(400, 300)  # Minimum size, allows resizing
            # Removed fixed resize to allow resizing
            # preview_window.resize(600, 500)
            preview_window.setCentralWidget(table)
            preview_window.show()
            logging.info(f"Successfully opened combined summary preview table for {len(preview_paths)} files")

        preview_button.clicked.connect(preview_csv)
        logging.debug("Preview button connected successfully.")

    setup_gui_preview(preview_button, window, load_and_parse_df)

    def validate_inputs(input_paths: list[Path], output_dir: Path, auto_parse: bool, groups: list[int], replicates: list[int]) -> bool:
        try:
            if not input_paths:
                raise ValueError("No input files or folders selected.")
            invalid_paths = [p for p in input_paths if not p.exists()]
            if invalid_paths:
                raise ValueError(f"Invalid paths: {invalid_paths}")
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
            if not auto_parse and (not groups or not replicates):
                raise ValueError("Groups and replicates must be defined when manual mode is enabled.")
            logging.debug("Inputs validated successfully.")
            return True
        except ValueError as e:
            logging.error(f"Validation failed: {str(e)}")
            QMessageBox.critical(None, "Input Error", str(e))
            return False

    def process_selected_path():
        input_paths = [Path(p.strip()) for p in path_entry.text().split("; ") if p.strip()]
        output_dir = Path(out_dir_entry.text().strip() or ".")
        if not validate_inputs(input_paths, output_dir, AUTO_PARSE_GROUPS, USER_GROUPS, USER_REPLICATES):
            return

        global USER_GROUP_LABELS
        USER_GROUP_LABELS[:] = [s.strip() for s in group_labels_entry.text().split(",") if s.strip()]

        def set_status(msg):
            status_label.setText(msg)
            QApplication.processEvents()

        def process_file(input_path):
            if input_path.is_file() and input_path.suffix.lower() == '.csv':
                output_file = output_dir / f"{input_path.stem}_Processed{'_Timecourse' if time_course_checkbox.isChecked() else '_Grouped'}.xlsx"
                try:
                    if time_course_checkbox.isChecked():
                        df, _ = load_and_parse_df(input_path)
                        if df['Time'].isna().all():
                            set_status(f"Skipping {input_path.name}: No time data for time course mode")
                            QMessageBox.warning(window, "Warning", f"No time data found in {input_path.name}. Skipping.")
                            return None, None
                    process_csv(input_path, output_file, time_course_mode=time_course_checkbox.isChecked())
                    return input_path.name, output_file.name
                except Exception as e:
                    logging.error(f"Error processing {input_path}: {str(e)}")
                    return input_path.name, None
            elif input_path.is_dir():
                process_directory(input_path, output_dir, recursive=True, pattern="*.csv", status_callback=set_status, time_course_mode=time_course_checkbox.isChecked())
                return input_path.name, "folder processed"

        try:
            total_files = len(input_paths)
            progress_bar.setMaximum(total_files)
            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(process_file, input_paths))
            processed_count = len([r for r in results if r[1]])
            for idx, (input_name, output_name) in enumerate(results, 1):
                if output_name:
                    set_status(f"Processed {input_name} → {output_name}")
                    progress_bar.setValue(idx)
            if processed_count > 0:
                save_last_output_dir(str(output_dir))
                QMessageBox.information(window, "Done", f"Successfully processed {processed_count} items.")
                set_status("Ready")
            else:
                QMessageBox.critical(window, "Error", "No valid files or directories processed.")
                status_label.setText("Error")
        except Exception as e:
            status_label.setText("Error")
            QMessageBox.critical(window, "Processing error", str(e))

    process_button.clicked.connect(process_selected_path)

    add_tooltips_to_widgets(window, path_entry, browse_input_button, out_dir_entry, process_button, time_course_checkbox)

    window.show()
    logging.debug("GUI window shown")
    app.exec()
    logging.debug("GUI application exited")

def add_tooltips_to_widgets(window: QMainWindow, path_entry: QLineEdit, browse_input_button: QPushButton, out_dir_entry: QLineEdit, process_button: QPushButton, time_course_checkbox: QCheckBox) -> None:
    try:
        path_entry.setToolTip("Drag and drop CSV files or folders here, or browse to select.")
        browse_input_button.setToolTip("Browse for CSV files or folders to process.")
        out_dir_entry.setToolTip("Specify the directory where processed Excel files will be saved.")
        process_button.setToolTip("Start processing the selected files or folders.")
        time_course_checkbox.setToolTip("Enable this for time-course output format; requires 'Time' data in CSV.")
        logging.debug("Tooltips added to GUI widgets.")
    except AttributeError as e:
        logging.error(f"Error adding tooltips: Widget not found - {str(e)}")
        raise AttributeError("Failed to add tooltips due to missing widget.") from e

def clear_input(path_entry: QLineEdit) -> None:
    """Clear the input field and reset preview paths."""
    path_entry.clear()
    global preview_paths
    preview_paths = []  # Clear preview paths when input is cleared
    logging.debug("Input field and preview paths cleared.")

def load_last_output_dir(config_file: Path = Path("config.json")) -> str:
    try:
        with config_file.open("r") as f:
            config = json.load(f)
            return config.get("last_output_dir", str(Path.home() / "Desktop"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"Failed to load config: {str(e)} - Using default directory.")
        return str(Path.home() / "Desktop")

def save_last_output_dir(output_dir: str, config_file: Path = Path("config.json")) -> None:
    try:
        config = {"last_output_dir": output_dir}
        with config_file.open("w") as f:
            json.dump(config, f)
        logging.debug(f"Saved last output directory: {output_dir}")
    except IOError as e:
        logging.error(f"Failed to save config: {str(e)}")
        raise

if __name__ == "__main__":
    create_gui()