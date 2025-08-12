# File: flowproc/presentation/gui/views/components/ui_builder.py
"""
UI building and layout management.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QProgressBar, QSizePolicy, QWidget
)

from ..widgets.drop_line_edit import DropLineEdit
from ...config_handler import load_last_output_dir

if TYPE_CHECKING:
    from ..main_window import MainWindow

logger = logging.getLogger(__name__)


class UIBuilder:
    """
    Handles UI construction and layout management.
    
    Separates UI building logic from the main window class.
    """

    def __init__(self, main_window: MainWindow) -> None:
        self.main_window = main_window
        self.widgets: Dict[str, Any] = {}
        
    def build_complete_ui(self, main_layout: QVBoxLayout) -> None:
        """Build the complete user interface."""
        self._build_io_group(main_layout)
        self._build_process_controls(main_layout)
        self._build_progress_section(main_layout)
        self._setup_tooltips()

    def _build_io_group(self, parent_layout: QVBoxLayout) -> None:
        """Build the input/output group box."""
        # IO label
        io_label = QLabel("Input / Output")
        io_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #0064FF;")
        parent_layout.addWidget(io_label)

        self.widgets['io_group'] = QGroupBox()
        io_layout = QVBoxLayout(self.widgets['io_group'])
        io_layout.setSpacing(10)
        io_layout.setContentsMargins(15, 15, 15, 15)

        # Output Directory Section
        out_dir_section = QWidget()
        out_dir_layout = QVBoxLayout(out_dir_section)
        out_dir_layout.setContentsMargins(0, 0, 0, 0)
        out_dir_layout.setSpacing(5)
        
        out_dir_label = QLabel("Output Directory:")
        out_dir_label.setStyleSheet("font-weight: 500; color: #F0F0F0;")
        
        out_dir_input_widget = QWidget()
        out_dir_input_layout = QHBoxLayout(out_dir_input_widget)
        out_dir_input_layout.setContentsMargins(0, 0, 0, 0)
        out_dir_input_layout.setSpacing(10)
        
        self.widgets['out_dir_entry'] = QLineEdit(load_last_output_dir())
        self.widgets['out_dir_entry'].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.widgets['out_dir_entry'].setMinimumHeight(35)
        self.widgets['out_dir_button'] = QPushButton("Browse")
        self.widgets['out_dir_button'].setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.widgets['out_dir_button'].setMinimumHeight(35)
        
        out_dir_input_layout.addWidget(self.widgets['out_dir_entry'])
        out_dir_input_layout.addWidget(self.widgets['out_dir_button'])
        
        out_dir_layout.addWidget(out_dir_label)
        out_dir_layout.addWidget(out_dir_input_widget)

        # Input File/Folder Section
        input_section = QWidget()
        input_layout = QVBoxLayout(input_section)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)
        
        input_label = QLabel("Input File/Folder:")
        input_label.setStyleSheet("font-weight: 500; color: #F0F0F0;")
        
        input_input_widget = QWidget()
        input_input_layout = QHBoxLayout(input_input_widget)
        input_input_layout.setContentsMargins(0, 0, 0, 0)
        input_input_layout.setSpacing(10)
        
        self.widgets['path_entry'] = DropLineEdit(self.main_window)
        self.widgets['path_entry'].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.widgets['path_entry'].setMinimumHeight(35)
        
        self.widgets['browse_input_button'] = QPushButton("Browse")
        self.widgets['browse_input_button'].setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.widgets['browse_input_button'].setMinimumHeight(35)
        
        self.widgets['preview_button'] = QPushButton("Preview CSV")
        self.widgets['preview_button'].setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.widgets['preview_button'].setMinimumHeight(35)
        
        self.widgets['clear_button'] = QPushButton("Clear")
        self.widgets['clear_button'].setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.widgets['clear_button'].setMinimumHeight(35)
        
        input_input_layout.addWidget(self.widgets['path_entry'])
        input_input_layout.addWidget(self.widgets['browse_input_button'])
        input_input_layout.addWidget(self.widgets['preview_button'])
        input_input_layout.addWidget(self.widgets['clear_button'])
        
        input_layout.addWidget(input_label)
        input_layout.addWidget(input_input_widget)

        # Add sections to main IO layout
        io_layout.addWidget(out_dir_section)
        io_layout.addWidget(input_section)

        parent_layout.addWidget(self.widgets['io_group'])

    def _build_process_controls(self, parent_layout: QVBoxLayout) -> None:
        """Build the process control buttons."""
        process_controls = QWidget()
        controls_layout = QHBoxLayout(process_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Process button
        self.widgets['process_button'] = QPushButton("Process")
        self.widgets['process_button'].setFixedWidth(160)
        self.widgets['process_button'].setFixedHeight(48)
        self.widgets['process_button'].setStyleSheet(
            "border-radius: 10px; background-color: #007BFF; color: white;"
        )
        
        # Group Labels button
        self.widgets['group_labels_button'] = QPushButton("Group Labels")
        self.widgets['group_labels_button'].setFixedWidth(120)
        self.widgets['group_labels_button'].setFixedHeight(48)
        self.widgets['group_labels_button'].setStyleSheet("border-radius: 10px; background-color: #28a745;")
        
        # Manual Groups button
        self.widgets['manual_groups_button'] = QPushButton("Manual Groups")
        self.widgets['manual_groups_button'].setFixedWidth(120)
        self.widgets['manual_groups_button'].setFixedHeight(48)
        self.widgets['manual_groups_button'].setStyleSheet("border-radius: 10px; background-color: #FF6B35;")
        
        # Visualize button
        self.widgets['visualize_button'] = QPushButton("Visualize")
        self.widgets['visualize_button'].setFixedWidth(120)
        self.widgets['visualize_button'].setFixedHeight(48)
        self.widgets['visualize_button'].setStyleSheet("border-radius: 10px; background-color: #17a2b8;")
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.widgets['process_button'])
        controls_layout.addWidget(self.widgets['group_labels_button'])
        controls_layout.addWidget(self.widgets['manual_groups_button'])
        controls_layout.addWidget(self.widgets['visualize_button'])
        controls_layout.addStretch()
        
        parent_layout.addWidget(process_controls)

    def _build_progress_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the progress bar and status label."""
        self.widgets['progress_bar'] = QProgressBar()
        self.widgets['progress_bar'].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.widgets['progress_bar'].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.widgets['progress_bar'].setStyleSheet(
            "QProgressBar { background-color: #222222; color: #F0F0F0; "
            "border-radius: 4px; text-align: center; }"
        )
        parent_layout.addWidget(self.widgets['progress_bar'])

        self.widgets['status_label'] = QLabel("Ready")
        self.widgets['status_label'].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.widgets['status_label'].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.widgets['status_label'].setStyleSheet(
            "background-color: #222222; padding: 8px; border-radius: 4px; "
            "font-size: 14px; color: #A0A0A0;"
        )
        parent_layout.addWidget(self.widgets['status_label'])
        parent_layout.addStretch()

    def _setup_tooltips(self) -> None:
        """Add tooltips to GUI widgets for user guidance."""
        tooltips = {
            'path_entry': "Drag and drop CSV files or folders here, or browse to select.",
            'browse_input_button': "Browse for CSV files to process or visualize.",
            'out_dir_entry': "Specify the directory where processed Excel files will be saved.",
            'process_button': "Start processing the selected files or folders.",
            'group_labels_button': "Manage group labels for data processing.",
            'manual_groups_button': "Manually define groups and replicates for data processing.",
            'visualize_button': "Visualize data from the first CSV file. Metric can be changed in the dialog. Uses current group labels if set.",
            'preview_button': "Preview the structure of selected CSV files.",
            'clear_button': "Clear the input field and reset preview paths."
        }
        
        for widget_name, tooltip in tooltips.items():
            if widget_name in self.widgets:
                self.widgets[widget_name].setToolTip(tooltip)

    def set_processing_state(self, is_processing: bool) -> None:
        """Update UI state for processing mode."""
        self.widgets['process_button'].setEnabled(not is_processing)
        self.widgets['progress_bar'].setVisible(is_processing)
        
        if not is_processing:
            self.widgets['progress_bar'].setValue(0)

    def update_progress(self, value: int) -> None:
        """Update the progress bar value."""
        self.widgets['progress_bar'].setValue(value)

    def update_status(self, message: str) -> None:
        """Update the status label."""
        self.widgets['status_label'].setText(message)

    def get_widget(self, name: str) -> Any:
        """Get a widget by name."""
        return self.widgets.get(name)



    def update_layout_for_size(self, width: int, height: int) -> None:
        """Update layout based on window size changes."""
        # Adjust spacing and margins based on window size
        if width < 800:
            # Compact layout for small windows
            spacing = 8
            margins = 10
        elif width < 1000:
            # Medium layout
            spacing = 12
            margins = 15
        else:
            # Full layout for large windows
            spacing = 16
            margins = 20
        
        # Update main layout spacing if it exists
        if hasattr(self.main_window, 'main_layout'):
            self.main_window.main_layout.setSpacing(spacing)
            self.main_window.main_layout.setContentsMargins(margins, margins, margins, margins)
        
        logger.debug(f"Updated layout for window size: {width}x{height}, spacing: {spacing}, margins: {margins}")