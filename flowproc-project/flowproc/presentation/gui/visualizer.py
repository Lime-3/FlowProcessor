"""
Visualizer module for flow cytometry GUI.
"""

import logging
import traceback
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, 
    QLabel, QMessageBox, QFileDialog, QSizePolicy, QDialog, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

from ...config import AUTO_PARSE_GROUPS, USER_REPLICATES, USER_GROUP_LABELS
from ...domain.visualization.visualize import visualize_data
from ...domain.visualization.themes import VisualizationThemes
from ...domain.parsing import load_and_parse_df
from ...core.constants import KEYWORDS
from ...logging_config import setup_logging
from .config_handler import load_last_output_dir, save_last_output_dir

logger = logging.getLogger(__name__)

def save_plot_as_image(fig: go.Figure, parent_widget: Optional[QWidget], metric: str = "plot") -> None:
    """Save the Plotly figure as a PNG image."""
    if not isinstance(parent_widget, QWidget):
        logger.error("Parent widget must be a QWidget, got %s", type(parent_widget))
        return
    
    # Create a clean default filename without hash
    default_filename = f"flowproc_{metric.replace(' ', '_').replace('|', '_')}.png"
    
    # Use last output directory from config, fallback to Desktop
    try:
        default_dir = load_last_output_dir()
    except Exception as e:
        logger.warning(f"Failed to load last output directory: {e}")
        default_dir = str(Path.home() / "Desktop")
    
    default_path = Path(default_dir) / default_filename
    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Save Plot as Image",
        str(default_path),
        "PNG Files (*.png);;JPEG Files (*.jpg)"
    )
    if file_path:
        try:
            pio.write_image(fig, file_path, scale=6)  # 600 DPI equivalent
            logger.info(f"Plot saved as image: {file_path}")
            
            # Save the directory for next time
            try:
                save_last_output_dir(str(Path(file_path).parent))
            except Exception as e:
                logger.warning(f"Failed to save output directory: {e}")
            
            QMessageBox.information(parent_widget, "Success", f"Plot saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save plot: {str(e)}")
            QMessageBox.critical(parent_widget, "Error", f"Failed to save plot: {str(e)}")

