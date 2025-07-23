# flowproc/gui.py
import os
import sys
import logging
from pathlib import Path

# Handle standalone execution
if __name__ == "__main__" and __package__ is None:
    # Add the parent directory to sys.path and set __package__ to simulate package context
    # Use PyInstaller-compatible path resolution
    if not hasattr(sys, '_MEIPASS'):
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
    __package__ = "flowproc"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QCheckBox, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QPalette, QColor, QFont, QDragEnterEvent, QDropEvent, QScreen
from .config import USER_GROUPS, USER_REPLICATES, AUTO_PARSE_GROUPS, USER_GROUP_LABELS, parse_range_or_list
from .writer import process_csv, process_directory
from .parsing import load_and_parse_df
from .logging_config import setup_logging

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
        mime_data: QMimeData = event.mimeData()
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
                event.acceptProposedAction()
            else:
                logging.debug("No valid paths dropped")
                QMessageBox.warning(self.parent(), "Invalid Drop", "Please drop only CSV files or folders.")
                event.ignore()
        else:
            logging.debug("No mime data with URLs")
            event.ignore()

def create_gui():
    """Create the main GUI window."""
    # Setup logging
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
            font-size: 12px; 
            font-family: 'Arial', sans-serif;
        }
        QLineEdit { 
            background-color: #191919; 
            color: #F0F0F0; 
            border: 1px solid #303030; 
            padding: 4px; 
            border-radius: 4px; 
            min-height: 24px;
        }
        QPushButton { 
            border: none; 
            background-color: #0064FF; 
            color: white; 
            padding: 6px 14px; 
            border-radius: 4px; 
            font-size: 12px; 
            min-height: 30px;
            font-weight: 600;
        }
        QPushButton:hover { 
            background-color: #004CCC; 
        }
        QCheckBox { 
            color: #FFFFFF; 
            font-size: 12px; 
            spacing: 5px; 
            padding: 2px; 
            background-color: transparent; 
            border-radius: 3px;
        }
        QCheckBox::indicator { 
            width: 13px; 
            height: 13px; 
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
            border: none; 
            margin-top: 12px; 
            color: #F0F0F0; 
            padding: 6px;
            background-color: #181818;
            border-radius: 4px;
        }
        QGroupBox::title { 
            subcontrol-origin: margin; 
            padding: 0 6px; 
            font-size: 14px; 
            font-weight: 600;
            color: #0064FF;
        }
    """)

    window = QMainWindow()
    window.setWindowTitle("Flow Cytometry Processor")
    window.setMinimumSize(600, 400)
    window.resize(700, 600)

    # Center the window on the screen
    screen = app.primaryScreen()
    screen_size = screen.size()
    window.move((screen_size.width() - window.width()) // 2, (screen_size.height() - window.height()) // 2)

    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(12, 12, 12, 12)
    main_layout.setSpacing(10)

    title_label = QLabel("Flow Cytometry Processor")
    title_label.setFont(QFont("Arial", 20, QFont.Bold))
    title_label.setStyleSheet("color: #0064FF;")
    title_label.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(title_label)

    desc_label = QLabel("Select a CSV file or folder to process and an output directory. Drag and drop CSV files or folders onto the input field!")
    desc_label.setWordWrap(True)
    desc_label.setAlignment(Qt.AlignCenter)
    desc_label.setStyleSheet("font-size: 13px; color: #A0A0A0;")
    main_layout.addWidget(desc_label)

    options_group = QGroupBox("Options")
    options_layout = QVBoxLayout(options_group)
    options_layout.setSpacing(4)
    time_course_checkbox = QCheckBox("Time Course Output Format")
    manual_groups_checkbox = QCheckBox("Manually Define Groups and Replicates")
    options_layout.addWidget(time_course_checkbox)
    options_layout.addWidget(manual_groups_checkbox)

    manual_widget = QWidget()
    manual_layout = QFormLayout(manual_widget)
    manual_layout.setContentsMargins(0, 0, 0, 0)
    manual_layout.setSpacing(3)
    groups_entry = QLineEdit("1,2,3")
    groups_entry.setEnabled(False)
    replicates_entry = QLineEdit("1,2")
    replicates_entry.setEnabled(False)
    save_button = QPushButton("Save")
    save_button.setEnabled(False)
    manual_layout.addRow("Group Numbers:", groups_entry)
    manual_layout.addRow("Replicate Numbers:", replicates_entry)
    manual_layout.addRow(save_button)
    options_layout.addWidget(manual_widget)
    main_layout.addWidget(options_group)

    io_group = QGroupBox("Input / Output")
    io_layout = QFormLayout(io_group)
    io_layout.setSpacing(4)

    out_dir_entry = QLineEdit(str(Path.home() / "Desktop"))
    def browse_output():
        folder = QFileDialog.getExistingDirectory(window, "Select Output Directory")
        if folder:
            out_dir_entry.setText(folder)
    out_dir_button = QPushButton("Browse")
    out_layout = QHBoxLayout()
    out_layout.addWidget(out_dir_entry)
    out_layout.addWidget(out_dir_button)
    out_widget = QWidget()
    out_widget.setLayout(out_layout)
    io_layout.addRow("Output Directory:", out_widget)
    out_dir_button.clicked.connect(browse_output)

    group_labels_entry = QLineEdit()
    io_layout.addRow("Group Labels (optional):", group_labels_entry)

    path_entry = DropLineEdit(window)
    def browse_input():
        file, _ = QFileDialog.getOpenFileName(window, "Select CSV File", "", "CSV files (*.csv)")
        if file:
            path_entry.setText(file)
            return
        folder = QFileDialog.getExistingDirectory(window, "Select Folder")
        if folder:
            path_entry.setText(folder)
    browse_input_button = QPushButton("Browse")
    browse_input_button.clicked.connect(browse_input)
    input_layout = QHBoxLayout()
    input_layout.addWidget(path_entry)
    input_layout.addWidget(browse_input_button)
    input_widget = QWidget()
    input_widget.setLayout(input_layout)
    io_layout.addRow("Input File/Folder:", input_widget)

    main_layout.addWidget(io_group)

    process_button = QPushButton("Process")
    process_button.setMaximumWidth(200)
    process_layout = QHBoxLayout()
    process_layout.addStretch()
    process_layout.addWidget(process_button)
    process_layout.addStretch()
    main_layout.addLayout(process_layout)

    status_label = QLabel("Ready")
    status_label.setAlignment(Qt.AlignCenter)
    status_label.setStyleSheet("background-color: #191919; padding: 6px; border-radius: 4px; font-size: 12px; color: #808080;")
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

    def process_selected_path():
        input_paths = [Path(p.strip()) for p in path_entry.text().split("; ") if p.strip()]
        if not input_paths:
            QMessageBox.critical(window, "Invalid Input", "No files or folder selected.")
            return

        invalid_paths = [p for p in input_paths if not p.exists()]
        if invalid_paths:
            QMessageBox.critical(window, "Invalid Input", f"The following paths do not exist: {invalid_paths}")
            return

        if not AUTO_PARSE_GROUPS and (not USER_GROUPS or not USER_REPLICATES):
            QMessageBox.critical(window, "Missing Info", "Please define groups and replicates before processing.")
            return

        output_dir = Path(out_dir_entry.text().strip() or ".")
        output_dir.mkdir(parents=True, exist_ok=True)

        global USER_GROUP_LABELS
        USER_GROUP_LABELS[:] = [s.strip() for s in group_labels_entry.text().split(",") if s.strip()]

        def set_status(msg):
            status_label.setText(msg)
            QApplication.processEvents()

        try:
            tc_mode = time_course_checkbox.isChecked()
            suffix = "_Processed_Timecourse.xlsx" if tc_mode else "_Processed_Grouped.xlsx"
            processed_count = 0
            total_files = len(input_paths)

            for input_path in input_paths:
                set_status(f"Processing {input_path.name} ({processed_count + 1} of {total_files})")
                if input_path.is_file() and input_path.suffix.lower() == '.csv':
                    output_file = output_dir / f"{input_path.stem}{suffix}"
                    if tc_mode:
                        df, _ = load_and_parse_df(input_path)
                        if df['Time'].isna().all():
                            set_status(f"Skipping {input_path.name}: No time data for time course mode")
                            QMessageBox.warning(window, "Warning", f"No time data found in {input_path.name}. Skipping.")
                            continue
                    process_csv(input_path, output_file, time_course_mode=tc_mode)
                    processed_count += 1
                    set_status(f"Processed {input_path.name} → {output_file.name}")
                elif input_path.is_dir():
                    process_directory(
                        input_dir=input_path,
                        output_dir=output_dir,
                        recursive=True,
                        pattern="*.csv",
                        status_callback=set_status,
                        time_course_mode=tc_mode,
                        output_suffix=suffix
                    )
                    processed_count += 1
                    set_status(f"Processed folder {input_path.name}")
                else:
                    QMessageBox.warning(window, "Warning", f"Skipping {input_path}: Not a file or directory.")

            if processed_count > 0:
                QMessageBox.information(window, "Done", f"Successfully processed {processed_count} items.")
                set_status("Ready")
            else:
                QMessageBox.critical(window, "Error", "No valid files or directories processed.")
                set_status("Error")

        except Exception as e:
            set_status("Error")
            QMessageBox.critical(window, "Processing error", str(e))

    process_button.clicked.connect(process_selected_path)

    window.show()
    logging.debug("GUI window shown")
    app.exec()
    logging.debug("GUI application exited")

if __name__ == "__main__":
    create_gui()