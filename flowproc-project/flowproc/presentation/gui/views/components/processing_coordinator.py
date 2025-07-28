# File: flowproc/presentation/gui/views/components/processing_coordinator.py
"""
Processing coordination and management.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Any, Optional, List
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from ...workers.processing_worker import ProcessingManager, ProcessingResult, ProcessingState
from ...visualizer import visualize_metric

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

    def visualize_data(self, csv_path: Path, metric: str, time_course: bool, user_group_labels: Optional[List[str]] = None) -> None:
        """
        Visualize processed data.
        
        Args:
            csv_path: Path to the CSV file to visualize
            metric: Visualization metric to use
            time_course: Whether to use time course mode
            user_group_labels: Optional group labels for visualization
        """
        try:
            visualize_metric(
                csv_path=csv_path,
                metric=metric,
                time_course_mode=time_course,
                parent_widget=self.main_window,
                user_group_labels=user_group_labels
            )
            logger.info(f"Visualization opened for {csv_path} with metric {metric}")
            
        except Exception as e:
            error_msg = f"Failed to visualize data: {str(e)}"
            QMessageBox.critical(
                self.main_window,
                "Visualization Error",
                error_msg
            )
            logger.error("Visualization failed", exc_info=True)

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