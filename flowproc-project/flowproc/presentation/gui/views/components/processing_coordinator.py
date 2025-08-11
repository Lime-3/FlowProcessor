# File: flowproc/presentation/gui/views/components/processing_coordinator.py
"""
Processing coordination and management.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Any, Optional, List
from pathlib import Path
import pandas as pd

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from ...workers.processing_worker import ProcessingManager, ProcessingResult, ProcessingState

if TYPE_CHECKING:
    from ..main_window import MainWindow
    from .state_manager import StateManager

logger = logging.getLogger(__name__)


class ProcessingCoordinator(QObject):
    """
    Coordinates processing operations and worker management.
    
    Handles the interface between the UI and processing workers.
    """
    
    # Signals for processing coordination
    processing_started = Signal()
    processing_completed = Signal(ProcessingResult)
    processing_error = Signal(str)
    processing_cancelled = Signal()

    def __init__(self, main_window: MainWindow, state_manager: StateManager) -> None:
        super().__init__()
        self.main_window = main_window
        self.state_manager = state_manager
        self.processing_manager = ProcessingManager(self)

    def connect_signals(self) -> None:
        """Connect processing signals to main window handlers."""
        self.processing_started.connect(self.main_window.on_processing_started)
        self.processing_completed.connect(self.main_window.on_processing_completed)
        self.processing_error.connect(self.main_window.on_processing_error)
        
        # Connect processing manager signals
        # Note: Progress and status signals are handled through callbacks in start_processing
        # self.processing_manager.processing_completed.connect(self._on_processing_completed)
        # self.processing_manager.processing_error.connect(self._on_processing_error)

    def start_processing(self, params: Dict[str, Any]) -> None:
        """
        Start the data processing operation.
        
        Args:
            params: Processing parameters dictionary
        """
        try:
            self.state_manager.is_processing = True
            self.processing_started.emit()
            
            # Start processing with the provided parameters
            self.processing_manager.start_processing(
                input_paths=params['input_paths'],
                output_dir=params['output_dir'],
                time_course_mode=params['time_course_mode'],
                user_replicates=params.get('user_replicates'),
                auto_parse_groups=params.get('auto_parse_groups', True),
                user_group_labels=params.get('user_group_labels', []),
                user_groups=params.get('user_groups'),
                progress_callback=self.main_window.on_progress_updated,
                status_callback=self.main_window.on_status_updated,
                completion_callback=self._on_processing_completed
            )
            
            logger.info("Processing started with parameters: %s", params)
            
        except Exception as e:
            self.state_manager.is_processing = False
            self.processing_error.emit(f"Failed to start processing: {str(e)}")
            logger.error("Failed to start processing", exc_info=True)

    def cancel_processing(self) -> None:
        """Cancel the current processing operation."""
        try:
            self.processing_manager.cancel_processing()
            self.state_manager.is_processing = False
            self.processing_cancelled.emit()
            logger.info("Processing cancelled by user")
            
        except Exception as e:
            logger.error("Error cancelling processing", exc_info=True)

    def pause_processing(self) -> None:
        """Pause the current processing operation."""
        try:
            self.processing_manager.pause_processing()
            logger.info("Processing paused by user")
            
        except Exception as e:
            logger.error("Error pausing processing", exc_info=True)

    def resume_processing(self) -> None:
        """Resume the current processing operation."""
        try:
            self.processing_manager.resume_processing()
            logger.info("Processing resumed by user")
            
        except Exception as e:
            logger.error("Error resuming processing", exc_info=True)

    def get_state(self) -> ProcessingState:
        """Get the current processing state."""
        return self.processing_manager.get_state()

    def is_processing(self) -> bool:
        """Check if processing is currently active."""
        return self.processing_manager.is_processing()

    @staticmethod
    def apply_filters(df: pd.DataFrame, options) -> pd.DataFrame:
        """
        Apply filters to data based on visualization options.
        When no filters are selected, returns an empty DataFrame.
        
        Args:
            df: DataFrame to filter
            options: VisualizationOptions object with filter settings
            
        Returns:
            Filtered DataFrame (empty if no filters selected)
        """
        filtered_df = df.copy()
        original_rows = len(filtered_df)
        
        # Check if any filters are selected
        has_tissue_filter = hasattr(options, 'selected_tissues') and options.selected_tissues
        has_time_filter = hasattr(options, 'selected_times') and options.selected_times
        
        # Check if data has filterable columns
        has_tissue_data = 'Tissue' in filtered_df.columns and not filtered_df['Tissue'].isna().all()
        has_time_data = 'Time' in filtered_df.columns and not filtered_df['Time'].isna().all()
        
        # If no filters are selected but data has filterable columns, show all data
        # This handles the case where filters are auto-populated but not explicitly selected
        if not has_tissue_filter and not has_time_filter:
            if has_tissue_data or has_time_data:
                logger.info("No filters explicitly selected but data has filterable columns - showing all data")
                return filtered_df  # Return all data
            else:
                logger.info("No filters selected and no filterable data - returning empty DataFrame")
                return filtered_df.iloc[0:0]  # Return empty DataFrame with same structure
        
        # Apply tissue filter
        if has_tissue_filter and 'Tissue' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Tissue'].isin(options.selected_tissues)]
            logger.info(f"After tissue filter: {len(filtered_df)} rows (was {original_rows})")
        
        # Apply time filter
        if has_time_filter and 'Time' in filtered_df.columns:
            pre_time_rows = len(filtered_df)
            filtered_df = filtered_df[filtered_df['Time'].isin(options.selected_times)]
            logger.info(f"After time filter: {len(filtered_df)} rows (was {pre_time_rows})")
        
        logger.info(f"Filter summary: {original_rows} -> {len(filtered_df)} rows")
        return filtered_df

    def visualize_data_with_options(self, csv_path: Path, options, output_html: Optional[Path] = None) -> Optional[Path]:
        """
        Unified visualization method that handles filtering and options.
        
        Args:
            csv_path: Path to the CSV file to visualize
            options: VisualizationOptions object with all parameters and filters
            output_html: Optional output path, will create temp file if not provided
            
        Returns:
            Path to generated HTML file, or None if failed
        """
        try:
            # Load and parse data
            from flowproc.domain.parsing import load_and_parse_df
            df, _ = load_and_parse_df(csv_path)
            
            if df is None or df.empty:
                raise ValueError("No data found in CSV file")
            
            # Apply filters
            filtered_df = self.apply_filters(df, options)
            
            if filtered_df.empty:
                raise ValueError("No data matches current filters")
            
            # Create output file if not provided
            if output_html is None:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                    output_html = Path(tmp_file.name)
            
            # Use the flow cytometry visualizer with filtered data
            from flowproc.domain.visualization.flow_cytometry_visualizer import plot, time_plot
            
            if options.time_course_mode:
                fig = time_plot(
                    data=filtered_df,  # Pass filtered DataFrame
                    time_col='Time',
                    value_col=options.y_axis,
                    save_html=output_html,
                    filter_options=options
                )
            else:
                fig = plot(
                    data=filtered_df,  # Pass filtered DataFrame
                    x='Group',
                    y=options.y_axis,
                    plot_type=options.plot_type,
                    save_html=output_html,
                    filter_options=options
                )
            
            logger.info(f"Visualization created for {csv_path} with options: {options}")
            return output_html
            
        except Exception as e:
            error_msg = f"Failed to visualize data: {str(e)}"
            QMessageBox.critical(
                self.main_window,
                "Visualization Error",
                error_msg
            )
            logger.error("Visualization failed", exc_info=True)
            return None

    def handle_close_request(self) -> bool:
        """
        Handle application close request.
        
        Returns:
            True if the application can close, False otherwise
        """
        if self.is_processing():
            reply = QMessageBox.question(
                self.main_window,
                "Processing in Progress",
                "Processing is still running. Do you want to cancel and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.cancel_processing()
                return True
            else:
                return False
        
        return True

    def cleanup(self) -> None:
        """Clean up resources when the application is closing."""
        try:
            if self.is_processing():
                self.cancel_processing()
            self.processing_manager.cleanup()
            logger.debug("Processing coordinator cleanup completed")
            
        except Exception as e:
            logger.error("Error during processing coordinator cleanup", exc_info=True)

    @Slot(ProcessingResult)
    def _on_processing_completed(self, result: ProcessingResult) -> None:
        """Handle processing completion from the worker."""
        self.state_manager.is_processing = False
        self.processing_completed.emit(result)

    @Slot(str)
    def _on_processing_error(self, error_message: str) -> None:
        """Handle processing error from the worker."""
        self.state_manager.is_processing = False
        self.processing_error.emit(error_message)