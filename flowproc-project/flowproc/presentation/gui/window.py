from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QProgressBar,
    QComboBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, QEvent, Slot
from PySide6.QtGui import QPalette, QColor, QFont
from pathlib import Path
import logging
from typing import List, Optional

from .widgets import DropLineEdit
from .config_handler import load_last_output_dir, save_last_output_dir
from .processor import validate_inputs
from .async_processor import ProcessingManager, ProcessingResult, ProcessingState
from .visualizer import visualize_metric
from ...config import USER_GROUPS, USER_REPLICATES, AUTO_PARSE_GROUPS, USER_GROUP_LABELS, parse_range_or_list
from ...core.constants import KEYWORDS

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main window for the Flow Cytometry Processor GUI with async processing."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Flow Cytometry Processor")
        self.preview_paths: List[str] = []
        self.last_csv: Optional[Path] = None
        
        # Initialize processing manager
        self.processing_manager = ProcessingManager(self)

        self.setup_palette_and_style()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)

        self.setup_options_group()
        self.setup_io_group()
        self.setup_process_controls()
        self.setup_visualize_section()
        self.setup_progress_and_status()

        self.add_tooltips()
        self.connect_signals()
        
        # Center window on screen
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        self.move((screen_size.width() - self.width()) // 2, 
                  (screen_size.height() - self.height()) // 2)
        
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.processing_manager.is_processing():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Processing is still running. Do you want to cancel and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.processing_manager.cancel_processing()
                event.accept()
            else:
                event.ignore()
        else:
            self.processing_manager.cleanup()
            event.accept()

    def setup_palette_and_style(self) -> None:
        """Set up the dark palette and apply the application stylesheet."""
        from typing import cast
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(15, 15, 15))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 100, 255))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        app = cast(QApplication, QApplication.instance())
        app.setPalette(dark_palette)

        app.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #0F0F0F; border-radius: 8px; }
            QLabel { color: #F0F0F0; font-size: 14px; font-family: 'Arial', sans-serif; }
            QLineEdit { background-color: #191919; color: #F0F0F0; border: 1px solid #303030;
                        padding: 8px; border-radius: 4px; min-height: 40px; max-width: 480px; }
            QLineEdit#groupEntry { min-height: 40px; }
            QPushButton { border: none; background-color: #007BFF; color: white; padding: 8px 16px;
                          border-radius: 4px; font-size: 12px; min-height: 30px; font-weight: 600; }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:disabled { background-color: #4A4A4A; color: #888888; }
            QPushButton#cancelButton { background-color: #DC3545; }
            QPushButton#cancelButton:hover { background-color: #B02A37; }
            QPushButton#pauseButton { background-color: #FFC107; color: #212529; }
            QPushButton#pauseButton:hover { background-color: #E0A800; }
            QCheckBox { color: #FFFFFF; font-size: 12px; spacing: 8px; padding: 4px;
                        background-color: transparent; border-radius: 3px; }
            QCheckBox::indicator { width: 16px; height: 16px; border: 2px solid #0064FF;
                                   background-color: #1A1A1A; border-radius: 3px; }
            QCheckBox::indicator:checked { background-color: #0064FF; border: 2px solid #0064FF;
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAdUlEQVQYV2NkYGBg+P//PwO2gYGBISHBgP8/A4j3798Z4D9//gT+//8fQ2kQJycnGfD///8M6O7uZqCvr28Gtm/fZqC3t7cZ6OvrZwC4uLiA4eHhAobRaCQAe/fuZqCnpycD9+7dA4hGo2kA7O3tZqC7u/sMABkKeg1K9n2GAAAAAElFTkSuQmCC); }
            QCheckBox::indicator:hover { background-color: #252525; }
            QCheckBox::indicator:checked:hover { background-color: #004CCC; }
            QGroupBox { border: 1px solid #303030; margin-top: 0px; color: #F0F0F0; padding: 10px;
                        border-radius: 6px; }
            QGroupBox::title { subcontrol-origin: margin; padding: 0 8px; font-size: 16px;
                               font-weight: 600; color: #0064FF; }
            QProgressBar { background-color: #222222; color: #F0F0F0; border-radius: 4px;
                           text-align: center; min-height: 30px; }
            QProgressBar::chunk { background-color: #0064FF; border-radius: 4px; }
            QTableWidget { background-color: #191919; color: #F0F0F0; border: 1px solid #303030;
                           gridline-color: #303030; selection-background-color: #0064FF;
                           selection-color: #FFFFFF; }
            QTableWidget::item { padding: 4px; }
            QComboBox { background-color: #191919; color: #F0F0F0; border: 1px solid #303030;
                        padding: 8px; border-radius: 4px; min-height: 40px; }
            QDialog { background-color: #0F0F0F; }
            """
        )

    def setup_options_group(self) -> None:
        """Set up the options group box with checkboxes and manual input fields."""
        options_label = QLabel("Options")
        options_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #0064FF;")
        self.main_layout.addWidget(options_label)

        self.options_group = QGroupBox()
        options_layout = QVBoxLayout(self.options_group)
        options_layout.setSpacing(10)

        self.time_course_checkbox = QCheckBox("Time Course Output Format")
        self.time_course_checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.manual_groups_checkbox = QCheckBox("Manually Define Groups and Replicates")
        self.manual_groups_checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.manual_groups_checkbox)
        checkbox_layout.addStretch()
        checkbox_layout.addWidget(self.time_course_checkbox)
        options_layout.addLayout(checkbox_layout)

        self.manual_widget = QWidget()
        manual_layout = QVBoxLayout(self.manual_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(10)

        group_row = QWidget()
        group_layout = QHBoxLayout(group_row)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_label = QLabel("Group Numbers:")
        group_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.groups_entry = QLineEdit("1-10")
        self.groups_entry.setEnabled(False)
        self.groups_entry.setObjectName("groupEntry")
        self.groups_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.groups_entry.setFixedHeight(40)
        self.groups_entry.setFixedWidth(400)
        group_layout.addWidget(group_label)
        group_layout.addSpacing(10)
        group_layout.addWidget(self.groups_entry)

        replicate_row = QWidget()
        replicate_layout = QHBoxLayout(replicate_row)
        replicate_layout.setContentsMargins(0, 0, 0, 0)
        replicate_label = QLabel("Replicate Numbers:")
        replicate_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.replicates_entry = QLineEdit("1-3")
        self.replicates_entry.setEnabled(False)
        self.replicates_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.replicates_entry.setFixedHeight(40)
        self.replicates_entry.setFixedWidth(400)
        replicate_layout.addWidget(replicate_label)
        replicate_layout.addSpacing(10)
        replicate_layout.addWidget(self.replicates_entry)

        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)
        self.save_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.save_button.setFixedHeight(30)

        manual_row_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        left_layout.addWidget(group_row)
        left_layout.addWidget(replicate_row)
        right_layout = QVBoxLayout()
        right_layout.addStretch()
        right_layout.addWidget(self.save_button)
        right_layout.addStretch()
        manual_row_layout.addLayout(left_layout, stretch=1)
        manual_row_layout.addLayout(right_layout, stretch=0)
        manual_layout.addLayout(manual_row_layout)
        options_layout.addWidget(self.manual_widget)

        self.main_layout.addWidget(self.options_group)

    def setup_io_group(self) -> None:
        """Set up the input/output group box with file/folder selection."""
        io_label = QLabel("Input / Output")
        io_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #0064FF;")
        self.main_layout.addWidget(io_label)

        self.io_group = QGroupBox()
        io_layout = QFormLayout(self.io_group)
        io_layout.setSpacing(10)
        io_layout.setVerticalSpacing(10)
        io_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        io_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        out_dir_widget = QWidget()
        out_dir_layout = QHBoxLayout(out_dir_widget)
        out_dir_layout.setContentsMargins(0, 0, 0, 0)
        out_dir_label = QLabel("Output Directory:")
        out_dir_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.out_dir_entry = QLineEdit(load_last_output_dir())
        self.out_dir_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.out_dir_entry.setFixedWidth(400)
        self.out_dir_button = QPushButton("Browse")
        self.out_dir_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        out_dir_layout.addWidget(out_dir_label)
        out_dir_layout.addSpacing(10)
        out_dir_layout.addWidget(self.out_dir_entry)
        out_dir_layout.addStretch()
        out_dir_layout.addWidget(self.out_dir_button, alignment=Qt.AlignmentFlag.AlignRight)
        io_layout.addRow(out_dir_widget)

        group_labels_widget = QWidget()
        group_labels_layout = QHBoxLayout(group_labels_widget)
        group_labels_layout.setContentsMargins(0, 0, 0, 0)
        group_labels_layout.addWidget(QLabel("Group Labels (optional):"))
        self.group_labels_entry = QLineEdit()
        self.group_labels_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.group_labels_entry.setFixedWidth(400)
        self.group_labels_entry.setPlaceholderText("Comma-separated group names")
        group_labels_layout.addStretch()
        group_labels_layout.addWidget(self.group_labels_entry)
        io_layout.addRow(group_labels_widget)

        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_label = QLabel("Input File/Folder:")
        input_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.path_entry = DropLineEdit(self)
        self.path_entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.path_entry.setFixedWidth(400)
        self.browse_input_button = QPushButton("Browse")
        self.browse_input_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.preview_button = QPushButton("Preview CSV")
        self.preview_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.clear_button = QPushButton("Clear")
        self.clear_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        input_layout.addWidget(input_label)
        input_layout.addSpacing(10)
        input_layout.addWidget(self.path_entry)
        input_layout.addStretch()
        input_layout.addWidget(self.browse_input_button)
        input_layout.addWidget(self.preview_button)
        input_layout.addWidget(self.clear_button)
        io_layout.addRow(input_widget)

        self.main_layout.addWidget(self.io_group)

    def setup_process_controls(self) -> None:
        """Set up the process control buttons with async support."""
        process_controls = QWidget()
        controls_layout = QHBoxLayout(process_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Process button
        self.process_button = QPushButton("Process")
        self.process_button.setFixedWidth(160)
        self.process_button.setFixedHeight(48)
        self.process_button.setStyleSheet(
            "border-radius: 10px; background-color: #007BFF; color: white;"
        )
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.setFixedHeight(48)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet("border-radius: 10px;")
        
        # Pause/Resume button
        self.pause_button = QPushButton("Pause")
        self.pause_button.setFixedWidth(100)
        self.pause_button.setFixedHeight(48)
        self.pause_button.setObjectName("pauseButton")
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet("border-radius: 10px;")
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.process_button)
        controls_layout.addWidget(self.cancel_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addStretch()
        
        self.main_layout.addWidget(process_controls)

    def setup_visualize_section(self) -> None:
        """Set up the visualization selection section."""
        visualize_label = QLabel("Select Metric to Visualize:")
        self.visualize_combo = QComboBox()
        self.visualize_combo.addItems(list(KEYWORDS.keys()))
        self.visualize_button = QPushButton("Visualize")
        visualize_layout = QHBoxLayout()
        visualize_layout.addWidget(visualize_label)
        self.visualize_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        visualize_layout.addWidget(self.visualize_combo)
        visualize_layout.addWidget(self.visualize_button)
        self.main_layout.addLayout(visualize_layout)

    def setup_progress_and_status(self) -> None:
        """Set up the progress bar and status label."""
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #222222; color: #F0F0F0; "
            "border-radius: 4px; text-align: center; }"
        )
        self.main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.status_label.setStyleSheet(
            "background-color: #222222; padding: 8px; border-radius: 4px; "
            "font-size: 14px; color: #A0A0A0;"
        )
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addStretch()

    def connect_signals(self) -> None:
        """Connect all widget signals to their handlers."""
        self.manual_groups_checkbox.stateChanged.connect(self.toggle_manual)
        self.save_button.clicked.connect(self.save_definitions)
        self.out_dir_button.clicked.connect(self.browse_output)
        self.browse_input_button.clicked.connect(self.browse_input)
        self.clear_button.clicked.connect(self.clear_input)
        self.preview_button.clicked.connect(self.preview_csv)
        self.process_button.clicked.connect(self.process_selected_path)
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.visualize_button.clicked.connect(self.visualize_selected)
        self.path_entry.textChanged.connect(self.update_preview_paths)

    def toggle_manual(self, state: int) -> None:
        """Toggle manual group/replicate mode based on checkbox state."""
        global AUTO_PARSE_GROUPS
        AUTO_PARSE_GROUPS = not bool(state)
        enabled = bool(state)
        self.groups_entry.setEnabled(enabled)
        self.replicates_entry.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        if not enabled:
            USER_GROUPS.clear()
            USER_REPLICATES.clear()
        self.status_label.setText(
            "Manual group/replicate mode enabled." if enabled else "Automatic parsing enabled."
        )

    def save_definitions(self) -> None:
        """Save user-defined groups and replicates."""
        try:
            USER_GROUPS[:] = parse_range_or_list(self.groups_entry.text().strip())
            USER_REPLICATES[:] = parse_range_or_list(self.replicates_entry.text().strip())
            if not USER_GROUPS or not USER_REPLICATES:
                raise ValueError("Groups and replicates cannot be empty.")
            self.status_label.setText("Groups and replicates saved.")
        except ValueError as e:
            QMessageBox.critical(self, "Input Error", str(e))

    def update_preview_paths(self) -> None:
        """Update the list of previewable CSV paths."""
        file_paths = self.path_entry.text().split("; ")
        self.preview_paths = [
            p for p in file_paths 
            if p and Path(p).is_file() and Path(p).suffix.lower() == '.csv' and Path(p).exists()
        ]
        if self.preview_paths:
            self.last_csv = Path(self.preview_paths[0])
            logger.info(f"Set last_csv to {self.last_csv}")
        else:
            self.last_csv = None

    def browse_output(self) -> None:
        """Handle browsing for an output directory."""
        logger.debug("Browse output directory triggered")
        options = QFileDialog.Option.DontUseNativeDialog
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", str(Path.home()), options=options
        )
        if folder:
            self.out_dir_entry.setText(folder)
            logger.debug(f"Selected output directory: {folder}")

    def browse_input(self) -> None:
        """Handle browsing for input CSV files."""
        logger.debug("Browse input files triggered")
        options = QFileDialog.Option.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select CSV Files", str(Path.home()), "CSV files (*.csv)", options=options
        )
        if files:
            self.path_entry.setText("; ".join(files))
            self.update_preview_paths()

    def clear_input(self) -> None:
        """Clear the input field and reset preview paths."""
        self.path_entry.clear()
        self.preview_paths = []
        self.last_csv = None
        logger.debug("Input field and preview paths cleared.")

    def preview_csv(self) -> None:
        """Display a preview table for selected CSV files."""
        from ...parsing import load_and_parse_df
        
        if not self.preview_paths:
            QMessageBox.warning(self, "Invalid Input", "No valid CSV files available for preview.")
            return
            
        table = QTableWidget(len(self.preview_paths), 6)
        table.setHorizontalHeaderLabels(["File", "Samples", "Groups", "Animal Range", "Timepoint", "Tissue"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        row = 0
        for selected_path in self.preview_paths:
            path_obj = Path(selected_path)
            if not path_obj.exists() or not path_obj.is_file() or path_obj.suffix.lower() != '.csv':
                table.setItem(row, 0, QTableWidgetItem(f"{path_obj.name} - Error: Invalid file"))
                row += 1
                continue
                
            try:
                df, _ = load_and_parse_df(path_obj)
                num_samples = len(df)
                unique_groups = ", ".join(map(str, sorted(df["Group"].dropna().unique()))) if "Group" in df.columns and not df["Group"].isna().all() else "N/A"
                unique_animals = ", ".join(map(str, sorted(df["Animal"].dropna().unique()))) if "Animal" in df.columns and not df["Animal"].isna().all() else "N/A"
                unique_timepoints = ", ".join(map(str, sorted(df["Time"].dropna().unique()))) if "Time" in df.columns and not df["Time"].isna().all() else "N/A"
                unique_tissues = ", ".join(map(str, sorted(df["Tissue"].dropna().unique()))) if "Tissue" in df.columns and not df["Tissue"].isna().all() else "N/A"
                
                table.setItem(row, 0, QTableWidgetItem(path_obj.name))
                table.setItem(row, 1, QTableWidgetItem(str(num_samples)))
                table.setItem(row, 2, QTableWidgetItem(unique_groups))
                table.setItem(row, 3, QTableWidgetItem(unique_animals))
                table.setItem(row, 4, QTableWidgetItem(unique_timepoints))
                table.setItem(row, 5, QTableWidgetItem(unique_tissues))
                row += 1
            except Exception as e:
                logger.error(f"Summary preview failed for {selected_path}: {str(e)}", exc_info=True)
                table.setItem(row, 0, QTableWidgetItem(f"{path_obj.name} - Error: Failed to parse ({str(e)})"))
                row += 1
                
        preview_window = QMainWindow(self)
        preview_window.setWindowTitle("Combined Summary Preview")
        preview_window.setMinimumSize(400, 300)
        preview_window.setCentralWidget(table)
        preview_window.show()
        logger.info(f"Opened combined summary preview for {len(self.preview_paths)} files")

    def process_selected_path(self) -> None:
        """Process the selected input paths using async processing."""
        input_paths = [Path(p.strip()) for p in self.path_entry.text().split("; ") if p.strip()]
        output_dir = Path(self.out_dir_entry.text().strip() or ".")
        
        if not validate_inputs(input_paths, output_dir, AUTO_PARSE_GROUPS, USER_GROUPS, USER_REPLICATES):
            return

        USER_GROUP_LABELS[:] = [s.strip() for s in self.group_labels_entry.text().split(",") if s.strip()]

        # Update UI state
        self.process_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        
        # Start async processing
        success = self.processing_manager.start_processing(
            input_paths=input_paths,
            output_dir=output_dir,
            time_course_mode=self.time_course_checkbox.isChecked(),
            user_replicates=USER_REPLICATES if not AUTO_PARSE_GROUPS and USER_REPLICATES else None,
            auto_parse_groups=AUTO_PARSE_GROUPS,
            user_group_labels=USER_GROUP_LABELS if USER_GROUP_LABELS else None,
            user_groups=USER_GROUPS if not AUTO_PARSE_GROUPS and USER_GROUPS else None,
            progress_callback=self.on_progress_updated,
            status_callback=self.on_status_updated,
            completion_callback=self.on_processing_completed
        )
        
        if not success:
            QMessageBox.warning(self, "Processing Error", "Failed to start processing.")
            self.reset_ui_state()

    def cancel_processing(self) -> None:
        """Cancel the current processing operation."""
        reply = QMessageBox.question(
            self,
            "Cancel Processing",
            "Are you sure you want to cancel the current processing?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.processing_manager.cancel_processing()
            self.status_label.setText("Cancelling...")
            self.cancel_button.setEnabled(False)

    def toggle_pause(self) -> None:
        """Toggle pause/resume for processing."""
        state = self.processing_manager.get_state()
        
        if state == ProcessingState.PAUSED:
            self.processing_manager.resume_processing()
            self.pause_button.setText("Pause")
            self.status_label.setText("Resumed processing...")
        else:
            self.processing_manager.pause_processing()
            self.pause_button.setText("Resume")
            self.status_label.setText("Paused")

    @Slot(int)
    def on_progress_updated(self, value: int) -> None:
        """Handle progress updates from the processing worker."""
        self.progress_bar.setValue(value)

    @Slot(str)
    def on_status_updated(self, message: str) -> None:
        """Handle status updates from the processing worker."""
        self.status_label.setText(message)
        QApplication.processEvents()

    @Slot(ProcessingResult)
    def on_processing_completed(self, result: ProcessingResult) -> None:
        """Handle processing completion."""
        self.reset_ui_state()
        
        if result.last_csv_path:
            self.last_csv = result.last_csv_path
            
        if result.processed_count > 0:
            save_last_output_dir(str(Path(self.out_dir_entry.text())))
            
            if result.failed_count > 0:
                QMessageBox.warning(
                    self,
                    "Processing Complete with Errors",
                    f"Processed {result.processed_count} items successfully.\n"
                    f"Failed to process {result.failed_count} items.\n"
                    f"Check the log for details."
                )
            else:
                QMessageBox.information(
                    self,
                    "Processing Complete",
                    f"Successfully processed {result.processed_count} items in "
                    f"{result.total_time:.1f} seconds."
                )
            self.status_label.setText("Ready")
        else:
            QMessageBox.critical(
                self,
                "Processing Failed",
                f"No files were processed successfully.\n"
                f"Errors: {', '.join(result.error_messages[:3])}"
            )
            self.status_label.setText("Error")

    def reset_ui_state(self) -> None:
        """Reset UI controls to default state."""
        self.process_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("Pause")

    def visualize_selected(self) -> None:
        """Generate and display a visualization for the selected metric."""
        metric = self.visualize_combo.currentText()
        visualize_metric(
            csv_path=self.last_csv,
            metric=metric,
            time_course_mode=self.time_course_checkbox.isChecked(),
            parent_widget=self
        )

    def add_tooltips(self) -> None:
        """Add tooltips to GUI widgets for user guidance."""
        self.path_entry.setToolTip("Drag and drop CSV files or folders here, or browse to select.")
        self.browse_input_button.setToolTip("Browse for CSV files to process or visualize.")
        self.out_dir_entry.setToolTip("Specify the directory where processed Excel files will be saved.")
        self.process_button.setToolTip("Start processing the selected files or folders.")
        self.cancel_button.setToolTip("Cancel the current processing operation.")
        self.pause_button.setToolTip("Pause or resume the current processing operation.")
        self.time_course_checkbox.setToolTip("Enable for time-course output; requires 'Time' data in CSV.")
        self.visualize_button.setToolTip("Visualize selected metric from the first CSV file.")
        self.visualize_combo.setToolTip("Select a metric to visualize (e.g., Freq. of Parent).")
        logger.debug("Tooltips added to GUI widgets")