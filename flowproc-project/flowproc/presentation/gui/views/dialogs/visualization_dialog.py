"""
Single Visualization Dialog

This module provides a unified visualization interface that goes directly from
button click to final visualization display without intermediate dialogs.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QComboBox, QCheckBox, QPushButton, QMessageBox,
    QWidget, QSplitter, QSizePolicy, QApplication,
    QFileDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
import pandas as pd

from flowproc.domain.parsing import load_and_parse_df
# Import moved to where it's used to avoid circular imports

logger = logging.getLogger(__name__)


@dataclass
class VisualizationOptions:
    """Container for visualization options."""
    plot_type: str = "bar"
    y_axis: Optional[str] = None
    time_course_mode: bool = False
    theme: str = "plotly"
    width: int = 800
    height: int = 600
    show_individual_points: bool = False
    error_bars: bool = True
    interactive: bool = True
    # Filter options
    selected_tissues: Optional[list] = None
    selected_times: Optional[list] = None


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
        
        # UI Components
        self.plot_type_combo: Optional[QComboBox] = None
        self.y_axis_combo: Optional[QComboBox] = None
        self.time_course_checkbox: Optional[QCheckBox] = None
        self.tissue_filter: Optional[QListWidget] = None
        self.time_filter: Optional[QListWidget] = None
        self.web_view: Optional[QWebEngineView] = None
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
        
        # Settings panel at the top
        settings_widget = self._create_settings_panel()
        main_layout.addWidget(settings_widget)
        
        # Create splitter for plot display
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Plot display (takes full width now)
        plot_widget = self._create_plot_panel()
        splitter.addWidget(plot_widget)
        
        # Status bar at bottom
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #191919; border-top: 1px solid #303030; color: #F0F0F0;")
        main_layout.addWidget(self.status_label)
    
    def _create_settings_panel(self):
        """Create the settings configuration panel at the top."""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(15)
        
        # Basic Options Group
        basic_group = QGroupBox("Visualization Settings")
        basic_layout = QVBoxLayout(basic_group)
        
        # Single row: Plot type, Y-axis, Mode, Tissue filter, Time filter, and Action buttons
        main_row = QHBoxLayout()
        
        # Plot type selection
        plot_type_layout = QVBoxLayout()
        plot_type_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["bar", "box", "scatter", "line"])
        self.plot_type_combo.currentTextChanged.connect(self._on_option_changed)
        plot_type_layout.addWidget(self.plot_type_combo)
        main_row.addLayout(plot_type_layout)
        
        # Y-axis selection
        y_axis_layout = QVBoxLayout()
        y_axis_layout.addWidget(QLabel("Y-Axis:"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.currentTextChanged.connect(self._on_option_changed)
        y_axis_layout.addWidget(self.y_axis_combo)
        main_row.addLayout(y_axis_layout)
        
        # Time course mode
        time_course_layout = QVBoxLayout()
        time_course_layout.addWidget(QLabel("Mode:"))
        self.time_course_checkbox = QCheckBox("Time Course Mode")
        self.time_course_checkbox.toggled.connect(self._on_time_course_toggled)
        time_course_layout.addWidget(self.time_course_checkbox)
        main_row.addLayout(time_course_layout)
        
        # Tissue filter
        tissue_filter_layout = QVBoxLayout()
        tissue_filter_layout.addWidget(QLabel("Tissue Filter:"))
        self.tissue_filter = QListWidget()
        self.tissue_filter.setMaximumHeight(80)
        # Use NoSelection mode to rely on checkboxes instead of selection highlighting
        self.tissue_filter.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.tissue_filter.itemChanged.connect(self._on_filter_changed)
        tissue_filter_layout.addWidget(self.tissue_filter)
        main_row.addLayout(tissue_filter_layout)
        
        # Time filter
        self.time_filter_layout = QVBoxLayout()
        self.time_filter_label = QLabel("Time Filter:")
        self.time_filter_layout.addWidget(self.time_filter_label)
        self.time_filter = QListWidget()
        self.time_filter.setMaximumHeight(80)
        # Use NoSelection mode to rely on checkboxes instead of selection highlighting
        self.time_filter.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.time_filter.itemChanged.connect(self._on_filter_changed)
        self.time_filter_layout.addWidget(self.time_filter)
        main_row.addLayout(self.time_filter_layout)
        
        # Action Buttons - stacked vertically to the right of filters
        button_layout = QVBoxLayout()
        button_layout.addStretch()  # Push buttons to the top
        
        generate_button = QPushButton("Generate Plot")
        generate_button.setMinimumHeight(40)
        generate_button.clicked.connect(self._generate_plot)
        button_layout.addWidget(generate_button)
        
        save_button = QPushButton("Save Plot")
        save_button.setMinimumHeight(40)
        save_button.clicked.connect(self._save_visualization)
        button_layout.addWidget(save_button)
        
        button_layout.addStretch()  # Add spacing at bottom
        main_row.addLayout(button_layout)
        
        basic_layout.addLayout(main_row)
        settings_layout.addWidget(basic_group)
        
        return settings_widget
    
    def _create_plot_panel(self):
        """Create the plot display panel."""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(10, 10, 10, 10)
        
        # Plot title
        plot_title = QLabel("Flow Cytometry Visualization")
        plot_title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: #0064FF;")
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plot_layout.addWidget(plot_title)
        
        # Web view for plot display
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        plot_layout.addWidget(self.web_view)
        
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
            
            # Auto-generate initial plot if filters are available
            if 'Tissue' in df.columns or ('Time' in df.columns and len(df['Time'].dropna().unique()) > 0):
                self._generate_plot()
            else:
                self.status_label.setText("Please select tissue and/or time filters to display data.")
            
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
    
    def _populate_filter_options(self, df: pd.DataFrame):
        """Populate tissue and time filter options from parsed data."""
        if self.tissue_filter is None or self.time_filter is None:
            return
        
        # Clear existing items
        self.tissue_filter.clear()
        self.time_filter.clear()
        
        # Populate tissue filter with unique tissue values
        if 'Tissue' in df.columns:
            unique_tissues = df['Tissue'].dropna().unique()
            # Use tissue parser to get full names
            from flowproc.domain.parsing.tissue_parser import TissueParser
            tissue_parser = TissueParser()
            
            for tissue_code in sorted(unique_tissues):
                # Get count for this tissue
                tissue_count = len(df[df['Tissue'] == tissue_code])
                
                if tissue_code == 'UNK':
                    # Include UNK but mark it clearly
                    display_text = f"UNK (Unknown) [{tissue_count} samples]"
                else:
                    full_name = tissue_parser.get_full_name(tissue_code)
                    display_text = f"{tissue_code} ({full_name}) [{tissue_count} samples]"
                    
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, tissue_code)  # Store the tissue code
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  # Enable checkbox
                item.setCheckState(Qt.CheckState.Checked)  # Auto-select all tissues by default
                self.tissue_filter.addItem(item)
        
        # Populate time filter with unique time values  
        has_time_data = False
        if 'Time' in df.columns:
            unique_times = df['Time'].dropna().unique()
            if len(unique_times) > 0:
                has_time_data = True
                # Use time parser to format time values
                from flowproc.domain.parsing.time_service import TimeService
                time_service = TimeService()
                
                for time_hours in sorted(unique_times):
                    if pd.notna(time_hours):
                        # Get count for this time point
                        time_count = len(df[df['Time'] == time_hours])
                        
                        formatted_time = time_service.format(time_hours, format_style='auto')
                        display_text = f"{formatted_time} ({time_hours}h) [{time_count} samples]"
                        
                        item = QListWidgetItem(display_text)
                        item.setData(Qt.ItemDataRole.UserRole, time_hours)  # Store the time value
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  # Enable checkbox
                        item.setCheckState(Qt.CheckState.Checked)  # Auto-select all time points by default
                        self.time_filter.addItem(item)
        
        # Hide time filter section if no time data is available
        self.time_filter_label.setVisible(has_time_data)
        self.time_filter.setVisible(has_time_data)
    
    def _on_option_changed(self):
        """Handle option changes."""
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
        else:
            self.plot_type_combo.setEnabled(True)
        
        self._generate_plot()
    
    def get_current_options(self) -> VisualizationOptions:
        """Get current visualization options including filters."""
        # Get selected tissues
        selected_tissues = []
        if self.tissue_filter:
            for i in range(self.tissue_filter.count()):
                item = self.tissue_filter.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    tissue_code = item.data(Qt.ItemDataRole.UserRole)
                    selected_tissues.append(tissue_code)
        
        # Get selected times
        selected_times = []
        if self.time_filter:
            for i in range(self.time_filter.count()):
                item = self.time_filter.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    time_value = item.data(Qt.ItemDataRole.UserRole)
                    selected_times.append(time_value)
        
        return VisualizationOptions(
            plot_type=self.plot_type_combo.currentText() if self.plot_type_combo else "bar",
            y_axis=self.y_axis_combo.currentText() if self.y_axis_combo else None,
            time_course_mode=self.time_course_checkbox.isChecked() if self.time_course_checkbox else False,
            selected_tissues=selected_tissues,
            selected_times=selected_times
        )
    
    def _generate_plot(self):
        """Generate the plot using the coordinator's unified method."""
        try:
            if not self.csv_path:
                self.status_label.setText("Error: No data available")
                return
            
            # Get current options including filters
            options = self.get_current_options()
            
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
            
            # Apply filters using coordinator's static method
            filtered_df = ProcessingCoordinator.apply_filters(df, options)
            
            # Provide detailed feedback about filtering
            filter_message = f"Filtered data: {len(filtered_df)} of {len(df)} rows"
            if options.selected_tissues:
                filter_message += f" (tissues: {', '.join(options.selected_tissues)})"
            if options.selected_times:
                filter_message += f" (times: {', '.join(map(str, options.selected_times))})"
            logger.info(filter_message)
            
            if filtered_df.empty:
                # Check if no filters are selected
                has_tissue_filter = options.selected_tissues and len(options.selected_tissues) > 0
                has_time_filter = options.selected_times and len(options.selected_times) > 0
                has_time_data = 'Time' in df.columns and len(df['Time'].dropna().unique()) > 0
                
                if not has_tissue_filter and not has_time_filter and has_time_data:
                    error_msg = "No filters selected. Please select at least one tissue or time filter to display data."
                    if 'Tissue' in df.columns:
                        available_tissues = df['Tissue'].dropna().unique()
                        error_msg += f"\n\nAvailable tissues: {', '.join(available_tissues)}"
                    if 'Time' in df.columns:
                        available_times = df['Time'].dropna().unique()
                        error_msg += f"\nAvailable times: {', '.join(map(str, available_times))}"
                elif not has_tissue_filter and not has_time_data:
                    error_msg = "No tissue filter selected. Please select at least one tissue to display data."
                    if 'Tissue' in df.columns:
                        available_tissues = df['Tissue'].dropna().unique()
                        error_msg += f"\n\nAvailable tissues: {', '.join(available_tissues)}"
                else:
                    error_msg = "No data matches the current filter selection."
                    if options.selected_tissues:
                        available_tissues = df['Tissue'].dropna().unique() if 'Tissue' in df.columns else []
                        error_msg += f"\nAvailable tissues: {', '.join(available_tissues)}"
                    if options.selected_times:
                        available_times = df['Time'].dropna().unique() if 'Time' in df.columns else []
                        error_msg += f"\nAvailable times: {', '.join(map(str, available_times))}"
                    error_msg += "\nPlease adjust your filters."
                self._show_error_message(error_msg)
                return
            
            # Generate plot with filtered data
            from flowproc.domain.visualization.flow_cytometry_visualizer import plot, time_plot
            
            if options.time_course_mode:
                fig = time_plot(
                    data=filtered_df,
                    time_col='Time',
                    value_col=options.y_axis,
                    save_html=self.temp_html_file
                )
            else:
                fig = plot(
                    data=filtered_df,
                    x='Group',
                    y=options.y_axis,
                    plot_type=options.plot_type,
                    save_html=self.temp_html_file
                )
            
            result_path = self.temp_html_file
            
            if fig and result_path:
                # Load in web view
                from PySide6.QtCore import QUrl
                file_url = QUrl.fromLocalFile(str(self.temp_html_file))
                self.web_view.load(file_url)
                
                # Update status with filter information
                status_text = f"Plot generated successfully - {len(filtered_df)} of {len(df)} rows displayed"
                if options.selected_tissues and len(options.selected_tissues) < len(df['Tissue'].dropna().unique()):
                    status_text += " (filtered by tissue)"
                if options.selected_times and len(options.selected_times) < len(df['Time'].dropna().unique()):
                    status_text += " (filtered by time)"
                self.status_label.setText(status_text)
                self.plot_generated.emit()
            else:
                self._show_error_message("Failed to generate plot. Please check your data and filters.")
            
        except Exception as e:
            logger.error(f"Failed to generate plot: {e}")
            self._show_error_message(f"Failed to generate plot: {str(e)}")
    
    def _save_visualization(self):
        """Save the current visualization to a user-selected location."""
        if not self.temp_html_file or not self.temp_html_file.exists():
            QMessageBox.warning(self, "No Plot", "Please generate a plot first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Visualization",
            str(self.csv_path.parent / "visualization.html") if self.csv_path else "visualization.html",
            "HTML Files (*.html)"
        )
        
        if file_path:
            import shutil
            shutil.copy2(self.temp_html_file, file_path)
            QMessageBox.information(self, "Success", f"Visualization saved to {file_path}")
    
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
        self.web_view.setHtml(error_html)
        self.status_label.setText("Error generating plot")
    
    def closeEvent(self, event):
        """Handle close event and cleanup temporary files."""
        try:
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file: {e}")
        
        super().closeEvent(event)
