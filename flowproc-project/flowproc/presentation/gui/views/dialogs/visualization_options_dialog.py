"""
Visualization Options Dialog

This dialog handles the configuration of visualization options before plotting.
Separated from the main visualization dialog for better modularity.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QComboBox, QCheckBox, QPushButton, QSpinBox, QMessageBox,
    QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Signal, Qt
import pandas as pd

from flowproc.domain.parsing import load_and_parse_df
from flowproc.core.constants import KEYWORDS, is_pure_metric_column

logger = logging.getLogger(__name__)


@dataclass
class VisualizationOptions:
    """Container for visualization options selected in the dialog."""
    plot_type: str = "line"  # Default to line plot for timecourse
    x_axis: Optional[str] = None  # Auto-detect if None
    y_axis: Optional[str] = None  # Auto-detect if None
    time_course_mode: bool = False
    time_course_strategy: str = "Faceted by Cell Type"  # Default to vertically stacked
    theme: str = "default"
    width: int = 800
    height: int = 600
    show_individual_points: bool = False
    error_bars: bool = True
    interactive: bool = True
    # Covariates for filtering
    tissue_filter: Optional[str] = None
    time_filter: Optional[str] = None


class VisualizationOptionsDialog(QDialog):
    """
    Dialog for configuring visualization options.
    
    This dialog provides a clean interface for selecting visualization parameters
    before generating plots.
    """
    
    # Signals
    options_configured = Signal(VisualizationOptions)
    
    def __init__(self, parent=None, csv_path: Optional[Path] = None, current_options: Optional[VisualizationOptions] = None):
        super().__init__(parent)
        self.csv_path = csv_path
        self.df: Optional[pd.DataFrame] = None
        self.current_options = current_options
        
        self.setWindowTitle("Visualization Options")
        self.setModal(True)
        self.resize(600, 500)
        
        # UI Components
        self.plot_type_combo: Optional[QComboBox] = None
        self.x_axis_combo: Optional[QComboBox] = None
        self.y_axis_combo: Optional[QComboBox] = None
        self.custom_x_axis_combo: Optional[QComboBox] = None
        self.custom_y_axis_combo: Optional[QComboBox] = None
        self.use_custom_axes_checkbox: Optional[QCheckBox] = None
        self.time_course_checkbox: Optional[QCheckBox] = None
        self.width_spinbox: Optional[QSpinBox] = None
        self.height_spinbox: Optional[QSpinBox] = None
        # Covariates components
        self.tissue_filter_combo: Optional[QComboBox] = None
        self.time_filter_combo: Optional[QComboBox] = None
        
        self._setup_ui()
        self._setup_styling()
        
        if csv_path:
            self._analyze_data_simple()
        
        # Apply current options if provided
        if current_options:
            self._apply_current_options(current_options)
    
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
            QComboBox QAbstractItemView {
                background-color: #4c4c4c;
                border: 1px solid #555555;
                border-radius: 3px;
                color: #ffffff;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #5c5c5c;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: #ffffff;
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
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        main_layout = QVBoxLayout()
        
        # Create scroll area for options
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Setup options sections
        self._setup_basic_options(scroll_layout)
        self._setup_covariates_section(scroll_layout)
        self._setup_advanced_options(scroll_layout)
        self._setup_data_info(scroll_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
        # Setup buttons
        self._setup_buttons(main_layout)
        
        self.setLayout(main_layout)
    
    def _setup_basic_options(self, parent_layout: QVBoxLayout):
        """Set up basic visualization options."""
        basic_group = QGroupBox("Basic Options")
        layout = QVBoxLayout()
        
        # Plot type
        plot_type_layout = QHBoxLayout()
        plot_type_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["bar", "scatter", "box", "line", "histogram"])
        self.plot_type_combo.setCurrentText("line")  # Default to line plot for timecourse
        plot_type_layout.addWidget(self.plot_type_combo)
        layout.addLayout(plot_type_layout)
        
        # X-axis
        x_axis_layout = QHBoxLayout()
        x_axis_layout.addWidget(QLabel("X-Axis:"))
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.addItem("Auto-detect")
        x_axis_layout.addWidget(self.x_axis_combo)
        layout.addLayout(x_axis_layout)
        
        # Y-axis (Summary)
        y_axis_layout = QHBoxLayout()
        y_axis_layout.addWidget(QLabel("Y-Axis (Summary):"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.addItem("Auto-detect")
        y_axis_layout.addWidget(self.y_axis_combo)
        layout.addLayout(y_axis_layout)
        
        # Time course mode
        self.time_course_checkbox = QCheckBox("Time Course Mode")
        layout.addWidget(self.time_course_checkbox)
        
        basic_group.setLayout(layout)
        parent_layout.addWidget(basic_group)
    
    def _setup_covariates_section(self, parent_layout: QVBoxLayout):
        """Set up covariates selection."""
        covariates_group = QGroupBox("Covariates")
        layout = QVBoxLayout()
        
        # Tissue Filter
        tissue_layout = QHBoxLayout()
        tissue_layout.addWidget(QLabel("Tissue Filter:"))
        self.tissue_filter_combo = QComboBox()
        self.tissue_filter_combo.addItem("All Tissues")
        self.tissue_filter_combo.setEnabled(False) # Disabled by default
        tissue_layout.addWidget(self.tissue_filter_combo)
        layout.addLayout(tissue_layout)
        
        # Time Filter
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time Filter:"))
        self.time_filter_combo = QComboBox()
        self.time_filter_combo.addItem("All Times")
        self.time_filter_combo.setEnabled(False) # Disabled by default
        time_layout.addWidget(self.time_filter_combo)
        layout.addLayout(time_layout)
        
        covariates_group.setLayout(layout)
        parent_layout.addWidget(covariates_group)
    
    def _setup_advanced_options(self, parent_layout: QVBoxLayout):
        """Set up advanced visualization options."""
        advanced_group = QGroupBox("Advanced Options")
        layout = QVBoxLayout()
        
        # Custom axes toggle
        self.use_custom_axes_checkbox = QCheckBox("Use Custom X and Y Axis Columns")
        self.use_custom_axes_checkbox.toggled.connect(self._on_custom_axes_toggled)
        layout.addWidget(self.use_custom_axes_checkbox)
        
        # Custom X-axis selection
        custom_x_layout = QHBoxLayout()
        custom_x_layout.addWidget(QLabel("Custom X-Axis:"))
        self.custom_x_axis_combo = QComboBox()
        self.custom_x_axis_combo.addItem("Select column...")
        self.custom_x_axis_combo.setEnabled(False)
        custom_x_layout.addWidget(self.custom_x_axis_combo)
        layout.addLayout(custom_x_layout)
        
        # Custom Y-axis selection
        custom_y_layout = QHBoxLayout()
        custom_y_layout.addWidget(QLabel("Custom Y-Axis:"))
        self.custom_y_axis_combo = QComboBox()
        self.custom_y_axis_combo.addItem("Select column...")
        self.custom_y_axis_combo.setEnabled(False)
        custom_y_layout.addWidget(self.custom_y_axis_combo)
        layout.addLayout(custom_y_layout)
        
        # Dimensions
        dimensions_layout = QHBoxLayout()
        dimensions_layout.addWidget(QLabel("Width:"))
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(400, 2000)
        self.width_spinbox.setValue(600)
        dimensions_layout.addWidget(self.width_spinbox)
        
        dimensions_layout.addWidget(QLabel("Height:"))
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(300, 1500)
        self.height_spinbox.setValue(400)
        dimensions_layout.addWidget(self.height_spinbox)
        layout.addLayout(dimensions_layout)
        
        advanced_group.setLayout(layout)
        parent_layout.addWidget(advanced_group)
    
    def _setup_data_info(self, parent_layout: QVBoxLayout):
        """Set up data information display."""
        info_group = QGroupBox("Data Information")
        layout = QVBoxLayout()
        
        self.data_info_label = QLabel("No data loaded")
        layout.addWidget(self.data_info_label)
        
        info_group.setLayout(layout)
        parent_layout.addWidget(info_group)
    
    def _setup_buttons(self, parent_layout: QVBoxLayout):
        """Set up the dialog buttons."""
        button_layout = QHBoxLayout()
        
        # Add spacer to push buttons to the right
        button_layout.addStretch()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Configure button
        configure_button = QPushButton("Configure & Generate Plot")
        configure_button.clicked.connect(self._configure_and_generate)
        configure_button.setDefault(True)
        button_layout.addWidget(configure_button)
        
        parent_layout.addLayout(button_layout)
    
    def _analyze_data_simple(self):
        """Analyze the CSV data to populate options."""
        try:
            if not self.csv_path or not self.csv_path.exists():
                self.data_info_label.setText("Error: CSV file not found")
                return
            
            # Use the proper parsing logic
            self.df, _ = load_and_parse_df(self.csv_path)
            
            if self.df is not None and not self.df.empty:
                self._populate_column_options(self.df)
                self._update_data_info()
            else:
                self.data_info_label.setText("Error: No data found in CSV")
                
        except Exception as e:
            logger.error(f"Failed to analyze data: {e}")
            self.data_info_label.setText(f"Error analyzing data: {str(e)}")
    
    def _populate_column_options(self, df: pd.DataFrame):
        """Populate the column selection combos."""
        if df is None or df.empty:
            return
        
        # Clear existing items (keep "Auto-detect")
        self.x_axis_combo.clear()
        self.x_axis_combo.addItem("Auto-detect")
        
        self.y_axis_combo.clear()
        self.y_axis_combo.addItem("Auto-detect")
        
        self.custom_x_axis_combo.clear()
        self.custom_x_axis_combo.addItem("Select column...")
        
        self.custom_y_axis_combo.clear()
        self.custom_y_axis_combo.addItem("Select column...")
        
        # Identify categorical columns (for X-axis) and summary metrics (for Y-axis)
        categorical_columns = self._identify_categorical_columns(df)
        summary_metrics = self._identify_summary_metrics(df)
        
        # Populate X-axis with categorical columns (priority for 'Group')
        x_columns = []
        if 'Group' in categorical_columns:
            x_columns.append('Group')
        x_columns.extend([col for col in categorical_columns if col != 'Group'])
        
        for col in x_columns:
            self.x_axis_combo.addItem(col)
        
        # Set default X-axis to 'Group' if available
        if 'Group' in categorical_columns:
            self.x_axis_combo.setCurrentText('Group')
        elif categorical_columns:
            self.x_axis_combo.setCurrentText(categorical_columns[0])
        
        # Populate Y-axis with summary metrics
        for metric in summary_metrics:
            self.y_axis_combo.addItem(metric)
        
        # Add ALL columns to custom x-axis and y-axis dropdowns for advanced users
        for col in df.columns:
            self.custom_x_axis_combo.addItem(col)
            self.custom_y_axis_combo.addItem(col)
        
        # Set default Y-axis to 'Freq. of Parent' if available
        if 'Freq. of Parent' in summary_metrics:
            self.y_axis_combo.setCurrentText('Freq. of Parent')
        elif summary_metrics:
            self.y_axis_combo.setCurrentText(summary_metrics[0])
        
        # Populate covariates dropdowns
        self._populate_covariates_options(df)
    
    def _identify_categorical_columns(self, df: pd.DataFrame) -> List[str]:
        """Identify categorical columns suitable for X-axis."""
        categorical_columns = []
        
        # Common categorical column names (excluding Tissue and SampleID)
        categorical_keywords = [
            'group', 'animal', 'well', 'time', 'replicate',
            'treatment', 'condition', 'experiment', 'batch', 'day', 'week',
            'mouse', 'rat', 'subject', 'patient', 'donor'
        ]
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Skip Tissue and SampleID columns (they will be used as covariates)
            if col_lower in ['tissue', 'sampleid', 'sample_id']:
                continue
            
            # Check if column name contains categorical keywords
            if any(keyword in col_lower for keyword in categorical_keywords):
                categorical_columns.append(col)
                continue
            
            # Check if column contains mostly string/non-numeric data
            if df[col].dtype == 'object':
                # Check if it's not a metric column (doesn't contain metric keywords)
                is_metric = any(keyword.lower() in col_lower for keyword in KEYWORDS.keys())
                if not is_metric:
                    categorical_columns.append(col)
                continue
            
            # Check if numeric column has limited unique values (likely categorical)
            if df[col].dtype in ['int64', 'float64']:
                unique_ratio = len(df[col].unique()) / len(df)
                if unique_ratio < 0.1:  # Less than 10% unique values
                    categorical_columns.append(col)
        
        return categorical_columns
    
    def _identify_summary_metrics(self, df: pd.DataFrame) -> List[str]:
        """Identify summary metrics in the dataframe."""
        summary_metrics = []
        
        for keyword in KEYWORDS:
            # Find columns that contain this keyword
            matching_cols = [col for col in df.columns if keyword.lower() in col.lower()]
            if matching_cols:
                # Add the keyword as a metric type (include both pure metrics and subpopulations)
                summary_metrics.append(keyword)
        
        return summary_metrics
    
    def _on_custom_axes_toggled(self, checked: bool):
        """Handle custom axes toggle."""
        if self.x_axis_combo:
            self.x_axis_combo.setEnabled(not checked)
        if self.custom_x_axis_combo:
            self.custom_x_axis_combo.setEnabled(checked)
        if self.y_axis_combo:
            self.y_axis_combo.setEnabled(not checked)
        if self.custom_y_axis_combo:
            self.custom_y_axis_combo.setEnabled(checked)
    
    def _populate_covariates_options(self, df: pd.DataFrame):
        """Populate the covariates filter dropdowns."""
        # Populate Tissue filter
        self.tissue_filter_combo.clear()
        self.tissue_filter_combo.addItem("All Tissues")
        
        if 'Tissue' in df.columns:
            tissues = sorted(df['Tissue'].unique())
            for tissue in tissues:
                self.tissue_filter_combo.addItem(str(tissue))
            self.tissue_filter_combo.setEnabled(True)
        
        # Populate Time filter
        self.time_filter_combo.clear()
        self.time_filter_combo.addItem("All Times")
        
        if 'Time' in df.columns:
            times = sorted(df['Time'].unique())
            for time in times:
                self.time_filter_combo.addItem(str(time))
            self.time_filter_combo.setEnabled(True)
    
    def _update_data_info(self):
        """Update the data information display."""
        if self.df is not None and not self.df.empty:
            info_text = f"Rows: {len(self.df)}, Columns: {len(self.df.columns)}"
            if 'Group' in self.df.columns:
                groups = self.df['Group'].unique()
                info_text += f", Groups: {len(groups)} ({', '.join(map(str, groups))})"
            self.data_info_label.setText(info_text)
        else:
            self.data_info_label.setText("No data available")
    
    def _configure_and_generate(self):
        """Configure options and emit signal to generate plot."""
        try:
            options = self._get_visualization_options()
            self.options_configured.emit(options)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Configuration Error", f"Failed to configure options: {str(e)}")
    
    def _get_visualization_options(self) -> VisualizationOptions:
        """Get the current visualization options from the UI."""
        # Handle X-axis selection (summary vs custom)
        if self.use_custom_axes_checkbox.isChecked():
            x_axis = self.custom_x_axis_combo.currentText()
            if x_axis == "Select column...":
                x_axis = None
        else:
            x_axis = None if self.x_axis_combo.currentText() == "Auto-detect" else self.x_axis_combo.currentText()
        
        # Handle Y-axis selection (summary vs custom)
        if self.use_custom_axes_checkbox.isChecked():
            y_axis = self.custom_y_axis_combo.currentText()
            if y_axis == "Select column...":
                y_axis = None
        else:
            y_axis = None if self.y_axis_combo.currentText() == "Auto-detect" else self.y_axis_combo.currentText()
        
        # Handle covariates
        tissue_filter = None
        if self.tissue_filter_combo and self.tissue_filter_combo.isEnabled():
            tissue_filter = self.tissue_filter_combo.currentText()
            if tissue_filter == "All Tissues":
                tissue_filter = None
        
        time_filter = None
        if self.time_filter_combo and self.time_filter_combo.isEnabled():
            time_filter = self.time_filter_combo.currentText()
            if time_filter == "All Times":
                time_filter = None
        
        return VisualizationOptions(
            plot_type=self.plot_type_combo.currentText(),
            x_axis=x_axis,
            y_axis=y_axis,
            time_course_mode=self.time_course_checkbox.isChecked(),
            time_course_strategy=self.time_course_strategy_combo.currentText(), # Assuming time_course_strategy_combo is added
            width=self.width_spinbox.value(),
            height=self.height_spinbox.value(),
            tissue_filter=tissue_filter,
            time_filter=time_filter
        )
    
    def _apply_current_options(self, options: VisualizationOptions):
        """Apply current options to the UI."""
        try:
            if self.plot_type_combo and options.plot_type:
                index = self.plot_type_combo.findText(options.plot_type)
                if index >= 0:
                    self.plot_type_combo.setCurrentIndex(index)
            
            if self.x_axis_combo and options.x_axis:
                index = self.x_axis_combo.findText(options.x_axis)
                if index >= 0:
                    self.x_axis_combo.setCurrentIndex(index)
                    self.use_custom_axes_checkbox.setChecked(False)
                else:
                    # Try custom X-axis
                    if self.custom_x_axis_combo:
                        index = self.custom_x_axis_combo.findText(options.x_axis)
                        if index >= 0:
                            self.custom_x_axis_combo.setCurrentIndex(index)
                            self.use_custom_axes_checkbox.setChecked(True)
            
            if self.y_axis_combo and options.y_axis:
                # Check if it's a summary metric or custom column
                index = self.y_axis_combo.findText(options.y_axis)
                if index >= 0:
                    self.y_axis_combo.setCurrentIndex(index)
                    self.use_custom_axes_checkbox.setChecked(False)
                else:
                    # Try custom Y-axis
                    if self.custom_y_axis_combo:
                        index = self.custom_y_axis_combo.findText(options.y_axis)
                        if index >= 0:
                            self.custom_y_axis_combo.setCurrentIndex(index)
                            self.use_custom_axes_checkbox.setChecked(True)
            
            if self.time_course_checkbox:
                self.time_course_checkbox.setChecked(options.time_course_mode)
            
            if self.width_spinbox:
                self.width_spinbox.setValue(options.width)
            
            if self.height_spinbox:
                self.height_spinbox.setValue(options.height)
            
            # Apply covariates
            if self.tissue_filter_combo and options.tissue_filter:
                index = self.tissue_filter_combo.findText(options.tissue_filter)
                if index >= 0:
                    self.tissue_filter_combo.setCurrentIndex(index)
            
            if self.time_filter_combo and options.time_filter:
                index = self.time_filter_combo.findText(options.time_filter)
                if index >= 0:
                    self.time_filter_combo.setCurrentIndex(index)
                
        except Exception as e:
            logger.warning(f"Failed to apply current options: {e}")
    
    def get_visualization_options(self) -> Optional[VisualizationOptions]:
        """Get the current visualization options."""
        try:
            return self._get_visualization_options()
        except Exception as e:
            logger.error(f"Failed to get visualization options: {e}")
            return None 