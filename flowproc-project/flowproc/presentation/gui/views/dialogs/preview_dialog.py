"""
Preview Dialog for displaying CSV file contents.

This dialog allows users to preview CSV files before processing,
showing a sample of the data and basic statistics.
"""

from typing import List, Optional
from pathlib import Path
import pandas as pd

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QSpinBox, QGroupBox, QFormLayout,
    QHeaderView, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

class CSVPreviewWorker(QThread):
    """Worker thread for loading CSV preview data."""
    
    data_loaded = Signal(pd.DataFrame)
    error_occurred = Signal(str)
    
    def __init__(self, file_path: Path, max_rows: int = 100):
        super().__init__()
        self.file_path = file_path
        self.max_rows = max_rows
        
    def run(self):
        """Load CSV data in background thread."""
        try:
            # Read CSV with limited rows for preview
            df = pd.read_csv(self.file_path, nrows=self.max_rows)
            self.data_loaded.emit(df)
        except Exception as e:
            self.error_occurred.emit(str(e))


class PreviewDialog(QDialog):
    """
    Dialog for previewing CSV file contents.
    
    Features:
    - Table view of CSV data
    - Basic statistics
    - Column selection
    - Row limit control
    """
    
    # Signals
    file_selected = Signal(Path)
    
    def __init__(self, parent=None, csv_files: Optional[List[Path]] = None):
        super().__init__(parent)
        self.csv_files = csv_files or []
        self.current_data: Optional[pd.DataFrame] = None
        self.preview_worker: Optional[CSVPreviewWorker] = None
        
        self.setWindowTitle("CSV Preview")
        self.setModal(True)
        self.resize(800, 600)
        
        self._setup_ui()
        self._setup_styling()
        
        if self.csv_files:
            self._populate_file_selector()
            
    def _setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # File selection group
        file_group = QGroupBox("File Selection")
        file_layout = QFormLayout(file_group)
        
        self.file_combo = QComboBox()
        self.file_combo.currentTextChanged.connect(self._on_file_selected)
        file_layout.addRow("CSV File:", self.file_combo)
        
        # Preview options group
        options_group = QGroupBox("Preview Options")
        options_layout = QFormLayout(options_group)
        
        self.row_limit_spin = QSpinBox()
        self.row_limit_spin.setRange(10, 1000)
        self.row_limit_spin.setValue(100)
        self.row_limit_spin.setSuffix(" rows")
        self.row_limit_spin.valueChanged.connect(self._on_options_changed)
        options_layout.addRow("Max Rows:", self.row_limit_spin)
        
        # Statistics group
        self.stats_group = QGroupBox("File Statistics")
        self.stats_layout = QFormLayout(self.stats_group)
        
        self.stats_label = QLabel("No file selected")
        self.stats_layout.addRow("Info:", self.stats_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._refresh_preview)
        self.refresh_button.setEnabled(False)
        
        self.select_button = QPushButton("Select File")
        self.select_button.clicked.connect(self._select_current_file)
        self.select_button.setEnabled(False)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.close_button)
        
        # Add all components to main layout
        layout.addWidget(file_group)
        layout.addWidget(options_group)
        layout.addWidget(self.stats_group)
        layout.addWidget(self.table)
        layout.addWidget(self.progress_bar)
        layout.addLayout(button_layout)
        
    def _setup_styling(self):
        """Apply custom styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #404040;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QComboBox, QSpinBox {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                color: #ffffff;
                padding: 5px;
            }
            
            QComboBox::drop-down {
                border: none;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            
            QComboBox QAbstractItemView {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                color: #ffffff;
                selection-background-color: #505050;
                selection-color: #ffffff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #505050;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #505050;
                color: #ffffff;
            }
            
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                color: #ffffff;
                padding: 8px 16px;
            }
            
            QPushButton:hover {
                background-color: #505050;
            }
            
            QPushButton:pressed {
                background-color: #303030;
            }
            
            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #808080;
                border-color: #404040;
            }
            
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #2b2b2b;
                gridline-color: #404040;
                color: #ffffff;
            }
            
            QTableWidget::item {
                padding: 5px;
            }
            
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #606060;
            }
        """)
        
    def _populate_file_selector(self):
        """Populate the file selector combo box."""
        self.file_combo.clear()
        for file_path in self.csv_files:
            self.file_combo.addItem(file_path.name, str(file_path))
            
        if self.csv_files:
            self.file_combo.setCurrentIndex(0)
            
    def set_csv_files(self, csv_files: List[Path]):
        """Set the list of CSV files to preview."""
        self.csv_files = csv_files
        self._populate_file_selector()
        
    def _on_file_selected(self, file_name: str):
        """Handle file selection change."""
        if not file_name:
            return
            
        file_path = Path(self.file_combo.currentData())
        if file_path.exists():
            self.refresh_button.setEnabled(True)
            self._load_preview(file_path)
        else:
            self.refresh_button.setEnabled(False)
            self.select_button.setEnabled(False)
            self._clear_preview()
            
    def _on_options_changed(self):
        """Handle preview options changes."""
        if self.file_combo.currentData():
            file_path = Path(self.file_combo.currentData())
            self._load_preview(file_path)
            
    def _load_preview(self, file_path: Path):
        """Load preview data for the selected file."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Cancel any existing worker
        if self.preview_worker and self.preview_worker.isRunning():
            self.preview_worker.quit()
            self.preview_worker.wait()
            
        # Create and start new worker
        self.preview_worker = CSVPreviewWorker(file_path, self.row_limit_spin.value())
        self.preview_worker.data_loaded.connect(self._on_data_loaded)
        self.preview_worker.error_occurred.connect(self._on_load_error)
        self.preview_worker.start()
        
    def _on_data_loaded(self, df: pd.DataFrame):
        """Handle data loaded from worker thread."""
        self.current_data = df
        self._populate_table(df)
        self._update_statistics(df)
        self.select_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    def _on_load_error(self, error_message: str):
        """Handle data loading error."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Load Error", f"Failed to load CSV file:\n{error_message}")
        self._clear_preview()
        
    def _populate_table(self, df: pd.DataFrame):
        """Populate the table with DataFrame data."""
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        
        # Populate table data
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, j, item)
                
    def _update_statistics(self, df: pd.DataFrame):
        """Update the statistics display."""
        stats_text = f"""
        Rows: {len(df):,}
        Columns: {len(df.columns):,}
        Memory usage: {df.memory_usage(deep=True).sum() / 1024:.1f} KB
        """
        
        self.stats_label.setText(stats_text.strip())
        
    def _clear_preview(self):
        """Clear the preview display."""
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.stats_label.setText("No file selected")
        self.select_button.setEnabled(False)
        
    def _refresh_preview(self):
        """Refresh the current preview."""
        if self.file_combo.currentData():
            file_path = Path(self.file_combo.currentData())
            self._load_preview(file_path)
            
    def _select_current_file(self):
        """Select the currently previewed file."""
        if self.file_combo.currentData():
            file_path = Path(self.file_combo.currentData())
            self.file_selected.emit(file_path)
            self.accept()
            
    def get_selected_file(self) -> Optional[Path]:
        """Get the currently selected file path."""
        if self.file_combo.currentData():
            return Path(self.file_combo.currentData())
        return None