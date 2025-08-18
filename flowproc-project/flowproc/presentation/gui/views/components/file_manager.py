# File: flowproc/presentation/gui/views/components/file_manager.py
"""
File management and operations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtWidgets import (
    QFileDialog, QMainWindow, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QMessageBox
)

if TYPE_CHECKING:
    from .state_manager import StateManager

logger = logging.getLogger(__name__)


class FileManager:
    """
    Handles file operations and dialogs.
    
    Centralizes file-related functionality for better organization.
    """

    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

    def browse_input_files(self) -> List[str]:
        """
        Open file/folder browser for input selection.
        
        Returns:
            List of selected file/folder paths
        """
        # Get the main window as parent for proper dialog hierarchy
        main_window = self.state_manager.main_window if hasattr(self.state_manager, 'main_window') else None
        
        dialog = QFileDialog(main_window)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter("CSV Files (*.csv);;All Files (*)")
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        
        # Enable both file and directory selection
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_paths = dialog.selectedFiles()
            validated_paths = self._validate_and_expand_paths(selected_paths)
            logger.info(f"Selected {len(validated_paths)} valid input paths")
            return validated_paths
        
        return []

    def show_preview_dialog(self, file_paths: List[str]) -> None:
        """
        Show a preview dialog for the selected CSV files.
        
        Args:
            file_paths: List of CSV file paths to preview
        """
        try:
            from ....parsing import load_and_parse_df
            
            # Get the main window as parent for proper dialog hierarchy
            main_window = self.state_manager.main_window if hasattr(self.state_manager, 'main_window') else None
            
            preview_window = QMainWindow(main_window)
            preview_window.setWindowTitle("Combined Summary Preview")
            preview_window.setMinimumSize(600, 400)
            
            table = self._create_preview_table(file_paths)
            preview_window.setCentralWidget(table)
            preview_window.show()
            
            # Keep reference to prevent garbage collection
            if not hasattr(self, '_preview_windows'):
                self._preview_windows = []
            self._preview_windows.append(preview_window)
            
            logger.info(f"Opened preview for {len(file_paths)} files")
            
        except Exception as e:
            QMessageBox.warning(
                main_window,
                "Preview Error",
                f"Failed to generate preview: {str(e)}"
            )
            logger.error("Preview generation failed", exc_info=True)

    def _validate_and_expand_paths(self, paths: List[str]) -> List[str]:
        """
        Validate paths and expand directories to find CSV files.
        
        Args:
            paths: List of file/directory paths
            
        Returns:
            List of valid CSV file paths
        """
        valid_paths = []
        
        for path_str in paths:
            path = Path(path_str)
            
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue
                
            if path.is_file():
                if path.suffix.lower() == '.csv':
                    valid_paths.append(str(path))
                else:
                    logger.warning(f"Skipping non-CSV file: {path}")
                    
            elif path.is_dir():
                # Find all CSV files in directory
                csv_files = list(path.glob("*.csv"))
                if csv_files:
                    valid_paths.extend(str(f) for f in csv_files)
                    logger.info(f"Found {len(csv_files)} CSV files in {path}")
                else:
                    logger.warning(f"No CSV files found in directory: {path}")
        
        return valid_paths

    def _create_preview_table(self, file_paths: List[str]) -> QTableWidget:
        """
        Create a preview table widget for the CSV files.
        
        Args:
            file_paths: List of CSV file paths
            
        Returns:
            Configured QTableWidget with preview data
        """
        from ....parsing import load_and_parse_df
        
        table = QTableWidget(len(file_paths), 6)
        table.setHorizontalHeaderLabels([
            "File", "Samples", "Groups", "Animal Range", "Timepoint", "Tissue"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        for row, file_path in enumerate(file_paths):
            path_obj = Path(file_path)
            
            if not path_obj.exists() or not path_obj.is_file() or path_obj.suffix.lower() != '.csv':
                table.setItem(row, 0, QTableWidgetItem(f"{path_obj.name} - Error: Invalid file"))
                continue
            
            try:
                df, _ = load_and_parse_df(path_obj)
                
                # Extract summary information
                num_samples = len(df)
                unique_groups = self._get_unique_values(df, "Group")
                unique_animals = self._get_unique_values(df, "Animal")
                unique_timepoints = self._get_unique_values(df, "Time")
                unique_tissues = self._get_unique_values(df, "Tissue")
                
                # Populate table row
                table.setItem(row, 0, QTableWidgetItem(path_obj.name))
                table.setItem(row, 1, QTableWidgetItem(str(num_samples)))
                table.setItem(row, 2, QTableWidgetItem(unique_groups))
                table.setItem(row, 3, QTableWidgetItem(unique_animals))
                table.setItem(row, 4, QTableWidgetItem(unique_timepoints))
                table.setItem(row, 5, QTableWidgetItem(unique_tissues))
                
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {str(e)}", exc_info=True)
                table.setItem(
                    row, 0, 
                    QTableWidgetItem(f"{path_obj.name} - Error: Failed to parse ({str(e)})")
                )
        
        return table

    def _get_unique_values(self, df, column_name: str) -> str:
        """
        Get unique values from a DataFrame column as a string.
        
        Args:
            df: DataFrame to process
            column_name: Name of the column to extract values from
            
        Returns:
            Comma-separated string of unique values or "N/A"
        """
        if column_name not in df.columns or df[column_name].isna().all():
            return "N/A"
            
        unique_values = df[column_name].dropna().unique()
        if len(unique_values) == 0:
            return "N/A"
            
        # Sort and join values
        sorted_values = sorted(map(str, unique_values))
        return ", ".join(sorted_values)