class VisualizationDialog(QDialog):
    """Enhanced dialog for visualization with theme selection and offline HTML embedding."""
    
    def __init__(self, parent: Optional[QWidget], csv_path: Path, metric_name: str, 
                 time_course_mode: bool, user_group_labels: Optional[List[str]] = None):
        super().__init__(parent)
        self.csv_path = csv_path
        self.metric_name = metric_name  # Renamed from metric to avoid Qt conflict
        self.time_course_mode = time_course_mode
        self.user_group_labels = user_group_labels
        self.current_fig: Optional[go.Figure] = None
        self.temp_html: Optional[Path] = None
        self.themes = VisualizationThemes()
        self.available_tissues: List[str] = []
        self.selected_tissue: Optional[str] = None
        self.available_subpopulations: List[str] = []
        self.selected_subpopulation: Optional[str] = None
        
        self.setWindowTitle(f"Visualization Preview - {metric_name}")
        self.setModal(True)
        self.resize(1400, 500)  # Increased width to accommodate metric selector
        self.setMinimumSize(1200, 400)  # Increased minimum width
        
        # Center the dialog on the screen
        self.setGeometry(
            (self.screen().size().width() - self.width()) // 2,
            (self.screen().size().height() - self.height()) // 2,
            self.width(),
            self.height()
        )
        
        self._load_available_tissues()
        self._load_available_subpopulations()
        self._setup_ui()
        self._setup_styling()
        self._setup_web_view_signals()
        self._generate_plot()
        
    def _load_available_tissues(self):
        """Load available tissues from the CSV data."""
        try:
            # Load and parse the data to get available tissues
            df, _ = load_and_parse_df(self.csv_path)
            if 'Tissue' in df.columns:
                self.available_tissues = sorted(df['Tissue'].unique().tolist())
                logger.debug(f"Available tissues: {self.available_tissues}")
            else:
                self.available_tissues = []
                logger.debug("No tissue column found in data")
        except Exception as e:
            logger.warning(f"Failed to load available tissues: {e}")
            self.available_tissues = []
    
    def _load_available_subpopulations(self):
        """Load available subpopulations from the CSV data."""
        try:
            # Load and parse the data to get available subpopulations
            df, _ = load_and_parse_df(self.csv_path)
            
            # For time-course mode, we need to process the data to get subpopulations
            if self.time_course_mode:
                # Get the metric columns that contain subpopulation information
                # Filter to only include columns that match the selected metric
                metric_cols = []
                if self.metric_name:
                    # Look for columns that contain the metric name
                    for col in df.columns:
                        if '|' in col and self.metric_name in col:
                            metric_cols.append(col)
                else:
                    # If no specific metric, include all columns with pipes
                    metric_cols = [col for col in df.columns if '|' in col]
                
                if metric_cols:
                    # Extract subpopulation names from metric columns
                    subpopulations = set()
                    for col in metric_cols:
                        # Extract the part before the pipe (subpopulation name)
                        # Use the same logic as the aggregation process
                        subpop_name = col.split(' | ')[0].strip() if ' | ' in col else col.strip()
                        subpopulations.add(subpop_name)
                    
                    self.available_subpopulations = sorted(list(subpopulations))
                    logger.debug(f"Available subpopulations from GUI for metric '{self.metric_name}': {self.available_subpopulations}")
                else:
                    self.available_subpopulations = []
                    logger.debug(f"No subpopulation columns found in data for metric '{self.metric_name}'")
            else:
                self.available_subpopulations = []
                logger.debug("Not in time-course mode, skipping subpopulation loading")
        except Exception as e:
            logger.warning(f"Failed to load available subpopulations: {e}")
            self.available_subpopulations = []
        
    def _setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Controls group
        controls_group = QGroupBox("Plot Controls")
        controls_layout = QHBoxLayout(controls_group)  # Changed to horizontal layout
        controls_layout.setSpacing(12)  # Add spacing between controls
        
        # Theme selection with wider combo box
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumWidth(180)  # Increased width for better readability
        available_themes = self.themes.get_available_themes()
        for theme in available_themes:
            self.theme_combo.addItem(theme.title(), theme)
        self.theme_combo.setCurrentText("Default")  # Changed default to Default theme
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        
        # Metric selection
        metric_label = QLabel("Metric:")
        self.metric_combo = QComboBox()
        self.metric_combo.setMinimumWidth(160)  # Width for metric names
        # Add all available metrics from KEYWORDS
        for metric in KEYWORDS.keys():
            self.metric_combo.addItem(metric, metric)
        # Set current metric
        current_index = self.metric_combo.findText(self.metric_name)
        if current_index >= 0:
            self.metric_combo.setCurrentIndex(current_index)
        self.metric_combo.currentTextChanged.connect(self._on_metric_changed)
        
        # Tissue filter (only show if multiple tissues are available)
        if len(self.available_tissues) > 1:
            tissue_label = QLabel("Tissue:")
            self.tissue_combo = QComboBox()
            self.tissue_combo.setMinimumWidth(140)
            self.tissue_combo.addItem("All Tissues", None)
            for tissue in self.available_tissues:
                self.tissue_combo.addItem(tissue, tissue)
            self.tissue_combo.currentTextChanged.connect(self._on_tissue_changed)
            
            controls_layout.addWidget(theme_label)
            controls_layout.addWidget(self.theme_combo)
            controls_layout.addWidget(metric_label)
            controls_layout.addWidget(self.metric_combo)
            controls_layout.addWidget(tissue_label)
            controls_layout.addWidget(self.tissue_combo)
        else:
            # Single tissue or no tissue data - show theme and metric
            controls_layout.addWidget(theme_label)
            controls_layout.addWidget(self.theme_combo)
            controls_layout.addWidget(metric_label)
            controls_layout.addWidget(self.metric_combo)
        
        # Population filter (only show in time-course mode if multiple populations are available)
        if self.time_course_mode and len(self.available_subpopulations) > 1:
            subpop_label = QLabel("Population:")
            self.subpop_combo = QComboBox()
            self.subpop_combo.setMinimumWidth(200)  # Increased width for longer population names
            self.subpop_combo.addItem("All Populations", None)
            for subpop in self.available_subpopulations:
                self.subpop_combo.addItem(subpop, subpop)
            self.subpop_combo.currentTextChanged.connect(self._on_subpopulation_changed)
            
            controls_layout.addWidget(subpop_label)
            controls_layout.addWidget(self.subpop_combo)
        
        # Buttons
        self.refresh_button = QPushButton("Refresh Plot")
        self.refresh_button.clicked.connect(self._generate_plot)
        self.refresh_button.setEnabled(False)  # Will be enabled after first plot
        
        self.save_button = QPushButton("Save Image")
        self.save_button.clicked.connect(self._save_plot)
        self.save_button.setEnabled(False)  # Will be enabled after first plot
        
        self.export_pdf_button = QPushButton("Export PDF")
        self.export_pdf_button.clicked.connect(self._export_to_pdf)
        self.export_pdf_button.setEnabled(False)  # Will be enabled after first plot
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        # Add stretch to push buttons to the right
        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.save_button)
        controls_layout.addWidget(self.export_pdf_button)
        controls_layout.addWidget(self.close_button)
        
        # Web view for plot display
        self.view = QWebEngineView()
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Configure web view settings for local file access
        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowGeolocationOnInsecureOrigins, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, True)
        
        # Add all components to main layout
        layout.addWidget(controls_group)
        layout.addWidget(self.view, stretch=1)
        
    def _setup_styling(self):
        """Apply custom styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F0F;
                color: #F0F0F0;
            }
            
            QGroupBox {
                border: 1px solid #303030;
                border-radius: 6px;
                margin-top: 0px;
                padding-top: 10px;
                font-weight: 600;
                color: #0064FF;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 8px;
                font-size: 14px;
            }
            
            QComboBox {
                background-color: #191919;
                color: #F0F0F0;
                border: 1px solid #303030;
                padding: 8px;
                border-radius: 4px;
                min-height: 30px;
            }
            
            QLabel {
                color: #F0F0F0;
                font-weight: 500;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #F0F0F0;
            }
            
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                min-height: 30px;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:disabled {
                background-color: #4A4A4A;
                color: #888888;
            }
            
            QPushButton#closeButton {
                background-color: #6c757d;
            }
            
            QPushButton#closeButton:hover {
                background-color: #5a6268;
            }
        """)
        
        # Apply specific styling to close button
        self.close_button.setObjectName("closeButton")
        
    def _setup_web_view_signals(self):
        """Set up web view signal connections."""
        self.view.page().loadFinished.connect(self._on_load_finished)
        
    def _on_load_finished(self, ok: bool) -> None:
        """Handle web view load finished event."""
        if ok:
            logger.info(f"Successfully loaded plot from {self.temp_html}")
            # Check if the page has content
            self.view.page().toHtml(lambda html: self._check_page_content(html))
        else:
            error_string = self.view.page().lastErrorString() or "Unknown error"
            logger.error(f"Failed to load plot from {self.temp_html}: {error_string}")
            QMessageBox.critical(self, "Load Error", f"Failed to load plot: {error_string}")
            
    def _check_page_content(self, html: str) -> None:
        """Check if the loaded page has the expected content."""
        if html and len(html) > 1000:  # Basic check for substantial content
            logger.info("Page loaded with substantial content")
        else:
            logger.warning("Page loaded but content seems minimal")
            # Show a simple message in the web view as fallback
            fallback_html = f"""
            <html>
            <body style="background-color: #0F0F0F; color: #F0F0F0; font-family: Arial; padding: 20px;">
                <h2>Plot Generated Successfully</h2>
                <p>Metric: {self.metric_name}</p>
                <p>File: {self.temp_html}</p>
                <p>If the plot is not visible, try refreshing or check the console for errors.</p>
            </body>
            </html>
            """
            self.view.setHtml(fallback_html)

    def _on_theme_changed(self, theme_name: str):
        """Handle theme selection change."""
        if self.current_fig is not None:
            self._generate_plot()
            
    def _on_metric_changed(self, metric_name: str):
        """Handle metric selection change."""
        self.metric_name = metric_name
        # Update dialog title to reflect new metric
        self.setWindowTitle(f"Visualization Preview - {metric_name}")
        # Reload available subpopulations for the new metric
        self._load_available_subpopulations()
        # Update population combo if it exists
        if hasattr(self, 'subpop_combo'):
            self.subpop_combo.clear()
            self.subpop_combo.addItem("All Populations", None)
            for subpop in self.available_subpopulations:
                self.subpop_combo.addItem(subpop, subpop)
        self._generate_plot()
            
    def _on_tissue_changed(self, tissue_name: str):
        """Handle tissue filter selection change."""
        if self.current_fig is not None:
            self._generate_plot()
            
    def _on_subpopulation_changed(self, subpopulation_name: str):
        """Handle subpopulation filter selection change."""
        if self.current_fig is not None:
            self._generate_plot()
            
    def _generate_plot(self):
        """Generate the plot with current settings."""
        try:
            # Get selected theme
            theme_name = self.theme_combo.currentData()
            
            # Get selected tissue filter (only if tissue combo exists)
            tissue_filter = None
            if hasattr(self, 'tissue_combo'):
                tissue_filter = self.tissue_combo.currentData()
            
            # Get selected subpopulation filter (only if subpop combo exists)
            subpopulation_filter = None
            if hasattr(self, 'subpop_combo'):
                subpopulation_filter = self.subpop_combo.currentData()
            
            # Create temporary HTML file for output
            if self.temp_html and self.temp_html.exists():
                try:
                    self.temp_html.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up old temp file: {e}")
            
            # Embed in QWebEngineView (offline HTML)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                self.temp_html = Path(tmp_file.name)
            
            # Use passed group labels if available, otherwise fall back to global labels
            group_labels_to_use = self.user_group_labels if self.user_group_labels else (USER_GROUP_LABELS if USER_GROUP_LABELS else None)
            
            # Generate visualization using the domain function
            # This already writes the HTML file with include_plotlyjs=True
            # Calculate dynamic width based on available space for better timecourse visualization
            # Get the available width from the web view
            available_width = self.view.width()
            if available_width <= 0:
                available_width = 800  # Fallback width if view not yet sized
            
            # Use the available width, but ensure it's reasonable
            plot_width = max(600, min(available_width - 100, 1200))  # Between 600 and 1200 pixels
            
            logger.info(f"Generating plot with parameters: csv_path={self.csv_path}, metric={self.metric_name}, theme={theme_name}, width={plot_width}")
            
            try:
                self.current_fig = visualize_data(
                    csv_path=self.csv_path,
                    output_html=self.temp_html,
                    metric=self.metric_name,  # Use the renamed attribute
                    width=plot_width,  # Dynamic width based on available space
                    height=300,  # Consistent height for all plot types
                    theme=theme_name,
                    time_course_mode=self.time_course_mode,
                    user_replicates=USER_REPLICATES if USER_REPLICATES else None,
                    auto_parse_groups=AUTO_PARSE_GROUPS,
                    user_group_labels=group_labels_to_use,
                    tissue_filter=tissue_filter, # Pass the selected tissue filter
                    subpopulation_filter=subpopulation_filter # Pass the selected subpopulation filter
                )
                logger.info("Plot generation completed successfully")
            except Exception as viz_error:
                logger.error(f"Visualization failed: {viz_error}")
                raise
            
            # Note: visualize_data already writes the HTML file, so we don't need to write it again
            
            # Verify file integrity
            if not self.temp_html.exists():
                raise ValueError(f"Plot file {self.temp_html} not created")
            
            file_size = self.temp_html.stat().st_size
            with open(self.temp_html, "rb") as fh:
                file_hash = hashlib.md5(fh.read()).hexdigest()
            logger.debug(f"Plot size: {file_size} bytes, MD5: {file_hash}")
            
            if not os.access(self.temp_html, os.R_OK):
                raise ValueError(f"Plot file {self.temp_html} not readable")
            
            # Load the plot in the web view
            self._load_plot()
            
            # Enable buttons after successful plot generation
            self.refresh_button.setEnabled(True)
            self.save_button.setEnabled(True)
            self.export_pdf_button.setEnabled(True)
            
        except Exception as e:
            logger.error(f"Failed to generate plot: {str(e)}")
            QMessageBox.critical(self, "Plot Generation Error", f"Failed to generate plot: {str(e)}")
            
    def _load_plot(self):
        """Load the plot in the web view."""
        if not self.temp_html or not self.temp_html.exists():
            logger.error("No temporary HTML file to load")
            return
            
        file_url = QUrl.fromLocalFile(str(self.temp_html.resolve()))
        logger.info(f"Loading URL: {file_url.toString()}")
        logger.info(f"HTML file exists: {self.temp_html.exists()}")
        logger.info(f"HTML file size: {self.temp_html.stat().st_size} bytes")
        
        # Debug: Check file content
        try:
            with open(self.temp_html, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"HTML content preview: {content[:200]}...")
                if 'plotly' not in content.lower():
                    logger.warning("Plotly not found in HTML content")
        except Exception as e:
            logger.error(f"Failed to read HTML content: {e}")
        
        # Add a small delay to ensure the file is fully written
        import time
        time.sleep(0.1)
        
        # Try loading with different approaches
        try:
            # First, try loading the file directly
            self.view.load(file_url)
            logger.info("Attempting to load file via URL")
        except Exception as e:
            logger.error(f"Failed to load file URL: {e}")
            # Fallback: read the HTML content and set it directly
            try:
                with open(self.temp_html, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                self.view.setHtml(html_content)
                logger.info("Loaded HTML content directly")
            except Exception as e2:
                logger.error(f"Failed to load HTML content directly: {e2}")
                # Show error message
                error_html = f"""
                <html>
                <body style="background-color: #0F0F0F; color: #F0F0F0; font-family: Arial; padding: 20px;">
                    <h2>Error Loading Plot</h2>
                    <p>Failed to load the visualization.</p>
                    <p>Error: {str(e)}</p>
                    <p>File: {self.temp_html}</p>
                    <p>File size: {self.temp_html.stat().st_size} bytes</p>
                </body>
                </html>
                """
                self.view.setHtml(error_html)
            
    def _save_plot(self):
        """Save the current plot as an image."""
        if self.current_fig is not None:
            save_plot_as_image(self.current_fig, self, self.metric_name)  # Use the renamed attribute
        else:
            QMessageBox.warning(self, "No Plot", "No plot available to save.")
    
    def _export_to_pdf(self, filename: str = "plot.pdf"):
        """Export plot to PDF format."""
        if self.current_fig is None:
            QMessageBox.warning(self, "No Plot", "No plot available to export.")
            return
        
        # Get save file path
        try:
            default_dir = load_last_output_dir()
        except Exception as e:
            logger.warning(f"Failed to load last output directory: {e}")
            default_dir = str(Path.home() / "Desktop")
        
        default_filename = f"flowproc_{self.metric_name.replace(' ', '_').replace('|', '_')}.pdf"
        default_path = Path(default_dir) / default_filename
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Plot as PDF",
            str(default_path),
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                # Export plot (excluding legend if desired by temp hiding)
                temp_fig = self.current_fig  # Copy to modify
                # Optional: Hide legend for export: temp_fig.update_layout(showlegend=False)
                temp_fig.write_image(file_path, width=1800, height=600, scale=1)  # 6x2 inches at 300 DPI
                
                logger.info(f"Plot exported as PDF: {file_path}")
                
                # Save the directory for next time
                try:
                    save_last_output_dir(str(Path(file_path).parent))
                except Exception as e:
                    logger.warning(f"Failed to save output directory: {e}")
                
                QMessageBox.information(self, "Success", f"Plot exported to {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to export plot as PDF: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to export plot as PDF: {str(e)}")
            
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle dialog resize events."""
        super().resizeEvent(event)
        logger.debug(f"Dialog resized to {event.size()}")
        
        # Regenerate plot with new width if we have a current figure
        # This ensures timecourse plots use the full available width
        if self.current_fig is not None:
            # Add a small delay to avoid too many regenerations during resize
            QTimer.singleShot(500, self._generate_plot)
        
    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
        # Clean up temporary file
        if self.temp_html and self.temp_html.exists():
            try:
                self.temp_html.unlink()
                logger.debug(f"Cleaned up temporary file: {self.temp_html}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {self.temp_html}: {e}")
        super().closeEvent(event)

def visualize_metric(
    csv_path: Optional[Path],
    metric: str,
    time_course_mode: bool,
    parent_widget: Optional[QWidget] = None,
    user_group_labels: Optional[List[str]] = None,
    tissue_filter: Optional[str] = None,
    subpopulation_filter: Optional[str] = None
) -> None:
    """Generate and display visualization for the given CSV and metric using the enhanced dialog."""
    if not csv_path or not csv_path.exists():
        QMessageBox.warning(parent_widget, "No Data", "Select at least one CSV file to visualize.")
        logger.warning("Visualization attempted with no valid CSV")
        return
    
    try:
        # Create and show the enhanced visualization dialog
        dialog = VisualizationDialog(
            parent=parent_widget,
            csv_path=csv_path,
            metric_name=metric,  # Pass as metric_name to avoid Qt conflict
            time_course_mode=time_course_mode,
            user_group_labels=user_group_labels
        )
        
        dialog.exec()
        
    except Exception as e:
        logger.error(f"Visualization failed: {str(e)}", exc_info=True)
        if parent_widget and isinstance(parent_widget, QWidget):
            QMessageBox.critical(parent_widget, "Visualization Error", f"Failed: {str(e)}")
        else:
            raise RuntimeError(f"Visualization failed: {str(e)}")