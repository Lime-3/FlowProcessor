"""
Visualization Display Dialog

This dialog displays flow cytometry visualizations with inline configuration options.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QGroupBox, QComboBox, QCheckBox, QSpinBox, QApplication
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView

from flowproc.domain.visualization.simple_visualizer import plot, time_plot, time_plot_faceted
from flowproc.domain.parsing import load_and_parse_df
from flowproc.core.constants import KEYWORDS, is_pure_metric_column

logger = logging.getLogger(__name__)


class VisualizationDisplayDialog(QDialog):
    """
    Dialog for displaying flow cytometry visualizations.
    
    This dialog focuses on displaying plots with options to save and open in browser.
    Options configuration is handled by a separate dialog.
    """
    
    # Signals
    plot_generated = Signal()
    
    def __init__(self, parent=None, csv_path: Optional[Path] = None, options=None):
        super().__init__(parent)
        self.csv_path = csv_path
        self.options = options
        self.temp_html_file: Optional[Path] = None
        self.df = None
        
        # UI Components for configuration
        self.plot_mode_combo: Optional[QComboBox] = None
        self.plot_type_combo: Optional[QComboBox] = None
        self.x_axis_combo: Optional[QComboBox] = None
        self.y_axis_combo: Optional[QComboBox] = None
        self.custom_x_axis_combo: Optional[QComboBox] = None
        self.custom_y_axis_combo: Optional[QComboBox] = None
        self.use_custom_axes_checkbox: Optional[QCheckBox] = None
        self.time_course_checkbox: Optional[QCheckBox] = None
        self.timecourse_strategy_combo: Optional[QComboBox] = None
        
        # Covariates components
        self.tissue_filter_combo: Optional[QComboBox] = None
        self.time_filter_combo: Optional[QComboBox] = None
        
        self.setWindowTitle("Flow Cytometry Visualization")
        self.setModal(False)  # Non-modal so user can interact with main window
        
        # Set size policy to allow resizing
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Get screen dimensions for dynamic sizing
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.size()
            # Calculate appropriate dialog size - settings take 1/4 of height
            # Target: ~80% of screen width and ~85% of screen height
            target_width = min(int(screen_size.width() * 0.8), 1200)  # Max 1200px width
            target_height = min(int(screen_size.height() * 0.85), 800)  # Max 800px height
            self.resize(target_width, target_height)
        else:
            # Fallback to conservative size
            self.resize(1000, 700)
        
        self._setup_ui()
        self._setup_styling()
        
        if csv_path:
            self._analyze_data()
            if options:
                self._apply_options(options)
                self._generate_plot()
            else:
                # Generate a basic placeholder plot with default options
                self._generate_placeholder_plot()
    
    def _setup_styling(self):
        """Set up the dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px 0 5px;
                color: #ffffff;
                background-color: transparent;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: bold;
                min-height: 18px;
                max-height: 25px;
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
            QLabel {
                color: #ffffff;
                font-size: 11px;
                background-color: transparent;
                border: none;
            }
            QComboBox {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 4px 8px;
                color: #ffffff;
                min-height: 20px;
                max-height: 25px;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
            QComboBox:editable {
                background-color: #4a4a4a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QComboBox::drop-down:open {
                border: none;
            }
            QComboBox:focus {
                border: 1px solid #0078d4;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #4a4a4a;
                border: 1px solid #666666;
                color: #ffffff;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
                outline: none;
                max-height: 200px;
                min-height: 50px;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #5a5a5a;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QComboBox QAbstractItemView::item:alternate {
                background-color: #4a4a4a;
            }
            QComboBox QAbstractItemView::item:!alternate {
                background-color: #4a4a4a;
            }
            QComboBox QAbstractItemView::item:selected:alternate {
                background-color: #0078d4;
                color: #ffffff;
            }
            QComboBox QAbstractItemView::item:selected:!alternate {
                background-color: #0078d4;
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 11px;
                spacing: 5px;
                background-color: transparent;
                border: none;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: transparent;
                border: 1px solid #666666;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
            QCheckBox::indicator:unchecked {
                background-color: transparent;
                border: 1px solid #666666;
            }
        """)
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)  # Reduced spacing for compact layout
        main_layout.setContentsMargins(10, 10, 10, 10)  # Compact margins
        
        # Configuration section
        self._setup_configuration_section(main_layout)
        
        # Plot display section
        self._setup_plot_section(main_layout)
        
        # Buttons section
        self._setup_buttons(main_layout)
        
        self.setLayout(main_layout)
    
    def _setup_plot_section(self, parent_layout: QVBoxLayout):
        """Set up the plot display section."""
        # Web view for displaying the plot
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(400)  # Increased since settings are compact
        self.web_view.setMinimumWidth(600)  # Increased minimum width
        
        # Set maximum size to prevent texture overflow
        self.web_view.setMaximumSize(16384, 16384)
        
        # Initial message
        initial_html = """
        <html>
        <body style="background-color: #2b2b2b; color: #ffffff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
            <div style="text-align: center;">
                <h3>Flow Cytometry Visualization</h3>
                <p>Configure options and generate plot to display visualization here.</p>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(initial_html)
        
        parent_layout.addWidget(self.web_view)
    
    def _setup_configuration_section(self, parent_layout: QVBoxLayout):
        """Set up the configuration section with mode dropdown and 3 columns."""
        config_group = QGroupBox("Settings")
        # Removed fixed height to allow dropdowns to expand properly
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)  # Further increased spacing to use more room
        config_layout.setContentsMargins(15, 15, 15, 15)  # Increased margins to use more room
        
        # Main layout with 3 columns
        main_layout = QHBoxLayout()
        main_layout.setSpacing(25)  # Increased spacing between columns
        
        # Left section: Config and Covariates
        left_section = QVBoxLayout()
        left_section.setSpacing(10)
        
        # Top row: Mode dropdown spanning the left section
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        mode_label = QLabel("Mode:")
        mode_label.setFixedWidth(50)
        mode_layout.addWidget(mode_label)
        
        self.plot_mode_combo = QComboBox()
        self.plot_mode_combo.addItems(["Standard Plotting", "Time Course"])
        self.plot_mode_combo.setCurrentText("Standard Plotting")
        self.plot_mode_combo.currentTextChanged.connect(self._on_plot_mode_changed)
        self.plot_mode_combo.activated.connect(self._on_plot_mode_activated)
        self._configure_combo_box_view(self.plot_mode_combo)
        mode_layout.addWidget(self.plot_mode_combo)
        
        left_section.addLayout(mode_layout)
        
        # Bottom row: Config and Covariates columns
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        
        # Column 1: Config
        config_column = QVBoxLayout()
        config_column.setSpacing(12)  # Increased spacing between elements
        config_column.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Plot type
        plot_type_layout = QHBoxLayout()
        plot_type_layout.setSpacing(8)
        type_label = QLabel("Type:")
        type_label.setFixedWidth(50)
        plot_type_layout.addWidget(type_label)
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["bar", "scatter", "box", "line", "histogram"])
        self.plot_type_combo.setCurrentText("line")
        self.plot_type_combo.currentTextChanged.connect(self._on_option_changed)
        self._configure_combo_box_view(self.plot_type_combo)
        plot_type_layout.addWidget(self.plot_type_combo)
        config_column.addLayout(plot_type_layout)
        
        # X-axis
        x_axis_layout = QHBoxLayout()
        x_axis_layout.setSpacing(8)
        x_label = QLabel("X:")
        x_label.setFixedWidth(50)
        x_axis_layout.addWidget(x_label)
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.addItem("Auto-detect")
        self.x_axis_combo.currentTextChanged.connect(self._on_option_changed)
        self._configure_combo_box_view(self.x_axis_combo)
        x_axis_layout.addWidget(self.x_axis_combo)
        config_column.addLayout(x_axis_layout)
        
        # Y-axis
        y_axis_layout = QHBoxLayout()
        y_axis_layout.setSpacing(8)
        y_label = QLabel("Y:")
        y_label.setFixedWidth(50)
        y_axis_layout.addWidget(y_label)
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.addItem("Auto-detect")
        self.y_axis_combo.currentTextChanged.connect(self._on_option_changed)
        self._configure_combo_box_view(self.y_axis_combo)
        y_axis_layout.addWidget(self.y_axis_combo)
        config_column.addLayout(y_axis_layout)
        
        bottom_row.addLayout(config_column)
        
        # Column 2: Covariates/Time
        covariates_column = QVBoxLayout()
        covariates_column.setSpacing(12)  # Increased spacing between elements
        covariates_column.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Tissue filter
        tissue_layout = QHBoxLayout()
        tissue_layout.setSpacing(8)
        tissue_label = QLabel("Tissue:")
        tissue_label.setFixedWidth(50)
        tissue_layout.addWidget(tissue_label)
        self.tissue_filter_combo = QComboBox()
        self.tissue_filter_combo.addItem("All")
        self.tissue_filter_combo.setEnabled(False)
        self.tissue_filter_combo.currentTextChanged.connect(self._on_option_changed)
        self._configure_combo_box_view(self.tissue_filter_combo)
        tissue_layout.addWidget(self.tissue_filter_combo)
        covariates_column.addLayout(tissue_layout)
        
        # Time filter
        time_layout = QHBoxLayout()
        time_layout.setSpacing(8)
        time_label = QLabel("Time:")
        time_label.setFixedWidth(50)
        time_layout.addWidget(time_label)
        self.time_filter_combo = QComboBox()
        self.time_filter_combo.addItem("All")
        self.time_filter_combo.setEnabled(False)
        self.time_filter_combo.currentTextChanged.connect(self._on_option_changed)
        self._configure_combo_box_view(self.time_filter_combo)
        time_layout.addWidget(self.time_filter_combo)
        covariates_column.addLayout(time_layout)
        
        # Time course strategy
        strategy_layout = QHBoxLayout()
        strategy_layout.setSpacing(8)
        strategy_label = QLabel("Strategy:")
        strategy_label.setFixedWidth(50)
        strategy_layout.addWidget(strategy_label)
        self.timecourse_strategy_combo = QComboBox()
        self.timecourse_strategy_combo.addItems(["By Group", "By Time"])
        self.timecourse_strategy_combo.setCurrentText("By Group")
        self.timecourse_strategy_combo.currentTextChanged.connect(self._on_option_changed)
        self._configure_combo_box_view(self.timecourse_strategy_combo)
        strategy_layout.addWidget(self.timecourse_strategy_combo)
        covariates_column.addLayout(strategy_layout)
        
        bottom_row.addLayout(covariates_column)
        
        left_section.addLayout(bottom_row)
        main_layout.addLayout(left_section)
        
        # Add stretch to center the custom axis column
        main_layout.addStretch(1)
        
        # Column 3: Custom Axis (centered with mode dropdown)
        custom_column = QVBoxLayout()
        custom_column.setSpacing(12)  # Increased spacing between elements
        custom_column.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add spacer to align Custom Axes checkbox with Mode dropdown
        custom_column.addSpacing(8)  # Reduced spacing to align with Mode
        
        # Custom axes toggle (centered with Mode dropdown)
        self.use_custom_axes_checkbox = QCheckBox("Custom Axes")
        self.use_custom_axes_checkbox.toggled.connect(self._on_custom_axes_toggled)
        custom_column.addWidget(self.use_custom_axes_checkbox)
        
        # Custom X-axis
        custom_x_layout = QHBoxLayout()
        custom_x_layout.setSpacing(8)
        custom_x_label = QLabel("Custom X:")
        custom_x_label.setFixedWidth(50)
        custom_x_layout.addWidget(custom_x_label)
        self.custom_x_axis_combo = QComboBox()
        self.custom_x_axis_combo.addItem("Select...")
        self.custom_x_axis_combo.setEnabled(False)
        self.custom_x_axis_combo.currentTextChanged.connect(self._on_option_changed)
        self._configure_combo_box_view(self.custom_x_axis_combo)
        custom_x_layout.addWidget(self.custom_x_axis_combo)
        custom_column.addLayout(custom_x_layout)
        
        # Custom Y-axis
        custom_y_layout = QHBoxLayout()
        custom_y_layout.setSpacing(8)
        custom_y_label = QLabel("Custom Y:")
        custom_y_label.setFixedWidth(50)
        custom_y_layout.addWidget(custom_y_label)
        self.custom_y_axis_combo = QComboBox()
        self.custom_y_axis_combo.addItem("Select...")
        self.custom_y_axis_combo.setEnabled(False)
        self.custom_y_axis_combo.currentTextChanged.connect(self._on_option_changed)
        self._configure_combo_box_view(self.custom_y_axis_combo)
        custom_y_layout.addWidget(self.custom_y_axis_combo)
        custom_column.addLayout(custom_y_layout)
        
        # Add spacer to align Update button with Y and Strategy fields
        custom_column.addSpacing(8)
        
        # Update button (centered with Y and Strategy fields)
        update_button = QPushButton("Update")
        update_button.clicked.connect(self._update_plot)
        custom_column.addWidget(update_button)
        
        main_layout.addLayout(custom_column)
        
        config_layout.addLayout(main_layout)
        
        config_group.setLayout(config_layout)
        parent_layout.addWidget(config_group)
    
    def _setup_buttons(self, parent_layout: QVBoxLayout):
        """Set up the dialog buttons."""
        button_layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel("Ready")
        button_layout.addWidget(self.status_label)
        
        # Add spacer to push buttons to the right
        button_layout.addStretch()
        
        # Open in browser button
        self.open_browser_button = QPushButton("Open in Browser")
        self.open_browser_button.clicked.connect(self._open_in_browser)
        self.open_browser_button.setEnabled(False)
        button_layout.addWidget(self.open_browser_button)
        
        # Update plot button (moved to config section)
        # self.update_button is now in the configuration section
        
        # Save button
        self.save_button = QPushButton("Save Plot")
        self.save_button.clicked.connect(self._save_visualization)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        parent_layout.addLayout(button_layout)
    
    def _analyze_data(self):
        """Analyze the CSV data to populate options."""
        try:
            if not self.csv_path or not self.csv_path.exists():
                return
            
            # Use the proper parsing logic
            self.df, _ = load_and_parse_df(self.csv_path)
            
            if self.df is not None and not self.df.empty:
                self._populate_column_options()
                
        except Exception as e:
            logger.error(f"Failed to analyze data: {e}")
    
    def _populate_column_options(self):
        """Populate the column selection combos."""
        if self.df is None or self.df.empty:
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
        categorical_columns = self._identify_categorical_columns()
        summary_metrics = self._identify_summary_metrics()
        
        # Populate X-axis with categorical columns (priority for 'Group')
        x_columns = []
        if 'Group' in categorical_columns:
            x_columns.append('Group')
        x_columns.extend([col for col in categorical_columns if col != 'Group'])
        
        for col in x_columns:
            self.x_axis_combo.addItem(col)
        
        # Set default X-axis - prefer time columns for timecourse visualization
        time_columns = [col for col in categorical_columns if self._is_time_column(col)]
        if time_columns:
            # Find the best time column (prefer 'Time' if available)
            best_time_col = None
            for col in time_columns:
                if col.lower() == 'time':
                    best_time_col = col
                    break
            if not best_time_col:
                best_time_col = time_columns[0]
            self.x_axis_combo.setCurrentText(best_time_col)
            # Auto-enable time course mode when time columns are detected
            if self.time_course_checkbox:
                self.time_course_checkbox.setChecked(True)
        elif 'Group' in categorical_columns:
            self.x_axis_combo.setCurrentText('Group')
        elif categorical_columns:
            self.x_axis_combo.setCurrentText(categorical_columns[0])
        
        # Populate Y-axis with summary metrics
        for metric in summary_metrics:
            self.y_axis_combo.addItem(metric)
        
        # Add ALL columns to custom x-axis and y-axis dropdowns for advanced users
        for col in self.df.columns:
            self.custom_x_axis_combo.addItem(col)
            self.custom_y_axis_combo.addItem(col)
        
        # Set default Y-axis to 'Freq. of Parent' if available
        if 'Freq. of Parent' in summary_metrics:
            self.y_axis_combo.setCurrentText('Freq. of Parent')
        elif summary_metrics:
            self.y_axis_combo.setCurrentText(summary_metrics[0])
        else:
            # Fallback: look for any frequency column
            freq_cols = [col for col in self.df.columns if 'freq' in col.lower()]
            if freq_cols:
                # Add the first frequency column as a custom option
                self.y_axis_combo.addItem(freq_cols[0])
                self.y_axis_combo.setCurrentText(freq_cols[0])
                logger.info(f"Using fallback frequency column: {freq_cols[0]}")
            else:
                # Last resort: use first non-metadata column
                metadata_cols = ['SampleID', 'Group', 'Animal', 'Well', 'Time', 'Replicate', 'Tissue']
                non_metadata_cols = [col for col in self.df.columns if col not in metadata_cols]
                if non_metadata_cols:
                    self.y_axis_combo.addItem(non_metadata_cols[0])
                    self.y_axis_combo.setCurrentText(non_metadata_cols[0])
                    logger.info(f"Using fallback column: {non_metadata_cols[0]}")
        
        # Populate covariates options
        self._populate_covariates_options()
    
    def _identify_summary_metrics(self) -> List[str]:
        """Identify summary metrics in the dataframe."""
        if self.df is None:
            return []
        
        summary_metrics = []
        
        for keyword in KEYWORDS:
            # Find columns that contain this keyword
            matching_cols = [col for col in self.df.columns if keyword.lower() in col.lower()]
            if matching_cols:
                # Add the keyword as a metric type (include both pure metrics and subpopulations)
                summary_metrics.append(keyword)
        
        # Also add any frequency columns that contain "Freq. of Parent" pattern
        freq_parent_cols = [col for col in self.df.columns if 'freq. of parent' in col.lower()]
        if freq_parent_cols and 'Freq. of Parent' not in summary_metrics:
            summary_metrics.append('Freq. of Parent')
        
        return summary_metrics
    
    def _identify_categorical_columns(self) -> List[str]:
        """Identify categorical columns suitable for X-axis."""
        if self.df is None:
            return []
        
        categorical_columns = []
        
        # Common categorical column names (excluding Tissue and SampleID)
        categorical_keywords = [
            'group', 'animal', 'well', 'time', 'replicate',
            'treatment', 'condition', 'experiment', 'batch', 'day', 'week',
            'mouse', 'rat', 'subject', 'patient', 'donor'
        ]
        
        for col in self.df.columns:
            col_lower = col.lower()
            
            # Skip Tissue and SampleID columns (they will be used as covariates)
            if col_lower in ['tissue', 'sampleid', 'sample_id']:
                continue
            
            # Check if column name contains categorical keywords
            if any(keyword in col_lower for keyword in categorical_keywords):
                categorical_columns.append(col)
                continue
            
            # Check if column contains mostly string/non-numeric data
            if self.df[col].dtype == 'object':
                # Check if it's not a metric column (doesn't contain metric keywords)
                is_metric = any(keyword.lower() in col_lower for keyword in KEYWORDS.keys())
                if not is_metric:
                    categorical_columns.append(col)
                continue
            
            # Check if numeric column has limited unique values (likely categorical)
            if self.df[col].dtype in ['int64', 'float64']:
                unique_ratio = len(self.df[col].unique()) / len(self.df)
                if unique_ratio < 0.1:  # Less than 10% unique values
                    categorical_columns.append(col)
        
        return categorical_columns
    
    def _populate_covariates_options(self):
        """Populate the covariates filter options."""
        if self.df is None or self.df.empty:
            return
        
        # Populate tissue filter
        if 'Tissue' in self.df.columns:
            tissue_values = sorted(self.df['Tissue'].dropna().unique())
            self.tissue_filter_combo.clear()
            self.tissue_filter_combo.addItem("All Tissues")
            for tissue in tissue_values:
                self.tissue_filter_combo.addItem(str(tissue))
            self.tissue_filter_combo.setEnabled(True)
        
        # Populate time filter
        if 'Time' in self.df.columns:
            time_values = sorted(self.df['Time'].dropna().unique())
            self.time_filter_combo.clear()
            self.time_filter_combo.addItem("All Times")
            for time_val in time_values:
                self.time_filter_combo.addItem(str(time_val))
            self.time_filter_combo.setEnabled(True)
    
    def _configure_combo_box_view(self, combo_box):
        """Configure the dropdown list view for better visibility and interaction."""
        from PySide6.QtWidgets import QSizePolicy
        
        # Set maximum visible items
        combo_box.setMaxVisibleItems(10)
        
        # Set minimum width to ensure dropdown is wide enough
        combo_box.setMinimumWidth(120)
        
        # Set size policy to allow expansion
        combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _on_custom_axes_toggled(self, checked: bool):
        """Handle custom axes checkbox toggle."""
        self.custom_x_axis_combo.setEnabled(checked)
        self.custom_y_axis_combo.setEnabled(checked)
        if checked:
            self.x_axis_combo.setEnabled(False)
            self.y_axis_combo.setEnabled(False)
        else:
            self.x_axis_combo.setEnabled(True)
            self.y_axis_combo.setEnabled(True)
    
    def _on_plot_mode_activated(self, index: int):
        """Handle plot mode dropdown activation."""
        try:
            mode = self.plot_mode_combo.itemText(index)
            logger.debug(f"Plot mode activated: {mode} at index {index}")
            print(f"DEBUG: Plot mode activated: {mode} at index {index}")
            self._on_plot_mode_changed(mode)
        except Exception as e:
            logger.error(f"Error handling plot mode activation: {e}")
            print(f"DEBUG: Error handling plot mode activation: {e}")
    

    
    def _on_plot_mode_changed(self, mode: str):
        """Handle plot mode dropdown change."""
        try:
            is_time_course = mode == "Time Course"
            
            # Enable/disable time course specific options
            self.timecourse_strategy_combo.setEnabled(is_time_course)
            
            if is_time_course:
                # When time course mode is enabled, set defaults for timecourse visualization
                # Set plot type to line
                if self.plot_type_combo:
                    self.plot_type_combo.setCurrentText("line")
                
                # Set strategy to "By Time" for vertically stacked plots
                if self.timecourse_strategy_combo:
                    self.timecourse_strategy_combo.setCurrentText("By Time")
                
                # Auto-select time column for x-axis if available
                if self.x_axis_combo and self.df is not None:
                    time_columns = [col for col in self.df.columns if self._is_time_column(col)]
                    if time_columns:
                        # Find the best time column (prefer 'Time' if available)
                        best_time_col = None
                        for col in time_columns:
                            if col.lower() == 'time':
                                best_time_col = col
                                break
                        if not best_time_col:
                            best_time_col = time_columns[0]
                        
                        # Set the x-axis to the time column
                        index = self.x_axis_combo.findText(best_time_col)
                        if index >= 0:
                            self.x_axis_combo.setCurrentIndex(index)
            else:
                # Standard plotting mode - reset to defaults
                if self.plot_type_combo:
                    self.plot_type_combo.setCurrentText("line")
                if self.timecourse_strategy_combo:
                    self.timecourse_strategy_combo.setCurrentText("By Group")
            
            # Always trigger the regular option change handler
            self._on_option_changed()
            
        except Exception as e:
            logger.error(f"Error handling plot mode change: {e}")
            self._show_error_message(f"Error updating plot mode: {str(e)}")

    def _on_time_course_toggled(self, checked: bool):
        """Handle time course mode checkbox toggle (legacy - now handled by dropdown)."""
        # This method is kept for backward compatibility but the functionality
        # is now handled by the plot mode dropdown
        pass
    
    def _on_option_changed(self):
        """Handle any option change and trigger plot update."""
        if self.csv_path and self.df is not None:
            # Use a small delay to avoid too many rapid updates
            from PySide6.QtCore import QTimer
            if hasattr(self, '_update_timer'):
                self._update_timer.stop()
            else:
                self._update_timer = QTimer()
                self._update_timer.setSingleShot(True)
                self._update_timer.timeout.connect(self._update_plot)
            
            self._update_timer.start(300)  # 300ms delay
    
    def _apply_options(self, options):
        """Apply options to the UI."""
        try:
            if self.plot_type_combo and options.plot_type:
                index = self.plot_type_combo.findText(options.plot_type)
                if index >= 0:
                    self.plot_type_combo.setCurrentIndex(index)
            
            if self.x_axis_combo and options.x_axis:
                # Check if it's a summary metric or custom column
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
                    # No need to set use_custom_axes_checkbox here, as it's for both
                else:
                    # Try custom Y-axis
                    if self.custom_y_axis_combo:
                        index = self.custom_y_axis_combo.findText(options.y_axis)
                        if index >= 0:
                            self.custom_y_axis_combo.setCurrentIndex(index)
                            # No need to set use_custom_axes_checkbox here, as it's for both
            
            if self.plot_mode_combo:
                mode = "Time Course" if options.time_course_mode else "Standard Plotting"
                index = self.plot_mode_combo.findText(mode)
                if index >= 0:
                    self.plot_mode_combo.setCurrentIndex(index)
            
            # Apply timecourse strategy
            if self.timecourse_strategy_combo and hasattr(options, 'time_course_strategy'):
                # Map old strategy names to new simplified names
                strategy_mapping = {
                    "Faceted by Group": "By Group",
                    "Faceted by Cell Type": "By Time",
                    "Interactive Dashboard": "By Group",
                    "Hierarchical View": "By Time"
                }
                strategy = options.time_course_strategy
                if strategy in strategy_mapping:
                    strategy = strategy_mapping[strategy]
                
                index = self.timecourse_strategy_combo.findText(strategy)
                if index >= 0:
                    self.timecourse_strategy_combo.setCurrentIndex(index)
            
            # Apply covariates
            if self.tissue_filter_combo and hasattr(options, 'tissue_filter'):
                if options.tissue_filter:
                    index = self.tissue_filter_combo.findText(options.tissue_filter)
                    if index >= 0:
                        self.tissue_filter_combo.setCurrentIndex(index)
                else:
                    # Set to "All Tissues"
                    index = self.tissue_filter_combo.findText("All Tissues")
                    if index >= 0:
                        self.tissue_filter_combo.setCurrentIndex(index)
            
            if self.time_filter_combo and hasattr(options, 'time_filter'):
                if options.time_filter:
                    index = self.time_filter_combo.findText(options.time_filter)
                    if index >= 0:
                        self.time_filter_combo.setCurrentIndex(index)
                else:
                    # Set to "All Times"
                    index = self.time_filter_combo.findText("All Times")
                    if index >= 0:
                        self.time_filter_combo.setCurrentIndex(index)
                

                
        except Exception as e:
            logger.warning(f"Failed to apply options: {e}")
    
    def _get_current_options(self):
        """Get the current options from the UI."""
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
            tissue_value = self.tissue_filter_combo.currentText()
            tissue_filter = None if tissue_value in ["All Tissues", ""] else tissue_value
        
        time_filter = None
        if self.time_filter_combo and self.time_filter_combo.isEnabled():
            time_value = self.time_filter_combo.currentText()
            time_filter = None if time_value in ["All Times", ""] else time_value
        
        from flowproc.presentation.gui.views.dialogs.visualization_options_dialog import VisualizationOptions
        
        return VisualizationOptions(
            plot_type=self.plot_type_combo.currentText(),
            x_axis=x_axis,
            y_axis=y_axis,
            time_course_mode=self.plot_mode_combo.currentText() == "Time Course",
            time_course_strategy=self.timecourse_strategy_combo.currentText(),
            width=800,  # Default width in code
            height=500,  # Default height in code
            tissue_filter=tissue_filter,
            time_filter=time_filter
        )
    
    def set_options(self, options):
        """Set the visualization options and regenerate plot."""
        self.options = options
        if self.csv_path and self.options:
            self._apply_options(options)
            self._generate_plot()
    
    def _generate_plot(self):
        """Generate the plot based on current options."""
        try:
            if not self.csv_path or not self.options:
                self.status_label.setText("Error: Missing CSV path or options")
                return
            
            # Dimensions are handled in code only - using defaults
            self.options.width = 800
            self.options.height = 500
            
            # Create temporary HTML file
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                self.temp_html_file = Path(tmp_file.name)
            
            # Show progress for large datasets
            if self.df is not None and len(self.df) > 1000:
                self.status_label.setText("Processing large dataset - applying optimizations...")
            
            # Check if time axis is selected and enable timecourse mode automatically
            time_course_mode = self.options.time_course_mode
            if self.options.x_axis and self._is_time_column(self.options.x_axis):
                time_course_mode = True
                logger.info(f"Auto-enabling timecourse mode for time column: {self.options.x_axis}")
            
            # Generate plot using simple visualizer
            logger.info(f"Generating plot with dimensions: width={self.options.width}, height={self.options.height}")
            logger.info(f"Plot options: x={self.options.x_axis}, y={self.options.y_axis}, plot_type={self.options.plot_type}, time_course_mode={time_course_mode}")
            
            if time_course_mode:
                # For time course mode, use the selected strategy
                value_col = self.options.y_axis
                time_col = self.options.x_axis  # Use selected x-axis as time column
                strategy = self.timecourse_strategy_combo.currentText()
                logger.info(f"Time course mode with strategy: {strategy}, value_col: {value_col}, time_col: {time_col}")
                
                # Show progress for time course plots
                if self.df is not None and len(self.df) > 5000:
                    self.status_label.setText("Generating time course plot - processing multiple cell types...")
                
                # Simplified timecourse strategies
                if strategy == "By Group":
                    # Faceted by group
                    fig = time_plot_faceted(
                        data=self.csv_path,
                        time_col=time_col,  # Use selected time column
                        value_col=value_col,
                        facet_by="Group",
                        save_html=self.temp_html_file
                    )
                elif strategy == "By Time":
                    # Faceted by cell type (time on x-axis)
                    fig = time_plot_faceted(
                        data=self.csv_path,
                        time_col=time_col,  # Use selected time column
                        value_col=value_col,
                        facet_by="Cell Type",
                        save_html=self.temp_html_file
                    )
                else:
                    # Fallback to standard
                    fig = time_plot(
                        data=self.csv_path,
                        time_col=time_col,  # Use selected time column
                        value_col=value_col,
                        save_html=self.temp_html_file
                    )
            else:
                # Get x and y columns (None for auto-detect)
                x_col = self.options.x_axis
                y_col = self.options.y_axis
                
                logger.info(f"Standard plot mode with x_col: {x_col}, y_col: {y_col}")
                fig = plot(
                    data=self.csv_path,
                    x=x_col,
                    y=y_col,
                    plot_type=self.options.plot_type,
                    save_html=self.temp_html_file
                )
            
            # Log the actual figure dimensions
            logger.info(f"Generated figure dimensions: width={fig.layout.width}, height={fig.layout.height}")
            
            # Load in web view
            from PySide6.QtCore import QUrl
            file_url = QUrl.fromLocalFile(str(self.temp_html_file))
            
            # Log device pixel ratio for debugging
            device_pixel_ratio = self.web_view.devicePixelRatio()
            logger.info(f"Web view device pixel ratio: {device_pixel_ratio}")
            
            self.web_view.load(file_url)
            
            # Enable buttons
            self.open_browser_button.setEnabled(True)
            self.save_button.setEnabled(True)
            
            # Update status
            self.status_label.setText("Plot generated successfully")
            
            # Emit signal
            self.plot_generated.emit()
            
            logger.info("Plot generated successfully")
            
        except Exception as e:
            logger.error(f"Failed to generate plot: {e}")
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
            self.status_label.setText(f"Error: {str(e)}")
    
    def _is_time_column(self, column_name: str) -> bool:
        """Check if a column name represents time data."""
        if not column_name:
            return False
        
        # Check for common time-related patterns
        time_patterns = [
            'time', 'day', 'hour', 'minute', 'second', 'date',
            'week', 'month', 'year', 'period', 'duration'
        ]
        
        column_lower = column_name.lower()
        
        # Check if column name contains time-related keywords
        for pattern in time_patterns:
            if pattern in column_lower:
                return True
        
        # Check for specific time formats like "Day X", "d3", etc.
        import re
        time_formats = [
            r'day\s*\d+',  # Day 1, Day 2, etc.
            r'd\d+',       # d1, d2, d3, etc.
            r't\d+',       # t1, t2, t3, etc.
            r'hour\s*\d+', # Hour 1, Hour 2, etc.
            r'h\d+',       # h1, h2, h3, etc.
        ]
        
        for pattern in time_formats:
            if re.search(pattern, column_lower):
                return True
        
        return False
    
    # Removed _configure_options method - no longer needed with inline configuration
    
    def _update_plot(self):
        """Update the plot with current options from UI."""
        try:
            # Get current options from UI
            self.options = self._get_current_options()
            self.status_label.setText("Updating plot...")
            self._generate_plot()
        except Exception as e:
            QMessageBox.warning(self, "Update Error", f"Failed to update plot: {str(e)}")
    
    def _open_in_browser(self):
        """Open the current plot in the default browser."""
        if self.temp_html_file and self.temp_html_file.exists():
            import webbrowser
            webbrowser.open(f"file://{self.temp_html_file}")
    
    def _save_visualization(self):
        """Save the current visualization to a user-selected location."""
        if not self.temp_html_file or not self.temp_html_file.exists():
            QMessageBox.warning(self, "No Plot", "Please generate a plot first.")
            return
        
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            str(self.csv_path.parent / f"{self.csv_path.stem}_plot.html") if self.csv_path else "plot.html",
            "HTML Files (*.html)"
        )
        
        if file_path:
            import shutil
            shutil.copy2(self.temp_html_file, file_path)
            QMessageBox.information(self, "Saved", f"Plot saved to {file_path}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Clean up temporary file
        if self.temp_html_file and self.temp_html_file.exists():
            try:
                self.temp_html_file.unlink()
                logger.info(f"Cleaned up temporary file: {self.temp_html_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")
        event.accept()

    def resizeEvent(self, event):
        """Handle dialog resize event to update plot display."""
        super().resizeEvent(event)
        # Update web view size if needed
        if hasattr(self, 'web_view'):
            # Ensure web view uses available space efficiently
            self.web_view.setMinimumHeight(max(300, self.height() // 2))
    
    def _generate_placeholder_plot(self):
        """Generate a basic placeholder plot with default options."""
        try:
            if self.df is None or self.df.empty:
                self._show_error_message("No data available for visualization")
                return
            
            # Create default options object
            from flowproc.presentation.gui.views.dialogs.visualization_options_dialog import VisualizationOptions
            
            # Check if we have time columns for timecourse visualization
            time_columns = [col for col in self.df.columns if self._is_time_column(col)]
            if time_columns:
                # Default to timecourse mode with line plots
                best_time_col = None
                for col in time_columns:
                    if col.lower() == 'time':
                        best_time_col = col
                        break
                if not best_time_col:
                    best_time_col = time_columns[0]
                
                default_options = VisualizationOptions(
                    plot_type='line',
                    x_axis=best_time_col,
                    y_axis=None,  # Auto-detect
                    time_course_mode=True,
                    time_course_strategy="Faceted by Cell Type",
                    width=800,
                    height=1200
                )
            else:
                # Standard defaults for non-timecourse data
                default_options = VisualizationOptions(
                    plot_type='line',
                    x_axis='Group' if 'Group' in self.df.columns else None,
                    y_axis=None,  # Auto-detect
                    time_course_mode=False,
                    width=800,
                    height=1200
                )
            
            # Set the options and apply them
            self.options = default_options
            self._apply_options(default_options)
            
            # Generate the plot
            self._generate_plot()
            
        except Exception as e:
            logger.error(f"Failed to generate placeholder plot: {e}")
            self._show_error_message(f"Failed to generate placeholder plot: {str(e)}")
    
    def _show_error_message(self, message: str):
        """Show an error message in the web view."""
        error_html = f"""
        <html>
        <body style="background-color: #2b2b2b; color: #ffffff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
            <div style="text-align: center;">
                <h3 style="color: #ff6b6b;">Visualization Error</h3>
                <p>{message}</p>
                <p>Please check your data and try again.</p>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(error_html) 