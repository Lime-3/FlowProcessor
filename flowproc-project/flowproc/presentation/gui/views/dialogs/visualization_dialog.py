"""
Single Visualization Dialog

This module provides a unified visualization interface that goes directly from
button click to final visualization display without intermediate dialogs.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QComboBox, QCheckBox, QPushButton, QMessageBox,
    QWidget, QSplitter, QSizePolicy, QApplication,
    QFileDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Signal, Qt, QThread, Slot
import pandas as pd

from flowproc.domain.parsing import load_and_parse_df
# Import moved to where it's used to avoid circular imports
from .visualization_options import VisualizationOptions
from .visualization_filters import (
    detect_population_options,
    build_tissue_entries,
    build_time_entries,
    detect_time_column,
)

logger = logging.getLogger(__name__)


 


class VisualizationDialog(QDialog):
    """
    Single, unified dialog for flow cytometry visualization.
    
    This dialog combines options configuration and plot display in one interface,
    eliminating the need for multiple dialog layers.
    """
    
    # Signals
    plot_generated = Signal()
    
    def __init__(self, parent=None, csv_path: Optional[Path] = None):
        super().__init__(parent)
        self.csv_path = csv_path
        self.temp_html_file: Optional[Path] = None
        self.current_fig: Optional[object] = None
        self._export_thread: Optional[QThread] = None
        
        # UI Components
        self.plot_type_combo: Optional[QComboBox] = None
        self.y_axis_combo: Optional[QComboBox] = None
        self.time_course_checkbox: Optional[QCheckBox] = None
        self.tissue_filter: Optional[QListWidget] = None
        self.time_filter: Optional[QListWidget] = None
        self.population_filter: Optional[QComboBox] = None  # New: population dropdown
        self.web_view: Optional[object] = None
        self.status_label: Optional[QLabel] = None
        
        self.setWindowTitle("Flow Cytometry Visualization")
        self.setModal(False)
        
        # Set size policy to allow resizing
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Get screen dimensions for dynamic sizing
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.size()
            target_width = min(int(screen_size.width() * 0.8), 1200)
            target_height = min(int(screen_size.height() * 0.8), 800)
            self.resize(target_width, target_height)
        else:
            self.resize(1000, 700)
        
        self._setup_ui()
        self._setup_styling()
        
        # Load and analyze data if CSV path provided
        if self.csv_path:
            self._analyze_data()
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        main_layout = QVBoxLayout(self)
        
        # Settings panel at the top with fixed height
        settings_widget = self._create_settings_panel()
        settings_widget.setFixedHeight(180)  # Fixed height for settings panel
        main_layout.addWidget(settings_widget)
        
        # Create splitter for plot display
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Plot display (takes full width now)
        plot_widget = self._create_plot_panel()
        splitter.addWidget(plot_widget)
        
        # Status bar at bottom with fixed height
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(5, 5, 5, 5)
        status_layout.setSpacing(10)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #191919; border-top: 1px solid #303030; color: #F0F0F0;")
        status_layout.addWidget(self.status_label)
        
        # Add cancel button for PDF export
        self.cancel_pdf_button = QPushButton("Cancel PDF Export")
        self.cancel_pdf_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #ccc;
            }
        """)
        self.cancel_pdf_button.clicked.connect(self.stop_pdf_export)
        self.cancel_pdf_button.setEnabled(False)
        status_layout.addWidget(self.cancel_pdf_button)
        
        status_widget.setFixedHeight(40)  # Increased height for button
        main_layout.addWidget(status_widget)
    
    def _create_settings_panel(self):
        """Create the settings configuration panel at the top."""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(15)
        
        # Basic Options Group
        basic_group = QGroupBox("Visualization Settings")
        basic_group.setStyleSheet("QGroupBox { border: 1px solid #404040; border-radius: 4px; margin-top: 8px; padding-top: 8px; }")
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setContentsMargins(8, 8, 8, 8)  # Tighter margins
        
        # Add top stretch to center content vertically
        basic_layout.addStretch()
        
        # Single row: Plot type, Y-axis, Mode, Tissue filter, Time filter, and Action buttons
        main_row = QHBoxLayout()
        
        # Plot type selection
        plot_type_layout = QVBoxLayout()
        plot_type_layout.setSpacing(5)  # Consistent spacing between label and control
        plot_type_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["bar", "box", "scatter", "line"])
        self.plot_type_combo.currentTextChanged.connect(self._on_option_changed)
        plot_type_layout.addWidget(self.plot_type_combo)
        plot_type_layout.addStretch()  # Push content to top
        main_row.addLayout(plot_type_layout)
        
        # Y-axis selection
        y_axis_layout = QVBoxLayout()
        y_axis_layout.setSpacing(5)  # Consistent spacing between label and control
        y_axis_layout.addWidget(QLabel("Y-Axis:"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.currentTextChanged.connect(self._on_option_changed)
        y_axis_layout.addWidget(self.y_axis_combo)
        y_axis_layout.addStretch()  # Push content to top
        main_row.addLayout(y_axis_layout)
        
        # Time course mode
        time_course_layout = QVBoxLayout()
        time_course_layout.setSpacing(5)  # Consistent spacing between label and control
        time_course_layout.addWidget(QLabel("Mode:"))
        self.time_course_checkbox = QCheckBox("Time Course Mode")
        self.time_course_checkbox.toggled.connect(self._on_time_course_toggled)
        time_course_layout.addWidget(self.time_course_checkbox)
        time_course_layout.addStretch()  # Push content to top
        main_row.addLayout(time_course_layout)
        
        # Tissue filter
        tissue_filter_layout = QVBoxLayout()
        tissue_filter_layout.setSpacing(5)  # Consistent spacing between label and control
        self.tissue_filter_label = QLabel("Tissue Filter:")
        tissue_filter_layout.addWidget(self.tissue_filter_label)
        self.tissue_filter = QListWidget()
        self.tissue_filter.setMaximumHeight(80)
        # Use NoSelection mode to rely on checkboxes instead of selection highlighting
        self.tissue_filter.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.tissue_filter.itemChanged.connect(self._on_filter_changed)
        tissue_filter_layout.addWidget(self.tissue_filter)
        tissue_filter_layout.addStretch()  # Push content to top
        main_row.addLayout(tissue_filter_layout)
        
        # Time filter
        self.time_filter_layout = QVBoxLayout()
        self.time_filter_layout.setSpacing(5)  # Consistent spacing between label and control
        self.time_filter_label = QLabel("Time Filter:")
        self.time_filter_layout.addWidget(self.time_filter_label)
        self.time_filter = QListWidget()
        self.time_filter.setMaximumHeight(80)
        # Use NoSelection mode to rely on checkboxes instead of selection highlighting
        self.time_filter.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.time_filter.itemChanged.connect(self._on_filter_changed)
        self.time_filter_layout.addWidget(self.time_filter)
        self.time_filter_layout.addStretch()  # Push content to top
        main_row.addLayout(self.time_filter_layout)
        
        # Population filter (only visible in timecourse mode)
        self.population_filter_layout = QVBoxLayout()
        self.population_filter_layout.setSpacing(5)  # Consistent spacing between label and control
        self.population_filter_label = QLabel("Population Filter:")
        self.population_filter_layout.addWidget(self.population_filter_label)
        self.population_filter = QComboBox()
        self.population_filter.currentTextChanged.connect(self._on_filter_changed)
        self.population_filter_layout.addWidget(self.population_filter)
        self.population_filter_layout.addStretch()  # Push content to the top
        main_row.addLayout(self.population_filter_layout)
        
        # Initially hide population filter (only show in timecourse mode)
        self.population_filter_label.setVisible(False)
        self.population_filter.setVisible(False)
        
        # Action Buttons - stacked vertically to the right of filters
        button_layout = QVBoxLayout()
        button_layout.addStretch()  # Push buttons to the top
        
        save_button = QPushButton("Save Plot")
        save_button.setMinimumHeight(40)
        save_button.clicked.connect(self._save_visualization)
        button_layout.addWidget(save_button)
        
        button_layout.addStretch()  # Add spacing at bottom
        main_row.addLayout(button_layout)
        
        basic_layout.addLayout(main_row)
        
        # Add bottom stretch to center content vertically
        basic_layout.addStretch()
        settings_layout.addWidget(basic_group)
        
        return settings_widget
    
    def _create_plot_panel(self):
        """Create the plot display panel."""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(10, 10, 10, 10)
        
        # Web view for plot display (lazy import with graceful fallback)
        import os
        if os.environ.get('PYTEST_CURRENT_TEST'):
            placeholder = QLabel("Web preview disabled during tests")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            plot_layout.addWidget(placeholder)
        else:
            try:
                from PySide6.QtWebEngineWidgets import QWebEngineView  # type: ignore
                self.web_view = QWebEngineView()
                self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                plot_layout.addWidget(self.web_view)
            except Exception:
                # Fallback placeholder to avoid crashes in environments without WebEngine
                placeholder = QLabel("Web engine unavailable; plot preview disabled in this environment")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                plot_layout.addWidget(placeholder)
        
        return plot_widget
    
    def _setup_styling(self):
        """Apply consistent styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F0F;
                color: #F0F0F0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #303030;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                color: #F0F0F0;
                background-color: #191919;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #0064FF;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton {
                background-color: #0064FF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
                min-height: 30px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0052CC;
            }
            QPushButton:pressed {
                background-color: #004099;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #303030;
                border-radius: 4px;
                background-color: #191919;
                color: #F0F0F0;
                min-width: 120px;
                min-height: 40px;
            }
            QComboBox:focus {
                border-color: #0064FF;
            }
            QComboBox:hover {
                border-color: #404040;
            }
            QComboBox QAbstractItemView {
                background-color: #191919;
                border: 1px solid #303030;
                selection-background-color: #0064FF;
                color: #F0F0F0;
            }
            QCheckBox {
                spacing: 8px;
                color: #F0F0F0;
                font-size: 12px;
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
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAdUlEQVQYV2NkYGBg+P//PwO2gYGBISHBgP8/A4j3798Z4D9//gT+//8fQ2kQJycnGfD///8M6O7uZqC3t7cZ6OvrZwC4uLiA4eHhAobRaCQAe/fuZqCnpycD9+7dA4hGo2kA7O3tZqC7u/sMABkKeg1K9n2GAAAAAElFTkSuQmCC);
            }
            QCheckBox::indicator:hover {
                background-color: #252525;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #004CCC;
            }
            QLabel {
                color: #F0F0F0;
                font-size: 14px;
                font-family: 'Arial', sans-serif;
            }
            QWidget {
                background-color: #0F0F0F;
                color: #F0F0F0;
            }
            QListWidget {
                background-color: #191919;
                border: 1px solid #303030;
                border-radius: 4px;
                padding: 4px;
                color: #F0F0F0;
                selection-background-color: #0064FF;
            }
            QListWidget::item {
                padding: 2px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #0064FF;
            }
            QListWidget::item:hover {
                background-color: #252525;
            }
        """)
    
    def _analyze_data(self):
        """Analyze the loaded data and populate options."""
        try:
            if not self.csv_path or not self.csv_path.exists():
                self.status_label.setText("Error: CSV file not found")
                return
            
            # Load data for analysis only (not stored)
            df, _ = load_and_parse_df(self.csv_path)
            
            if df is None or df.empty:
                self.status_label.setText("Error: No data found in CSV file")
                return
            
            # Populate column options
            self._populate_column_options(df)
            
            # Populate filter options
            self._populate_filter_options(df)
            
            # Force a UI update to ensure all widgets have processed their state changes
            QApplication.processEvents()
            
            # Auto-generate initial plot if filters are available
            has_tissue_data = 'Tissue' in df.columns and not df['Tissue'].isna().all()
            has_time_data = 'Time' in df.columns and len(df['Time'].dropna().unique()) > 0
            
            # Check if we have real tissue data (not just UNK)
            has_real_tissue_data = False
            if has_tissue_data:
                unique_tissues = df['Tissue'].dropna().unique()
                real_tissues = [t for t in unique_tissues if t != 'UNK']
                has_real_tissue_data = len(real_tissues) > 0
            
            if has_real_tissue_data or has_time_data:
                # Use a small delay to ensure UI is fully updated before generating plot
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, self._generate_plot)
            else:
                self.status_label.setText("No real tissue or time data detected. Generating plot with available data.")
                # Use a small delay to ensure UI is fully updated before generating plot
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, self._generate_plot)
            
        except Exception as e:
            logger.error(f"Failed to analyze data: {e}")
            self.status_label.setText(f"Error analyzing data: {str(e)}")
    
    def _populate_column_options(self, df: pd.DataFrame):
        """Populate the y-axis combo box with summary metric types only."""
        if self.y_axis_combo is None:
            return
        
        # Clear existing items
        self.y_axis_combo.clear()
        
        # Import the dynamic metric detection logic
        from flowproc.domain.visualization.column_utils import detect_available_metric_types
        
        # Get the available metric types from the actual data
        available_metrics = detect_available_metric_types(df)
        
        # Add the dynamically detected metric types
        for metric_type in available_metrics:
            self.y_axis_combo.addItem(metric_type)
        
        # Ensure we have a default selection for the Y-axis
        if available_metrics and self.y_axis_combo.count() > 0:
            self.y_axis_combo.setCurrentIndex(0)
            logger.info(f"Set default Y-axis selection to: {self.y_axis_combo.currentText()}")
        else:
            logger.warning("No available metrics found for Y-axis selection")
    
    def _populate_filter_options(self, df: pd.DataFrame):
        """Populate tissue and time filter options from parsed data."""
        if self.tissue_filter is None or self.time_filter is None:
            return
        
        # Clear existing items
        self.tissue_filter.clear()
        self.time_filter.clear()
        
        # Populate population filter
        self._populate_population_options(df)
        
        # Populate tissue filter with unique tissue values
        has_real_tissue_data = False
        entries, has_real_tissue_data = build_tissue_entries(df)
        for entry in entries:
            item = QListWidgetItem(entry['display'])
            item.setData(Qt.ItemDataRole.UserRole, entry['value'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if entry.get('checked', True) else Qt.CheckState.Unchecked)
            self.tissue_filter.addItem(item)
        
        # Hide tissue filter section if no real tissue data is available
        self.tissue_filter_label.setVisible(has_real_tissue_data)
        self.tissue_filter.setVisible(has_real_tissue_data)
        
        # Populate time filter with unique time values  
        has_time_data = False
        time_entries, has_time_data = build_time_entries(df)
        logger.info(f"Populating time filter with {len(time_entries)} time points")
        for entry in time_entries:
            item = QListWidgetItem(entry['display'])
            item.setData(Qt.ItemDataRole.UserRole, entry['value'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if entry.get('checked', True) else Qt.CheckState.Unchecked)
            self.time_filter.addItem(item)
        
        # Hide time filter section if no time data is available
        self.time_filter_label.setVisible(has_time_data)
        self.time_filter.setVisible(has_time_data)
        logger.info(f"Time filter visibility - has_time_data: {has_time_data}, visible: {has_time_data}")
    
    def _populate_population_options(self, df: pd.DataFrame):
        """Populate population filter with available populations from the data."""
        if self.population_filter is None:
            return
        
        # Clear existing items
        self.population_filter.clear()
        
        metric = None
        if self.y_axis_combo and self.y_axis_combo.currentText():
            metric = self.y_axis_combo.currentText()

        available_populations, population_mapping = detect_population_options(df, metric)
        
        # Add populations to dropdown
        if available_populations:
            # Sort populations for consistent ordering
            available_populations.sort()
            
            # Add "All Populations" option
            self.population_filter.addItem("All Populations")
            
            # Add individual populations using shortnames
            for shortname in available_populations:
                self.population_filter.addItem(shortname)
            
            # Set default selection to first population (not "All Populations")
            if len(available_populations) > 0:
                self.population_filter.setCurrentText(available_populations[0])
            
            # Store the mapping for later use in filtering
            self._population_mapping = population_mapping
            
            logger.info(f"Populated population filter with {len(available_populations)} populations using shortnames: {available_populations}")
            logger.debug(f"Population mapping: {population_mapping}")
            
            # Log a few examples of the mapping for verification
            if population_mapping:
                logger.info("Population filter shortname examples:")
                for i, (shortname, full_name) in enumerate(list(population_mapping.items())[:3]):
                    logger.info(f"  '{shortname}' -> '{full_name}'")
        else:
            # No populations found, add a default option
            self.population_filter.addItem("No Populations Available")
            logger.warning("No populations detected in the data")
    
    # Population name helpers now live in visualization_filters module
    
    def _on_option_changed(self):
        """Handle option changes."""
        # If y-axis changed and we're in timecourse mode, repopulate population options
        if (self.time_course_checkbox and self.time_course_checkbox.isChecked() and 
            self.csv_path and self.csv_path.exists()):
            try:
                from flowproc.domain.parsing import load_and_parse_df
                df, _ = load_and_parse_df(self.csv_path)
                if df is not None and not df.empty:
                    self._populate_population_options(df)
            except Exception as e:
                logger.warning(f"Failed to repopulate population options: {e}")
        
        self._generate_plot()
    
    def _on_filter_changed(self):
        """Handle filter changes."""
        # Debug: Log current filter state
        options = self.get_current_options()
        logger.info(f"Filter changed - selected tissues: {options.selected_tissues}, selected times: {options.selected_times}")
        logger.info("Filter changed - regenerating plot")
        self._generate_plot()
    
    def _on_time_course_toggled(self, checked: bool):
        """Handle time course mode toggle."""
        # Update plot type combo based on time course mode
        if checked:
            self.plot_type_combo.setCurrentText("line")
            self.plot_type_combo.setEnabled(False)  # Disable plot type selection for time course
            
            # Show population filter for timecourse mode
            if self.population_filter_label and self.population_filter:
                self.population_filter_label.setVisible(True)
                self.population_filter.setVisible(True)
                
                # Repopulate population options if we have data
                if self.csv_path and self.csv_path.exists():
                    try:
                        from flowproc.domain.parsing import load_and_parse_df
                        df, _ = load_and_parse_df(self.csv_path)
                        if df is not None and not df.empty:
                            self._populate_population_options(df)
                    except Exception as e:
                        logger.warning(f"Failed to repopulate population options: {e}")
        else:
            self.plot_type_combo.setEnabled(True)
            
            # Hide population filter when not in timecourse mode
            if self.population_filter_label and self.population_filter:
                self.population_filter_label.setVisible(False)
                self.population_filter.setVisible(False)
        
        self._generate_plot()
    
    def get_current_options(self) -> VisualizationOptions:
        """Get current visualization options including filters."""
        # Get selected tissues
        selected_tissues = []
        if self.tissue_filter and self.tissue_filter.isVisible():
            for i in range(self.tissue_filter.count()):
                item = self.tissue_filter.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    tissue_code = item.data(Qt.ItemDataRole.UserRole)
                    selected_tissues.append(tissue_code)
        else:
            # If tissue filter is not visible, it means no real tissue data was detected
            # In this case, we want to show all data (no tissue filtering)
            # Set selected_tissues to None to indicate "show all" rather than empty list
            selected_tissues = None
        
        # Get selected times
        selected_times = []
        if self.time_filter and self.time_filter.isVisible():
            for i in range(self.time_filter.count()):
                item = self.time_filter.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    time_value = item.data(Qt.ItemDataRole.UserRole)
                    selected_times.append(time_value)
        else:
            # If time filter is not visible, it means no time data was detected
            # In this case, we want to show all data (no time filtering)
            # Set selected_times to None to indicate "show all" rather than empty list
            selected_times = None
        
        # Debug logging for filter selection
        logger.info(f"Filter selection - tissue_filter visible: {self.tissue_filter and self.tissue_filter.isVisible()}, count: {self.tissue_filter.count() if self.tissue_filter else 0}")
        logger.info(f"Filter selection - time_filter visible: {self.time_filter and self.time_filter.isVisible()}, count: {self.time_filter.count() if self.time_filter else 0}")
        logger.info(f"Filter selection - selected tissues: {selected_tissues}, selected times: {selected_times}")
        
        # Get selected population (only relevant in timecourse mode)
        selected_population = None
        if (self.population_filter and self.population_filter.isVisible() and 
            self.population_filter.currentText() and 
            self.population_filter.currentText() != "All Populations" and
            self.population_filter.currentText() != "No Populations Available"):
            # Get the shortname from the dropdown
            shortname = self.population_filter.currentText()
            
            # Use the mapping to get the full column name for filtering
            if hasattr(self, '_population_mapping') and shortname in self._population_mapping:
                selected_population = self._population_mapping[shortname]
                logger.debug(f"Population filter: shortname '{shortname}' maps to column '{selected_population}'")
            else:
                # Fallback to using the shortname directly if no mapping available
                selected_population = shortname
                logger.warning(f"No population mapping found for '{shortname}', using shortname directly")
        
        logger.info(f"Filter selection - selected population: {selected_population}")
        
        # Additional debugging for widget states
        if self.tissue_filter and self.tissue_filter.isVisible():
            logger.debug("Tissue filter items and states:")
            for i in range(self.tissue_filter.count()):
                item = self.tissue_filter.item(i)
                logger.debug(f"  Item {i}: '{item.text()}' - checked: {item.checkState() == Qt.CheckState.Checked}")
        
        if self.time_filter and self.time_filter.isVisible():
            logger.debug("Time filter items and states:")
            for i in range(self.time_filter.count()):
                item = self.time_filter.item(i)
                logger.debug(f"  Item {i}: '{item.text()}' - checked: {item.checkState() == Qt.CheckState.Checked}")
        
        if self.population_filter and self.population_filter.isVisible():
            logger.debug(f"Population filter current text: '{self.population_filter.currentText()}'")
        
        return VisualizationOptions(
            plot_type=self.plot_type_combo.currentText() if self.plot_type_combo else "bar",
            y_axis=self.y_axis_combo.currentText() if self.y_axis_combo else None,
            time_course_mode=self.time_course_checkbox.isChecked() if self.time_course_checkbox else False,
            selected_tissues=selected_tissues,
            selected_times=selected_times,
            selected_population=selected_population
        )
    
    def _ensure_filter_synchronization(self):
        """Ensure all filter options are properly synchronized before generating plots."""
        logger.info("Ensuring filter synchronization...")
        
        # Check tissue filter synchronization
        if self.tissue_filter and self.tissue_filter.isVisible():
            logger.debug("Tissue filter synchronization check:")
            for i in range(self.tissue_filter.count()):
                item = self.tissue_filter.item(i)
                logger.debug(f"  Item {i}: '{item.text()}' - checked: {item.checkState() == Qt.CheckState.Checked}")
        
        # Check time filter synchronization
        if self.time_filter and self.time_filter.isVisible():
            logger.debug("Time filter synchronization check:")
            for i in range(self.time_filter.count()):
                item = self.time_filter.item(i)
                logger.debug(f"  Item {i}: '{item.text()}' - checked: {item.checkState() == Qt.CheckState.Checked}")
        
        # Check population filter synchronization
        if self.population_filter and self.population_filter.isVisible():
            logger.debug(f"Population filter synchronization check: '{self.population_filter.currentText()}'")
        
        # Check Y-axis synchronization
        if self.y_axis_combo and self.y_axis_combo.count() > 0:
            logger.debug(f"Y-axis synchronization check: '{self.y_axis_combo.currentText()}'")
        
        logger.info("Filter synchronization check completed")

    def _generate_plot(self):
        """Generate the plot using the coordinator's unified method."""
        try:
            if not self.csv_path:
                self.status_label.setText("Error: No data available")
                return
            
            # Ensure all filter options are properly synchronized before generating the plot
            self._ensure_filter_synchronization()
            
            # Get current options including filters
            options = self.get_current_options()
            
            # Debug logging for filter options
            logger.info(f"Current options - tissues: {options.selected_tissues}, times: {options.selected_times}, time_course: {options.time_course_mode}")
            
            # Validate that we have the necessary options for plotting
            if not options.y_axis:
                logger.warning("No Y-axis metric selected, this may cause plot generation issues")
            
            # Log filter validation
            if options.selected_tissues is None:
                logger.info("No tissue filtering applied (showing all tissues)")
            elif len(options.selected_tissues) == 0:
                logger.warning("No tissues selected for filtering - this may result in empty plots")
            
            if options.selected_times is None:
                logger.info("No time filtering applied (showing all time points)")
            elif len(options.selected_times) == 0:
                logger.warning("No time points selected for filtering - this may result in empty plots")
            
            if options.time_course_mode and not options.selected_population:
                logger.info("Time course mode: no specific population selected (showing all populations)")
            
            # Create temporary HTML file
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                self.temp_html_file = Path(tmp_file.name)
            
            self.status_label.setText("Generating plot...")
            
            # Use the coordinator's unified visualization method
            from flowproc.presentation.gui.views.components.processing_coordinator import ProcessingCoordinator
            
            # Load data and apply filters using coordinator's static method
            from flowproc.domain.parsing import load_and_parse_df
            df, _ = load_and_parse_df(self.csv_path)
            
            if df is None or df.empty:
                self._show_error_message("No data found in CSV file")
                return
            
            # Debug logging for data structure
            logger.info(f"Data loaded - rows: {len(df)}, columns: {list(df.columns)}")
            if 'Tissue' in df.columns:
                logger.info(f"Tissue data - unique values: {df['Tissue'].dropna().unique()}")
            if 'Time' in df.columns:
                logger.info(f"Time data - unique values: {df['Time'].dropna().unique()}")
            
            # Apply filters using coordinator's static method
            filtered_df = ProcessingCoordinator.apply_filters(df, options)
            
            # Additional debugging for filtered data
            logger.info(f"Filtered data - rows: {len(filtered_df)}, columns: {list(filtered_df.columns)}")
            logger.info("Filtered data sample:")
            logger.info(f"  First few rows: {filtered_df.head(3).to_dict('records')}")
            
            # Check for time-related columns
            time_cols = [col for col in filtered_df.columns if any(keyword in col.lower() for keyword in ['time', 'day', 'hour', 'week', 'minute'])]
            logger.info(f"Time-related columns found: {time_cols}")
            
            # Check for value columns (numeric columns that might be metrics)
            numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
            logger.info(f"Numeric columns (potential metrics): {numeric_cols}")
            
            # Check for group columns
            group_cols = [col for col in filtered_df.columns if any(keyword in col.lower() for keyword in ['group', 'treatment', 'condition', 'sample'])]
            logger.info(f"Group-related columns found: {group_cols}")
            
            # Provide detailed feedback about filtering
            filter_message = f"Filtered data: {len(filtered_df)} of {len(df)} rows"
            if options.selected_tissues is not None:
                filter_message += f" (tissues: {', '.join(options.selected_tissues)})"
            if options.selected_times is not None:
                filter_message += f" (times: {', '.join(map(str, options.selected_times))})"
            logger.info(filter_message)
            
            if filtered_df.empty:
                # Check if no filters are selected
                # None means "show all" (filter is hidden), empty list means "no selection" (filter is visible but nothing checked)
                has_tissue_filter = options.selected_tissues is not None and len(options.selected_tissues) > 0
                has_time_filter = options.selected_times is not None and len(options.selected_times) > 0
                has_time_data = 'Time' in df.columns and len(df['Time'].dropna().unique()) > 0
                has_tissue_data = 'Tissue' in df.columns and not df['Tissue'].isna().all()
                
                # Check if we have real tissue data (not just UNK)
                has_real_tissue_data = False
                if has_tissue_data:
                    unique_tissues = df['Tissue'].dropna().unique()
                    real_tissues = [t for t in unique_tissues if t != 'UNK']
                    has_real_tissue_data = len(real_tissues) > 0
                
                # Note: visibility flags are not used below; skip assignments to avoid linter warnings
                
                if not has_tissue_filter and not has_time_filter and (has_time_data or has_real_tissue_data):
                    error_msg = "No filters selected. Please select at least one tissue or time filter to display data."
                    if has_real_tissue_data:
                        available_tissues = [t for t in df['Tissue'].dropna().unique() if t != 'UNK']
                        error_msg += f"\n\nAvailable tissues: {', '.join(available_tissues)}"
                    if has_time_data:
                        available_times = df['Time'].dropna().unique()
                        error_msg += f"\nAvailable times: {', '.join(map(str, available_times))}"
                elif not has_tissue_filter and not has_time_data and not has_real_tissue_data:
                    error_msg = "No real tissue data detected and no time data available. Please check your data."
                    if has_tissue_data:
                        available_tissues = df['Tissue'].dropna().unique()
                        error_msg += f"\n\nDetected tissue codes: {', '.join(available_tissues)}"
                elif not has_tissue_filter and not has_time_data:
                    error_msg = "No tissue filter selected. Please select at least one tissue to display data."
                    if has_real_tissue_data:
                        available_tissues = [t for t in df['Tissue'].dropna().unique() if t != 'UNK']
                        error_msg += f"\n\nAvailable tissues: {', '.join(available_tissues)}"
                elif has_time_filter and has_time_data and not has_tissue_filter:
                    # Time filter is selected but no tissue filter - this might be the issue
                    error_msg = "Time filter selected but no tissue filter selected. Please select at least one tissue to display data."
                    if has_real_tissue_data:
                        available_tissues = [t for t in df['Tissue'].dropna().unique() if t != 'UNK']
                        error_msg += f"\n\nAvailable tissues: {', '.join(available_tissues)}"
                    if has_time_data:
                        available_times = df['Time'].dropna().unique()
                        error_msg += f"\nAvailable times: {', '.join(map(str, available_times))}"
                else:
                    error_msg = "No data matches the current filter selection."
                    if options.selected_tissues is not None:
                        available_tissues = df['Tissue'].dropna().unique() if 'Tissue' in df.columns else []
                        error_msg += f"\nAvailable tissues: {', '.join(available_tissues)}"
                    if options.selected_times is not None:
                        available_times = df['Time'].dropna().unique() if 'Time' in df.columns else []
                        error_msg += f"\nAvailable times: {', '.join(map(str, available_times))}"
                    error_msg += "\nPlease adjust your filters."
                self._show_error_message(error_msg)
                return
            
            # Generate plot with filtered data
            from flowproc.domain.visualization.flow_cytometry_visualizer import plot
            from flowproc.domain.visualization.time_plots import create_timecourse_visualization
            
            # Reset current figure before generation
            self.current_fig = None

            if options.time_course_mode:
                # Create filter options including population filter
                # Pass the options object directly since create_comprehensive_plot_title expects an object with attributes
                filter_options = options
                # Add population filter as a separate parameter since it's not part of the options object structure
                population_filter = options.selected_population
                
                # Debug: Log filter options being passed
                logger.info(f"Timecourse mode - filter_options: {filter_options}")
                logger.info(f"Timecourse mode - selected_tissues: {filter_options.selected_tissues}")
                logger.info(f"Timecourse mode - selected_times: {filter_options.selected_times}")
                logger.info(f"Timecourse mode - population_filter: {population_filter}")
                
                # Additional debugging for attribute access
                logger.info(f"Timecourse mode - filter_options type: {type(filter_options)}")
                logger.info(f"Timecourse mode - hasattr selected_population: {hasattr(filter_options, 'selected_population')}")
                logger.info(f"Timecourse mode - hasattr selected_tissues: {hasattr(filter_options, 'selected_tissues')}")
                logger.info(f"Timecourse mode - hasattr selected_times: {hasattr(filter_options, 'selected_times')}")
                
                # Try to access attributes directly to see if there are any issues
                try:
                    logger.info(f"Timecourse mode - direct access selected_population: {getattr(filter_options, 'selected_population', 'NOT_FOUND')}")
                    logger.info(f"Timecourse mode - direct access selected_tissues: {getattr(filter_options, 'selected_tissues', 'NOT_FOUND')}")
                    logger.info(f"Timecourse mode - direct access selected_times: {getattr(filter_options, 'selected_times', 'NOT_FOUND')}")
                except Exception as e:
                    logger.error(f"Timecourse mode - Error accessing filter options attributes: {e}")
                
                # Detect the actual time column from the data
                time_column = detect_time_column(filtered_df)
                if time_column not in filtered_df.columns:
                    logger.warning(f"Detected time column '{time_column}' not present in filtered data columns.")
                
                logger.info(f"Using time column: {time_column}")
                
                fig = create_timecourse_visualization(
                    data=filtered_df,
                    time_column=time_column,  # Use detected time column
                    metric=options.y_axis,
                    population_filter=population_filter,  # Pass population filter
                    filter_options=filter_options,  # Pass all filter options
                    width=options.width,
                    height=options.height,
                    save_html=self.temp_html_file
                )
            else:
                # Debug: Log filter options being passed for non-timecourse mode
                logger.info(f"Standard mode - filter_options: {options}")
                logger.info(f"Standard mode - selected_tissues: {options.selected_tissues}")
                logger.info(f"Standard mode - selected_times: {options.selected_times}")
                
                # Additional debugging for attribute access in standard mode
                logger.info(f"Standard mode - filter_options type: {type(options)}")
                logger.info(f"Standard mode - hasattr selected_population: {hasattr(options, 'selected_population')}")
                logger.info(f"Standard mode - hasattr selected_tissues: {hasattr(options, 'selected_tissues')}")
                logger.info(f"Standard mode - hasattr selected_times: {hasattr(options, 'selected_times')}")
                
                # Try to access attributes directly to see if there are any issues
                try:
                    logger.info(f"Standard mode - direct access selected_population: {getattr(options, 'selected_population', 'NOT_FOUND')}")
                    logger.info(f"Standard mode - direct access selected_tissues: {getattr(options, 'selected_tissues', 'NOT_FOUND')}")
                    logger.info(f"Standard mode - direct access selected_times: {getattr(options, 'selected_times', 'NOT_FOUND')}")
                except Exception as e:
                    logger.error(f"Standard mode - Error accessing filter options attributes: {e}")
                
                fig = plot(
                    data=filtered_df,
                    x='Group',
                    y=options.y_axis,
                    plot_type=options.plot_type,
                    filter_options=options,  # Pass filter options for title generation
                    # Pass user group labels only if explicitly set by user via state
                    user_group_labels=getattr(self.parent(), 'current_group_labels', []) or None,
                    fixed_layout=True,
                    width=options.width,
                    height=options.height,
                    save_html=self.temp_html_file
                )
            
            result_path = self.temp_html_file
            # Store figure for export
            self.current_fig = fig
            
            # Debug: Check the figure title
            if fig and hasattr(fig, 'layout') and hasattr(fig.layout, 'title'):
                if hasattr(fig.layout.title, 'text'):
                    logger.info(f"Figure title: {fig.layout.title.text}")
                else:
                    logger.info("Figure has title but no text attribute")
            else:
                logger.info("Figure has no title or layout")
            
            if fig and result_path:
                # Debug: Check the generated HTML content
                if self.temp_html_file.exists():
                    try:
                        with open(self.temp_html_file, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                            logger.info(f"Generated HTML file size: {len(html_content)} characters")
                            if 'title' in html_content.lower():
                                title_start = html_content.find('<title>')
                                title_end = html_content.find('</title>')
                                if title_start != -1 and title_end != -1:
                                    title_text = html_content[title_start + 7:title_end]
                                    logger.info(f"HTML title found: {title_text}")
                                else:
                                    logger.info("No HTML title tags found")
                            else:
                                logger.info("No title content found in HTML")
                    except Exception as e:
                        logger.warning(f"Failed to read HTML content for debugging: {e}")
                
                # Load in web view if available (skip during tests where web_view may be absent)
                from PySide6.QtCore import QUrl
                file_url = QUrl.fromLocalFile(str(self.temp_html_file))
                logger.info(f"Loading web view with URL: {file_url}")
                if self.web_view is not None and hasattr(self.web_view, 'load'):
                    self.web_view.load(file_url)
                
                # Update status with filter information
                status_text = f"Plot generated successfully - {len(filtered_df)} of {len(df)} rows displayed"
                
                # Check if we have real tissue data
                has_real_tissue_data = False
                if 'Tissue' in df.columns:
                    unique_tissues = df['Tissue'].dropna().unique()
                    real_tissues = [t for t in unique_tissues if t != 'UNK']
                    has_real_tissue_data = len(real_tissues) > 0
                
                if options.selected_tissues is not None and len(options.selected_tissues) < len(df['Tissue'].dropna().unique()):
                    status_text += " (filtered by tissue)"
                elif not has_real_tissue_data and 'Tissue' in df.columns:
                    status_text += " (auto-filtered UNK tissues)"
                
                if options.selected_times is not None and len(options.selected_times) < len(df['Time'].dropna().unique()):
                    status_text += " (filtered by time)"
                
                self.status_label.setText(status_text)
                self.plot_generated.emit()
            else:
                self._show_error_message("Failed to generate plot. Please check your data and filters.")
            
        except Exception as e:
            logger.error(f"Failed to generate plot: {e}")
            self._show_error_message(f"Failed to generate plot: {str(e)}")
    
    def _save_visualization(self):
        """Save the current visualization to a user-selected location as PDF (non-blocking)."""
        if not self.current_fig:
            QMessageBox.warning(self, "No Plot", "Please generate a plot first.")
            return

        # Generate standard filename using naming utils
        from flowproc.domain.visualization.naming_utils import NamingUtils
        
        # Detect plot type from current figure
        plot_type = 'scatter'  # Default
        if self.current_fig and hasattr(self.current_fig, 'data') and self.current_fig.data:
            # Try to detect plot type from the first trace
            first_trace = self.current_fig.data[0]
            if hasattr(first_trace, 'type'):
                trace_type = first_trace.type
                # Map trace types to plot types
                type_mapping = {
                    'scatter': 'scatter',
                    'bar': 'bar',
                    'box': 'box',
                    'violin': 'violin',
                    'histogram': 'histogram',
                    'area': 'area'
                }
                plot_type = type_mapping.get(trace_type, 'scatter')
        
        # Create a mock plot config based on current figure
        plot_config = {
            'type': plot_type,
            'format': 'pdf'
        }
        
        # Use current data if available, otherwise load from CSV
        if hasattr(self, 'current_data') and self.current_data is not None:
            data = self.current_data
        elif self.csv_path and self.csv_path.exists():
            # Load data from CSV for naming purposes
            from flowproc.domain.parsing import load_and_parse_df
            data, _ = load_and_parse_df(self.csv_path)
        else:
            # Create minimal data for naming purposes
            import pandas as pd
            data = pd.DataFrame({
                'Group': [1],
                'Freq. of Parent': [10]
            })
        
        # Generate standard filename
        standard_filename = NamingUtils.generate_plot_filename(
            plot_config=plot_config,
            data=data,
            source_file=self.csv_path,
            plot_index=1
        )
        
        # Use standard filename as default
        default_name = (
            str(self.csv_path.parent / standard_filename)
            if self.csv_path else standard_filename
        )

        # Create a custom file dialog to ensure proper parent-child relationship
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("PDF Files (*.pdf)")
        file_dialog.setDefaultSuffix("pdf")
        file_dialog.setDirectory(str(self.csv_path.parent) if self.csv_path else "")
        file_dialog.selectFile(default_name)
        
        # Ensure the visualization dialog stays on top
        self.raise_()
        self.activateWindow()
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_path = file_dialog.selectedFiles()[0]
        else:
            return

        if not file_path:
            return

        # Ensure .pdf extension
        if not str(file_path).lower().endswith('.pdf'):
            file_path = str(file_path) + '.pdf'

        # Prepare export parameters
        width = getattr(getattr(self.current_fig, 'layout', None), 'width', None)
        height = getattr(getattr(self.current_fig, 'layout', None), 'height', None)

        logger.info(f"Starting PDF export to: {file_path} (width={width}, height={height})")
        
        # Update UI to show export is in progress
        self.status_label.setText("PDF export in progress...")
        self.cancel_pdf_button.setEnabled(True)

        # Run export in background thread to avoid interfering with Qt event loop
        class _PdfExportThread(QThread):
            success = Signal(str)
            error = Signal(str)

            def __init__(self, fig, out_path: str, width: int | None, height: int | None) -> None:
                super().__init__()
                self._fig = fig
                self._out_path = out_path
                self._width = width
                self._height = height

            def run(self) -> None:
                try:
                    from flowproc.domain.visualization.plotly_renderer import PlotlyRenderer
                    renderer = PlotlyRenderer()
                    
                    # Use Selenium-based export method for reliable image generation
                    if self._width is not None and self._height is not None:
                        renderer.export_to_pdf(self._fig, self._out_path, width=self._width, height=self._height, scale=1)
                    else:
                        renderer.export_to_pdf(self._fig, self._out_path)
                    
                    self.success.emit(self._out_path)
                except Exception as e:  # noqa: BLE001
                    self.error.emit(str(e))
            
            def stop(self):
                """Safely stop the thread."""
                if self.isRunning():
                    self.quit()
                    self.wait(2000)
                    if self.isRunning():
                        self.terminate()
                        self.wait(1000)

        self._export_thread = _PdfExportThread(self.current_fig, file_path, width, height)

        @Slot(str)
        def _on_success(path: str) -> None:
            logger.info(f"PDF export completed: {path}")
            # Reset UI state
            self.status_label.setText("PDF export completed successfully")
            self.cancel_pdf_button.setEnabled(False)
            QMessageBox.information(self, "Success", f"Visualization saved to {path}")

        @Slot(str)
        def _on_error(msg: str) -> None:
            logger.error(f"Failed to save PDF: {msg}")
            # Reset UI state
            self.status_label.setText("PDF export failed")
            self.cancel_pdf_button.setEnabled(False)
            QMessageBox.critical(self, "Error", f"Failed to save PDF: {msg}")

        self._export_thread.success.connect(_on_success)
        self._export_thread.error.connect(_on_error)
        self._export_thread.finished.connect(self._on_pdf_export_finished)
        self._export_thread.start()
        
        # Store the success and error handlers to prevent them from being garbage collected
        self._success_handler = _on_success
        self._error_handler = _on_error
    
    def _show_error_message(self, message: str):
        """Show an error message in the web view."""
        error_html = f"""
        <html>
        <body style="background-color: #0F0F0F; color: #F0F0F0; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
            <div style="text-align: center;">
                <h3 style="color: #ff6b6b;">Visualization Error</h3>
                <p>{message}</p>
                <p>Please check your data and try again.</p>
            </div>
        </body>
        </html>
        """
        # In test mode, web_view may be unavailable; guard the call
        if self.web_view is not None and hasattr(self.web_view, 'setHtml'):
            self.web_view.setHtml(error_html)
        self.status_label.setText("Error generating plot")
    
    def closeEvent(self, event):
        """Handle close event and cleanup temporary files and threads."""
        # Check if PDF export is running and ask user if they want to cancel it
        if self.is_pdf_export_running():
            reply = QMessageBox.question(
                self,
                "PDF Export in Progress",
                "A PDF export is currently running. Do you want to cancel it and close the dialog?\n\n"
                "Note: Cancelling may result in an incomplete PDF file.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # User chose to cancel - stop the export first
                self.stop_pdf_export()
                # Wait a bit for the thread to finish
                if self._export_thread is not None:
                    self._export_thread.wait(1000)
            else:
                event.ignore()
                return
        
        try:
            # Clean up any running PDF export thread
            if self._export_thread is not None:
                if self._export_thread.isRunning():
                    logger.info("Terminating PDF export thread before closing dialog")
                    # Disconnect signals first to prevent callbacks after thread termination
                    self._export_thread.success.disconnect()
                    self._export_thread.error.disconnect()
                    # Use the thread's own stop method for safer termination
                    self._export_thread.stop()
                self._export_thread.deleteLater()
                self._export_thread = None
            
            # Clean up temporary HTML file
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup during dialog close: {e}")
        
        super().closeEvent(event)
    
    def hideEvent(self, event):
        """Handle hide event to ensure thread safety."""
        super().hideEvent(event)
        # Don't stop the thread when hiding, just ensure it's properly managed
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        # Check if any thread is still running and clean up if needed
        if self._export_thread is not None and not self._export_thread.isRunning():
            self._export_thread.deleteLater()
            self._export_thread = None
    
    def is_pdf_export_running(self) -> bool:
        """Check if PDF export is currently running."""
        return self._export_thread is not None and self._export_thread.isRunning()
    
    def can_close_safely(self) -> bool:
        """Check if the dialog can be closed safely without interrupting operations."""
        return not self.is_pdf_export_running()
    
    @Slot()
    def _on_pdf_export_finished(self):
        """Handle PDF export thread completion (success, error, or cancellation)."""
        # Ensure UI state is consistent regardless of how the thread finished
        if self._export_thread is not None:
            self._export_thread.deleteLater()
            self._export_thread = None
        
        # Reset UI state if not already done by success/error handlers
        if self.cancel_pdf_button.isEnabled():
            self.cancel_pdf_button.setEnabled(False)
            if "completed" not in self.status_label.text() and "failed" not in self.status_label.text():
                self.status_label.setText("Ready")
    
    def stop_pdf_export(self):
        """Safely stop any ongoing PDF export."""
        if self._export_thread is not None and self._export_thread.isRunning():
            logger.info("Stopping PDF export on user request")
            try:
                # Disconnect signals first
                self._export_thread.success.disconnect()
                self._export_thread.error.disconnect()
                # Use the thread's own stop method for safer termination
                self._export_thread.stop()
                self._export_thread.deleteLater()
                self._export_thread = None
                # Reset UI state
                self.status_label.setText("PDF export cancelled")
                self.cancel_pdf_button.setEnabled(False)
                logger.info("PDF export stopped successfully")
            except Exception as e:
                logger.warning(f"Failed to stop PDF export: {e}")
                # Reset UI state even on error
                self.status_label.setText("PDF export error")
                self.cancel_pdf_button.setEnabled(False)
    
    def __del__(self):
        """Destructor to ensure thread cleanup."""
        try:
            if self._export_thread is not None:
                if self._export_thread.isRunning():
                    logger.info("Terminating PDF export thread in destructor")
                    # Disconnect signals first to prevent callbacks after thread termination
                    try:
                        self._export_thread.success.disconnect()
                        self._export_thread.error.disconnect()
                    except Exception:
                        pass  # Signals may already be disconnected
                    # Use the thread's own stop method for safer termination
                    self._export_thread.stop()
                self._export_thread.deleteLater()
        except Exception as e:
            logger.warning(f"Failed to cleanup thread in destructor: {e}")