# File: flowproc/presentation/gui/views/components/event_handler.py
"""
Event handling for the main window.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List
from pathlib import Path

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMainWindow, QDialog, QSizePolicy

from ..dialogs import GroupLabelsDialog
from ..dialogs.manual_groups_dialog import ManualGroupsDialog
from ...workers.processing_worker import ProcessingResult
from ...config_handler import save_last_output_dir
from flowproc.config import parse_range_or_list, USER_GROUPS, USER_REPLICATES, AUTO_PARSE_GROUPS, USER_GROUP_LABELS
from flowproc.core.constants import KEYWORDS

if TYPE_CHECKING:
    from ..main_window import MainWindow
    from .state_manager import StateManager
    from .file_manager import FileManager
    from .processing_coordinator import ProcessingCoordinator

logger = logging.getLogger(__name__)


class EventHandler(QObject):
    """
    Handles UI events and user interactions.
    
    Centralizes event handling logic to keep the main window clean.
    """

    def __init__(
        self,
        main_window: MainWindow,
        state_manager: StateManager,
        file_manager: FileManager,
        processing_coordinator: ProcessingCoordinator
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.state_manager = state_manager
        self.file_manager = file_manager
        self.processing_coordinator = processing_coordinator

    def connect_all_signals(self) -> None:
        """Connect all UI signals to their handlers."""
        ui_builder = self.main_window.ui_builder
        
        # Button connections
        ui_builder.get_widget('browse_input_button').clicked.connect(self.browse_input)
        ui_builder.get_widget('clear_button').clicked.connect(self.clear_input)
        ui_builder.get_widget('preview_button').clicked.connect(self.preview_csv)
        ui_builder.get_widget('out_dir_button').clicked.connect(self.browse_output)
        ui_builder.get_widget('process_button').clicked.connect(self.process_data)
        ui_builder.get_widget('visualize_button').clicked.connect(self.visualize_results)
        ui_builder.get_widget('group_labels_button').clicked.connect(self.open_group_labels_dialog)
        ui_builder.get_widget('manual_groups_button').clicked.connect(self.open_manual_groups_dialog)
        
        # Path entry text change
        ui_builder.get_widget('path_entry').textChanged.connect(self.update_preview_paths)



    @Slot()
    def update_preview_paths(self) -> None:
        """Update the list of previewable CSV paths."""
        ui_builder = self.main_window.ui_builder
        file_paths = ui_builder.get_widget('path_entry').text().split("; ")
        self.state_manager.preview_paths = [
            p for p in file_paths 
            if p and Path(p).is_file() and Path(p).suffix.lower() == '.csv' and Path(p).exists()
        ]
        
        if self.state_manager.preview_paths:
            self.state_manager.last_csv = Path(self.state_manager.preview_paths[0])
            logger.info(f"Set last_csv to {self.state_manager.last_csv}")
        else:
            self.state_manager.last_csv = None

    @Slot()
    def browse_input(self) -> None:
        """Handle browsing for input CSV files."""
        logger.debug("Browse input files triggered")
        options = QFileDialog.Option.DontUseNativeDialog
        
        # Use Desktop as default starting directory
        from ...config_handler import load_last_output_dir
        try:
            default_dir = load_last_output_dir()
        except Exception as e:
            logger.warning(f"Failed to load last output directory: {e}")
            default_dir = str(Path.home() / "Desktop")
        
        files, _ = QFileDialog.getOpenFileNames(
            self.main_window, "Select CSV Files", default_dir, "CSV files (*.csv)", options=options
        )
        if files:
            ui_builder = self.main_window.ui_builder
            ui_builder.get_widget('path_entry').setText("; ".join(files))
            self.update_preview_paths()

    @Slot()
    def clear_input(self) -> None:
        """Clear the input field and reset preview paths."""
        ui_builder = self.main_window.ui_builder
        ui_builder.get_widget('path_entry').clear()
        self.state_manager.clear_preview_data()
        logger.debug("Input field and preview paths cleared.")

    @Slot()
    def preview_csv(self) -> None:
        """Display a preview table for selected CSV files."""
        from flowproc.domain.parsing.parsing_utils import load_and_parse_df
        
        if not self.state_manager.preview_paths:
            QMessageBox.warning(
                self.main_window, 
                "Invalid Input", 
                "No valid CSV files available for preview."
            )
            return
            
        table = QTableWidget(len(self.state_manager.preview_paths), 6)
        table.setHorizontalHeaderLabels(["File", "Samples", "Groups", "Animal Range", "Timepoint", "Tissue"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        row = 0
        
        for selected_path in self.state_manager.preview_paths:
            path_obj = Path(selected_path)
            if not path_obj.exists() or not path_obj.is_file() or path_obj.suffix.lower() != '.csv':
                table.setItem(row, 0, QTableWidgetItem(f"{path_obj.name} - Error: Invalid file"))
                row += 1
                continue
                
            try:
                # Use the correct parsing function
                df, _ = load_and_parse_df(path_obj)
                num_samples = len(df)
                
                # Check for various possible column names and combinations
                group_col = None
                animal_col = None
                time_col = None
                tissue_col = None
                
                # Look for group columns
                for col in df.columns:
                    col_lower = col.lower()
                    if 'group' in col_lower or 'treatment' in col_lower or 'condition' in col_lower:
                        group_col = col
                        break
                
                # Look for animal columns
                for col in df.columns:
                    col_lower = col.lower()
                    if 'animal' in col_lower or 'mouse' in col_lower or 'subject' in col_lower:
                        animal_col = col
                        break
                
                # Look for time columns
                for col in df.columns:
                    col_lower = col.lower()
                    if 'time' in col_lower or 'timepoint' in col_lower or 'hour' in col_lower or 'day' in col_lower:
                        time_col = col
                        break
                
                # Look for tissue columns
                for col in df.columns:
                    col_lower = col.lower()
                    if 'tissue' in col_lower or 'organ' in col_lower:
                        tissue_col = col
                        break
                
                # Extract unique values for each column type
                unique_groups = "N/A"
                if group_col and group_col in df.columns and not df[group_col].isna().all():
                    groups = sorted(df[group_col].dropna().unique())
                    if len(groups) > 0:
                        if len(groups) == 1:
                            unique_groups = str(groups[0])
                        else:
                            unique_groups = f"{len(groups)}: {min(groups)} - {max(groups)}"
                
                unique_animals = "N/A"
                if animal_col and animal_col in df.columns and not df[animal_col].isna().all():
                    animals = sorted(df[animal_col].dropna().unique())
                    if len(animals) > 0:
                        if len(animals) == 1:
                            unique_animals = str(animals[0])
                        else:
                            unique_animals = f"{len(animals)}: {min(animals)} - {max(animals)}"
                
                unique_timepoints = "N/A"
                if time_col and time_col in df.columns and not df[time_col].isna().all():
                    timepoints = sorted(df[time_col].dropna().unique())
                    if len(timepoints) > 0:
                        if len(timepoints) == 1:
                            unique_timepoints = str(timepoints[0])
                        else:
                            unique_timepoints = f"{len(timepoints)}: {min(timepoints)} - {max(timepoints)}"
                
                unique_tissues = "N/A"
                if tissue_col and tissue_col in df.columns and not df[tissue_col].isna().all():
                    tissues = df[tissue_col].dropna().unique()
                    if len(tissues) > 0:
                        unique_tissues = f"{len(tissues)}: {', '.join(map(str, sorted(tissues)))}"
                
                # Populate table row
                table.setItem(row, 0, QTableWidgetItem(path_obj.name))
                table.setItem(row, 1, QTableWidgetItem(str(num_samples)))
                table.setItem(row, 2, QTableWidgetItem(unique_groups))
                table.setItem(row, 3, QTableWidgetItem(unique_animals))
                table.setItem(row, 4, QTableWidgetItem(unique_timepoints))
                table.setItem(row, 5, QTableWidgetItem(unique_tissues))
                row += 1
                
            except Exception as e:
                logger.error(f"Summary preview failed for {selected_path}: {str(e)}", exc_info=True)
                table.setItem(row, 0, QTableWidgetItem(f"{path_obj.name} - Error: Failed to parse ({str(e)})"))
                # Set other columns to error state
                for col in range(1, 6):
                    table.setItem(row, col, QTableWidgetItem("Error"))
                row += 1
                
        preview_window = QMainWindow(self.main_window)
        preview_window.setWindowTitle("Combined Summary Preview")
        preview_window.setMinimumSize(400, 300)
        preview_window.setCentralWidget(table)
        preview_window.show()
        logger.info(f"Opened combined summary preview for {len(self.state_manager.preview_paths)} files")

    @Slot()
    def browse_output(self) -> None:
        """Handle browsing for an output directory."""
        logger.debug("Browse output directory triggered")
        options = QFileDialog.Option.DontUseNativeDialog
        
        # Use Desktop as default starting directory
        from ...config_handler import load_last_output_dir
        try:
            default_dir = load_last_output_dir()
        except Exception as e:
            logger.warning(f"Failed to load last output directory: {e}")
            default_dir = str(Path.home() / "Desktop")
        
        folder = QFileDialog.getExistingDirectory(
            self.main_window, "Select Output Directory", default_dir, options=options
        )
        if folder:
            ui_builder = self.main_window.ui_builder
            ui_builder.get_widget('out_dir_entry').setText(folder)
            logger.debug(f"Selected output directory: {folder}")

    @Slot()
    def process_data(self) -> None:
        """Handle process data button click."""
        input_paths = [Path(p.strip()) for p in self.main_window.ui_builder.get_widget('path_entry').text().split("; ") if p.strip()]
        output_dir = Path(self.main_window.ui_builder.get_widget('out_dir_entry').text().strip() or ".")
        
        # Basic validation
        if not input_paths:
            QMessageBox.critical(self.main_window, "Invalid Input", "No files or folder selected.")
            return

        invalid_paths = [p for p in input_paths if not p.exists()]
        if invalid_paths:
            QMessageBox.critical(self.main_window, "Invalid Input", f"The following paths do not exist: {invalid_paths}")
            return

        if not AUTO_PARSE_GROUPS and (not USER_GROUPS or not USER_REPLICATES):
            QMessageBox.critical(self.main_window, "Missing Info", "Please define groups and replicates before processing.")
            return

        USER_GROUP_LABELS[:] = self.state_manager.current_group_labels.copy()

        # Collect processing parameters
        params = {
            'input_paths': input_paths,
            'output_dir': output_dir,
            'time_course_mode': False,  # Always use automatic detection
            'user_replicates': USER_REPLICATES if not AUTO_PARSE_GROUPS and USER_REPLICATES else None,
            'auto_parse_groups': AUTO_PARSE_GROUPS,
            'user_group_labels': USER_GROUP_LABELS if USER_GROUP_LABELS else None,
            'user_groups': USER_GROUPS if not AUTO_PARSE_GROUPS and USER_GROUPS else None
        }
        
        self.processing_coordinator.start_processing(params)

    @Slot()
    def visualize_results(self) -> None:
        """Handle visualize results button click."""
        if not self.state_manager.last_csv:
            QMessageBox.warning(
                self.main_window,
                "No Data",
                "Please select a CSV file before creating visualizations."
            )
            return
        
        # Open the visualization dialog (modern implementation)
        from ..dialogs.visualization_dialog import VisualizationDialog as _VizDialog
        
        try:
            self.state_manager.update_status("Opening visualization...")
            
            # Create and show the single visualization dialog
            visualization_dialog = _VizDialog(
                parent=self.main_window,
                csv_path=self.state_manager.last_csv
            )
            
            # Show the dialog (non-modal)
            visualization_dialog.show()
            
            self.state_manager.update_status("Visualization opened")
            
        except Exception as e:
            error_msg = f"Failed to open visualization: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.state_manager.update_status(f"Visualization error: {error_msg}")
            QMessageBox.critical(
                self.main_window,
                "Visualization Error",
                error_msg
            )



    @Slot()
    def open_group_labels_dialog(self) -> None:
        """Open the group labels dialog."""
        dialog = GroupLabelsDialog(self.main_window, self.state_manager.current_group_labels)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.state_manager.current_group_labels = dialog.get_labels()
            self.state_manager.update_status(f"Group labels updated: {len(self.state_manager.current_group_labels)} labels")
        else:
            # User cancelled, restore previous labels
            dialog.set_labels(self.state_manager.current_group_labels)

    @Slot()
    def open_manual_groups_dialog(self) -> None:
        """Open the manual groups and replicates dialog."""
        global AUTO_PARSE_GROUPS, USER_GROUPS, USER_REPLICATES
        
        dialog = ManualGroupsDialog(
            self.main_window, 
            initial_groups=USER_GROUPS.copy(),
            initial_replicates=USER_REPLICATES.copy(),
            manual_mode_enabled=not AUTO_PARSE_GROUPS
        )
        
        # Connect dialog signals
        dialog.manual_mode_toggled.connect(self._on_manual_mode_toggled)
        dialog.definitions_saved.connect(self._on_definitions_saved)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update global state
            AUTO_PARSE_GROUPS = not dialog.is_manual_mode_enabled()
            USER_GROUPS[:] = dialog.get_groups()
            USER_REPLICATES[:] = dialog.get_replicates()
            
            self.state_manager.update_status(
                f"Manual mode {'enabled' if dialog.is_manual_mode_enabled() else 'disabled'}. "
                f"Groups: {len(USER_GROUPS)}, Replicates: {len(USER_REPLICATES)}"
            )
        else:
            # User cancelled, no changes made
            pass

    def _on_manual_mode_toggled(self, enabled: bool) -> None:
        """Handle manual mode toggle from dialog."""
        # This is just for UI feedback, actual state is saved when dialog is accepted
        pass
        
    def _on_definitions_saved(self, groups: List[int], replicates: List[int]) -> None:
        """Handle definitions saved from dialog."""
        # This is just for UI feedback, actual state is saved when dialog is accepted
        pass

    def on_group_mode_changed(self, mode_text: str) -> None:
        """Handle group mode change."""
        if "custom group labels" in mode_text.lower():
            dialog = GroupLabelsDialog(self.main_window)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.state_manager.current_group_labels = dialog.get_labels()
                self.state_manager.update_status(f"Group labels updated: {len(self.state_manager.current_group_labels)} labels")

    def _validate_inputs(self) -> bool:
        """Validate user inputs before processing."""
        ui_builder = self.main_window.ui_builder
        
        # Check if preview paths are available
        if not self.state_manager.preview_paths:
            QMessageBox.warning(
                self.main_window,
                "Validation Error",
                "No valid CSV files selected for processing."
            )
            return False
        
        # Check if output directory is specified
        output_dir = ui_builder.get_widget('output_entry').text().strip()
        if not output_dir:
            QMessageBox.warning(
                self.main_window,
                "Validation Error",
                "Please specify an output directory."
            )
            return False
        
        # Check if output directory exists or can be created
        output_path = Path(output_dir)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(
                    self.main_window,
                    "Validation Error",
                    f"Cannot create output directory: {str(e)}"
                )
                return False
        
        return True

    def handle_processing_completion(self, result: ProcessingResult) -> None:
        """Handle processing completion."""
        if result.last_csv_path:
            self.state_manager.last_csv = result.last_csv_path
            
        if result.processed_count > 0:
            # Save last output dir if available and writable; tolerate test environments
            try:
                out_widget = self.main_window.ui_builder.get_widget('out_dir_entry') or \
                             self.main_window.ui_builder.get_widget('output_entry')
                out_dir = out_widget.text().strip() if out_widget else ""
                if out_dir:
                    out_path = Path(out_dir)
                    if out_path.exists() and out_path.is_dir() and out_path.parent.exists():
                        try:
                            save_last_output_dir(str(out_path))
                        except Exception:
                            logger.debug("Skipping save_last_output_dir due to unwritable path in tests")
            except Exception as e:
                logger.debug(f"Skipping save_last_output_dir: {e}")
            
            if result.failed_count > 0:
                QMessageBox.warning(
                    self.main_window,
                    "Processing Complete with Errors",
                    f"Processed {result.processed_count} items successfully.\n"
                    f"Failed to process {result.failed_count} items.\n"
                    f"Check the log for details."
                )
            else:
                QMessageBox.information(
                    self.main_window,
                    "Processing Complete",
                    f"Successfully processed {result.processed_count} items in "
                    f"{result.total_time:.1f} seconds."
                )
            self.state_manager.update_status("Ready")
        else:
            QMessageBox.critical(
                self.main_window,
                "Processing Failed",
                f"No files were processed successfully.\n"
                f"Errors: {', '.join(result.error_messages[:3])}"
            )
            self.state_manager.update_status("Error")

    def handle_processing_error(self, error_message: str) -> None:
        """Handle processing error."""
        QMessageBox.critical(
            self.main_window,
            "Processing Error",
            f"An error occurred during processing:\n{error_message}"
        )

    def handle_validation_error(self, error_message: str) -> None:
        """Handle validation error."""
        QMessageBox.warning(
            self.main_window,
            "Validation Error",
            error_message
        )