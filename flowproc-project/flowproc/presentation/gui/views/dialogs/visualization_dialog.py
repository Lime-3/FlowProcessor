"""
Visualization dialog for selecting visualization parameters.

This dialog provides a comprehensive interface for configuring visualization
options including metrics, tissues, themes, and other parameters.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QLabel, QPushButton,
    QLineEdit, QMessageBox, QWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QUrl
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView

import pandas as pd
import tempfile

from flowproc.domain.visualization.facade import create_visualization
from flowproc.domain.visualization.data_processor import detect_data_characteristics
from flowproc.domain.parsing import load_and_parse_df
from flowproc.core.constants import KEYWORDS

logger = logging.getLogger(__name__)


@dataclass
class VisualizationOptions:
    """Container for visualization options selected in the dialog."""
    metric: str
    time_course_mode: bool
    theme: str
    width: int
    height: int
    tissue_filter: Optional[str] = None
    subpopulation_filter: Optional[str] = None
    user_group_labels: Optional[List[str]] = None
    show_individual_points: bool = False
    error_bars: bool = True
    interactive: bool = True


class DataAnalysisWorker(QThread):
    """Worker thread for analyzing data characteristics."""
    
    analysis_complete = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, csv_path: Path):
        super().__init__()
        self.csv_path = csv_path
    
    def run(self):
        """Analyze the CSV file to detect available options."""
        try:
            # Load and analyze the data
            df, sid_col = load_and_parse_df(self.csv_path)
            characteristics = detect_data_characteristics(df)
            
            # Get available metrics
            available_metrics = []
            for metric in KEYWORDS.keys():
                key_substring = KEYWORDS.get(metric, metric.lower())
                matching_cols = [
                    col for col in df.columns
                    if key_substring in col.lower()
                    and col not in {sid_col, 'Well', 'Group', 'Animal', 
                                  'Time', 'Replicate', 'Tissue'}
                    and not df[col].isna().all()
                ]
                if matching_cols:
                    available_metrics.append(metric)
            
            # Get available tissues
            available_tissues = []
            if 'Tissue' in df.columns:
                tissues = df['Tissue'].dropna().unique()
                available_tissues = [t for t in tissues if t != 'UNK']
            
            # Get available subpopulations (if any)
            available_subpopulations = []
            if 'Subpopulation' in df.columns:
                subpops = df['Subpopulation'].dropna().unique()
                available_subpopulations = list(subpops)
            
            # Check for time data
            has_time_data = "Time" in df.columns and df["Time"].notna().any()
            
            analysis_result = {
                'available_metrics': available_metrics,
                'available_tissues': available_tissues,
                'available_subpopulations': available_subpopulations,
                'has_time_data': has_time_data,
                'data_shape': df.shape,
                'characteristics': characteristics
            }
            
            self.analysis_complete.emit(analysis_result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class VisualizationDialog(QDialog):
    """
    Dialog for configuring visualization options with live preview.
    
    This dialog provides a comprehensive interface for selecting
    visualization parameters with real-time plot updates.
    """
    
    # Signals
    visualization_requested = Signal(VisualizationOptions)
    
    def __init__(self, parent=None, csv_path: Optional[Path] = None):
        super().__init__(parent)
        self.csv_path = csv_path
        self.analysis_worker: Optional[DataAnalysisWorker] = None
        self.analysis_result: Optional[Dict[str, Any]] = None
        self.temp_html_file: Optional[Path] = None
        self.update_timer: Optional[QTimer] = None
        
        self.setWindowTitle("Visualization Options")
        self.setModal(True)
        self.resize(1200, 800)
        
        self._setup_ui()
        self._setup_styling()
        self._setup_update_timer()
        
        if csv_path:
            self._analyze_data()
    
    def _setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Options section on top
        self._setup_options_section(layout)
        
        # Plot section below
        self._setup_plot_section(layout)
        
        # Buttons at bottom
        self._setup_buttons(layout)
    
    def _setup_options_section(self, parent_layout: QVBoxLayout):
        """Set up the options section on top."""
        # Create scrollable options area
        options_scroll = QScrollArea()
        options_scroll.setWidgetResizable(True)
        options_scroll.setMaximumHeight(300)
        options_scroll.setFrameStyle(QFrame.Shape.NoFrame)
        
        options_widget = QWidget()
        options_layout = QHBoxLayout(options_widget)
        options_layout.setSpacing(20)
        
        # Basic options group
        basic_group = self._create_basic_options_group()
        options_layout.addWidget(basic_group)
        
        # Advanced options group
        advanced_group = self._create_advanced_options_group()
        options_layout.addWidget(advanced_group)
        
        # Data info group
        info_group = self._create_data_info_group()
        options_layout.addWidget(info_group)
        
        options_layout.addStretch()
        options_scroll.setWidget(options_widget)
        parent_layout.addWidget(options_scroll)
    
    def _create_basic_options_group(self) -> QGroupBox:
        """Create the basic options group."""
        group = QGroupBox("Basic Options")
        layout = QFormLayout(group)
        layout.setSpacing(8)
        
        # Metric selection
        self.metric_combo = QComboBox()
        self.metric_combo.addItems([
            "Freq. of Parent", "Freq. of Total", "Freq. of Live",
            "Count", "Median", "Mean", "Geometric Mean"
        ])
        self.metric_combo.setCurrentText("Freq. of Parent")
        self.metric_combo.currentTextChanged.connect(self._on_option_changed)
        layout.addRow("Metric:", self.metric_combo)
        
        # Time course mode
        self.time_course_checkbox = QCheckBox("Time Course Mode")
        self.time_course_checkbox.setToolTip("Enable for time-course line plots")
        self.time_course_checkbox.toggled.connect(self._on_option_changed)
        layout.addRow("Mode:", self.time_course_checkbox)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "default", "scientific", "publication", "presentation", 
            "minimal", "colorful", "dark"
        ])
        self.theme_combo.setCurrentText("default")
        self.theme_combo.currentTextChanged.connect(self._on_option_changed)
        layout.addRow("Theme:", self.theme_combo)
        
        # Dimensions
        self.width_spin = QSpinBox()
        self.width_spin.setRange(400, 2000)
        self.width_spin.setValue(1200)
        self.width_spin.setSuffix(" px")
        self.width_spin.valueChanged.connect(self._on_option_changed)
        layout.addRow("Width:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(300, 1500)
        self.height_spin.setValue(600)
        self.height_spin.setSuffix(" px")
        self.height_spin.valueChanged.connect(self._on_option_changed)
        layout.addRow("Height:", self.height_spin)
        
        return group
    
    def _create_advanced_options_group(self) -> QGroupBox:
        """Create the advanced options group."""
        group = QGroupBox("Advanced Options")
        layout = QFormLayout(group)
        layout.setSpacing(8)
        
        # Tissue filter
        self.tissue_combo = QComboBox()
        self.tissue_combo.addItem("All Tissues")
        self.tissue_combo.setEnabled(False)
        self.tissue_combo.currentTextChanged.connect(self._on_option_changed)
        layout.addRow("Tissue Filter:", self.tissue_combo)
        
        # Subpopulation filter
        self.subpop_combo = QComboBox()
        self.subpop_combo.addItem("All Subpopulations")
        self.subpop_combo.setEnabled(False)
        self.subpop_combo.currentTextChanged.connect(self._on_option_changed)
        layout.addRow("Subpopulation Filter:", self.subpop_combo)
        
        # Display options
        self.error_bars_checkbox = QCheckBox("Show Error Bars")
        self.error_bars_checkbox.setChecked(True)
        self.error_bars_checkbox.toggled.connect(self._on_option_changed)
        layout.addRow("Error Bars:", self.error_bars_checkbox)
        
        self.individual_points_checkbox = QCheckBox("Show Individual Points")
        self.individual_points_checkbox.toggled.connect(self._on_option_changed)
        layout.addRow("Individual Points:", self.individual_points_checkbox)
        
        self.interactive_checkbox = QCheckBox("Interactive Plot")
        self.interactive_checkbox.setChecked(True)
        self.interactive_checkbox.toggled.connect(self._on_option_changed)
        layout.addRow("Interactive:", self.interactive_checkbox)
        
        # Group labels
        self.group_labels_edit = QLineEdit()
        self.group_labels_edit.setPlaceholderText("Control, Treatment A, Treatment B")
        self.group_labels_edit.textChanged.connect(self._on_option_changed)
        layout.addRow("Custom Labels:", self.group_labels_edit)
        
        return group
    
    def _create_data_info_group(self) -> QGroupBox:
        """Create the data information group."""
        group = QGroupBox("Data Information")
        layout = QFormLayout(group)
        layout.setSpacing(8)
        
        self.data_shape_label = QLabel("Loading...")
        layout.addRow("Data Shape:", self.data_shape_label)
        
        self.time_data_label = QLabel("Loading...")
        layout.addRow("Time Data:", self.time_data_label)
        
        self.metrics_label = QLabel("Loading...")
        layout.addRow("Available Metrics:", self.metrics_label)
        
        self.tissues_label = QLabel("Loading...")
        layout.addRow("Available Tissues:", self.tissues_label)
        
        return group
    
    def _setup_plot_section(self, parent_layout: QVBoxLayout):
        """Set up the plot section below."""
        # Plot label
        plot_label = QLabel("Live Preview")
        plot_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #0064FF; margin-bottom: 8px;")
        parent_layout.addWidget(plot_label)
        
        # Web view for plot
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(400)
        self.web_view.setHtml("""
            <html>
            <body style="background-color: #2b2b2b; color: #ffffff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
                <div style="text-align: center;">
                    <h3>Loading visualization...</h3>
                    <p>Please wait while the data is being analyzed.</p>
                </div>
            </body>
            </html>
        """)
        parent_layout.addWidget(self.web_view)
    
    def _setup_buttons(self, parent_layout: QVBoxLayout):
        """Set up the buttons at the bottom."""
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Visualization")
        self.save_button.clicked.connect(self._save_visualization)
        self.save_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        parent_layout.addLayout(button_layout)
    
    def _setup_update_timer(self):
        """Set up timer for delayed plot updates."""
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_plot)
    
    def _setup_styling(self):
        """Set up the dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #3c3c3c;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QComboBox, QSpinBox, QLineEdit {
                background-color: #4c4c4c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
                min-height: 20px;
            }
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                color: #ffffff;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QScrollArea {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
            }
        """)
    
    def _analyze_data(self):
        """Analyze the CSV data to populate available options."""
        if not self.csv_path or not self.csv_path.exists():
            return
        
        # Create and start analysis worker
        self.analysis_worker = DataAnalysisWorker(self.csv_path)
        self.analysis_worker.analysis_complete.connect(self._on_analysis_complete)
        self.analysis_worker.error_occurred.connect(self._on_analysis_error)
        self.analysis_worker.start()
        
        # Update UI to show loading state
        self.data_shape_label.setText("Analyzing...")
        self.time_data_label.setText("Analyzing...")
        self.metrics_label.setText("Analyzing...")
        self.tissues_label.setText("Analyzing...")
    
    def _on_analysis_complete(self, result: Dict[str, Any]):
        """Handle data analysis completion."""
        self.analysis_result = result
        
        # Update metric combo with available metrics
        available_metrics = result.get('available_metrics', [])
        if available_metrics:
            self.metric_combo.clear()
            self.metric_combo.addItems(available_metrics)
            self.metric_combo.setCurrentText(available_metrics[0])
        
        # Update tissue combo
        available_tissues = result.get('available_tissues', [])
        if available_tissues:
            self.tissue_combo.clear()
            self.tissue_combo.addItem("All Tissues")
            self.tissue_combo.addItems(available_tissues)
            self.tissue_combo.setEnabled(True)
        
        # Update subpopulation combo
        available_subpops = result.get('available_subpopulations', [])
        if available_subpops:
            self.subpop_combo.clear()
            self.subpop_combo.addItem("All Subpopulations")
            self.subpop_combo.addItems(available_subpops)
            self.subpop_combo.setEnabled(True)
        
        # Update time course checkbox
        has_time_data = result.get('has_time_data', False)
        self.time_course_checkbox.setEnabled(has_time_data)
        if not has_time_data:
            self.time_course_checkbox.setToolTip("No time data available in the CSV file")
        
        # Update data info labels
        data_shape = result.get('data_shape', (0, 0))
        self.data_shape_label.setText(f"{data_shape[0]} rows, {data_shape[1]} columns")
        
        self.time_data_label.setText("Available" if has_time_data else "Not available")
        
        metrics_text = ", ".join(available_metrics) if available_metrics else "None detected"
        self.metrics_label.setText(metrics_text)
        
        tissues_text = ", ".join(available_tissues) if available_tissues else "None detected"
        self.tissues_label.setText(tissues_text)
        
        # Enable save button and create initial plot
        self.save_button.setEnabled(True)
        self._update_plot()
    
    def _on_analysis_error(self, error_message: str):
        """Handle data analysis error."""
        QMessageBox.warning(
            self,
            "Analysis Error",
            f"Failed to analyze data: {error_message}\n\nBasic visualization options will be available."
        )
        
        # Enable save button with basic options
        self.save_button.setEnabled(True)
        self._update_plot()
    
    def _on_option_changed(self):
        """Handle option changes - trigger delayed plot update."""
        if self.update_timer:
            self.update_timer.start(500)  # 500ms delay to avoid too frequent updates
    
    def _update_plot(self):
        """Update the plot with current options."""
        if not self.csv_path or not self.save_button.isEnabled():
            return
        
        try:
            options = self._get_visualization_options()
            
            # Create temporary HTML file
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                self.temp_html_file = Path(tmp_file.name)
            
            # Create visualization
            fig = create_visualization(
                data_source=self.csv_path,
                metric=options.metric,
                output_html=self.temp_html_file,
                time_course_mode=options.time_course_mode,
                theme=options.theme,
                width=options.width,
                height=options.height,
                tissue_filter=options.tissue_filter,
                subpopulation_filter=options.subpopulation_filter,
                user_group_labels=options.user_group_labels,
                show_individual_points=options.show_individual_points,
                error_bars=options.error_bars,
                interactive=options.interactive
            )
            
            # Load in web view
            self.web_view.load(QUrl.fromLocalFile(str(self.temp_html_file)))
            
        except Exception as e:
            # Show error in web view
            error_html = f"""
            <html>
            <body style="background-color: #2b2b2b; color: #ffffff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
                <div style="text-align: center;">
                    <h3 style="color: #ff6b6b;">Visualization Error</h3>
                    <p>{str(e)}</p>
                </div>
            </body>
            </html>
            """
            self.web_view.setHtml(error_html)
    
    def _get_visualization_options(self) -> VisualizationOptions:
        """Get the current visualization options from the dialog."""
        # Parse group labels
        group_labels_text = self.group_labels_edit.text().strip()
        user_group_labels = None
        if group_labels_text:
            user_group_labels = [label.strip() for label in group_labels_text.split(',') if label.strip()]
        
        # Get tissue filter
        tissue_filter = None
        if self.tissue_combo.currentText() != "All Tissues":
            tissue_filter = self.tissue_combo.currentText()
        
        # Get subpopulation filter
        subpop_filter = None
        if self.subpop_combo.currentText() != "All Subpopulations":
            subpop_filter = self.subpop_combo.currentText()
        
        return VisualizationOptions(
            metric=self.metric_combo.currentText(),
            time_course_mode=self.time_course_checkbox.isChecked(),
            theme=self.theme_combo.currentText(),
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            tissue_filter=tissue_filter,
            subpopulation_filter=subpop_filter,
            user_group_labels=user_group_labels,
            show_individual_points=self.individual_points_checkbox.isChecked(),
            error_bars=self.error_bars_checkbox.isChecked(),
            interactive=self.interactive_checkbox.isChecked()
        )
    
    def _save_visualization(self):
        """Save the current visualization."""
        if not self.csv_path:
            QMessageBox.warning(self, "Error", "No CSV file selected for visualization.")
            return
        
        options = self._get_visualization_options()
        self.visualization_requested.emit(options)
        self.accept()
    
    def get_visualization_options(self) -> Optional[VisualizationOptions]:
        """Get the visualization options after dialog execution."""
        if self.result() == QDialog.DialogCode.Accepted:
            return self._get_visualization_options()
        return None
    
    def closeEvent(self, event):
        """Clean up temporary files on close."""
        if self.temp_html_file and self.temp_html_file.exists():
            try:
                self.temp_html_file.unlink()
            except:
                pass
        super().closeEvent(event) 