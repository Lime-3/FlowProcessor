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
    QFileDialog
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
import pandas as pd

from flowproc.domain.parsing import load_and_parse_df
from flowproc.domain.visualization.flow_cytometry_visualizer import plot, time_plot

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
        self.df = None
        
        # UI Components
        self.plot_type_combo: Optional[QComboBox] = None
        self.y_axis_combo: Optional[QComboBox] = None
        self.time_course_checkbox: Optional[QCheckBox] = None
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
            self._generate_plot()  # Auto-generate initial plot
    
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
        
        # First row: Plot type and Y-axis
        first_row = QHBoxLayout()
        
        # Plot type selection
        plot_type_layout = QVBoxLayout()
        plot_type_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["bar", "box", "scatter", "line"])
        self.plot_type_combo.currentTextChanged.connect(self._on_option_changed)
        plot_type_layout.addWidget(self.plot_type_combo)
        first_row.addLayout(plot_type_layout)
        
        # Y-axis selection
        y_axis_layout = QVBoxLayout()
        y_axis_layout.addWidget(QLabel("Y-Axis:"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.currentTextChanged.connect(self._on_option_changed)
        y_axis_layout.addWidget(self.y_axis_combo)
        first_row.addLayout(y_axis_layout)
        
        # Time course mode
        time_course_layout = QVBoxLayout()
        time_course_layout.addWidget(QLabel("Mode:"))
        self.time_course_checkbox = QCheckBox("Time Course Mode")
        self.time_course_checkbox.toggled.connect(self._on_time_course_toggled)
        time_course_layout.addWidget(self.time_course_checkbox)
        first_row.addLayout(time_course_layout)
        
        # Add some spacing
        first_row.addStretch()
        
        basic_layout.addLayout(first_row)
        
        # Action Buttons - prominently displayed
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Push buttons to the right
        
        generate_button = QPushButton("Generate Plot")
        generate_button.setMinimumHeight(40)
        generate_button.clicked.connect(self._generate_plot)
        button_layout.addWidget(generate_button)
        
        save_button = QPushButton("Save Plot")
        save_button.setMinimumHeight(40)
        save_button.clicked.connect(self._save_visualization)
        button_layout.addWidget(save_button)
        
        basic_layout.addLayout(button_layout)
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
                background-color: #007BFF;
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
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
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
        """)
    
    def _analyze_data(self):
        """Analyze the loaded data and populate options."""
        try:
            if not self.csv_path or not self.csv_path.exists():
                self.status_label.setText("Error: CSV file not found")
                return
            
            self.df, _ = load_and_parse_df(self.csv_path)
            
            if self.df is None or self.df.empty:
                self.status_label.setText("Error: No data found in CSV file")
                return
            
            # Populate column options
            self._populate_column_options(self.df)
            
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
    
    def _on_option_changed(self):
        """Handle option changes."""
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
    
    def _generate_plot(self):
        """Generate the plot based on current options."""
        try:
            if not self.csv_path or self.df is None:
                self.status_label.setText("Error: No data available")
                return
            
            # Get current options
            plot_type = self.plot_type_combo.currentText()
            y_axis = self.y_axis_combo.currentText()
            time_course_mode = self.time_course_checkbox.isChecked()
            
            # Create temporary HTML file
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                self.temp_html_file = Path(tmp_file.name)
            
            self.status_label.setText("Generating plot...")
            
            # Generate plot
            if time_course_mode:
                time_plot(
                    data=self.csv_path,
                    time_col='Time',
                    value_col=y_axis,
                    save_html=self.temp_html_file
                )
            else:
                plot(
                    data=self.csv_path,
                    x='Group',
                    y=y_axis,
                    plot_type=plot_type,
                    save_html=self.temp_html_file
                )
            
            # Load in web view
            from PySide6.QtCore import QUrl
            file_url = QUrl.fromLocalFile(str(self.temp_html_file))
            self.web_view.load(file_url)
            
            # Update status
            self.status_label.setText("Plot generated successfully")
            self.plot_generated.emit()
            
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
