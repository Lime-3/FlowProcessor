"""
Main Controller for the GUI application.

This controller handles the business logic for the main window,
managing the interaction between the view and domain services.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot

from ....domain.parsing.service import ParseService
from ....domain.processing.service import DataProcessingService
# VisualizationService removed - using simple_visualizer directly
from ....domain.export.service import ExportService
from ..workers.processing_worker import ProcessingManager, ProcessingResult
from ..views.main_window import MainWindow

logger = logging.getLogger(__name__)


class MainController(QObject):
    """
    Main controller that coordinates between the GUI and domain services.
    
    This controller handles:
    - Input validation
    - Processing coordination
    - Error handling
    - State management
    """
    
    # Signals
    processing_started = Signal()
    processing_completed = Signal(ProcessingResult)
    processing_error = Signal(str)
    validation_error = Signal(str)
    
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self.main_window = main_window
        self.processing_manager = ProcessingManager(self)
        
        # Initialize domain services
        self.parse_service = ParseService()
        self.processing_service = DataProcessingService()
        # self.visualization_service = VisualizationService()  # Removed - using simple_visualizer directly
        self.export_service = ExportService()
        
        # Connect signals
        self._connect_signals()
        
    def _connect_signals(self) -> None:
        """Connect controller signals to the main window."""
        self.processing_started.connect(self.main_window.on_processing_started)
        self.processing_completed.connect(self.main_window.on_processing_completed)
        self.processing_error.connect(self.main_window.on_processing_error)
        self.validation_error.connect(self.main_window.on_validation_error)
        
    def validate_inputs(self, input_paths: List[str], output_dir: str, 
                       time_course_mode: bool, **kwargs) -> bool:
        """
        Validate user inputs before processing using the unified validation service.
        
        Args:
            input_paths: List of input file/directory paths
            output_dir: Output directory path
            time_course_mode: Whether time course mode is enabled
            **kwargs: Additional validation parameters
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            from flowproc.domain.validation import validate_gui_inputs
            
            # Extract groups and replicates from kwargs
            groups = kwargs.get('groups')
            replicates = kwargs.get('replicates')
            
            # Use the unified validation service
            result = validate_gui_inputs(
                input_paths=input_paths,
                output_dir=output_dir,
                groups=groups,
                replicates=replicates,
                time_course_mode=time_course_mode,
                **kwargs
            )
            
            if not result.is_valid:
                # Emit the first error message
                if result.errors:
                    self.validation_error.emit(result.errors[0])
                else:
                    self.validation_error.emit("Validation failed")
                return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            self.validation_error.emit(f"Validation error: {e}")
            return False
        
    def start_processing(self, input_paths: List[str], output_dir: str,
                        time_course_mode: bool, **kwargs) -> bool:
        """
        Start the processing workflow.
        
        Args:
            input_paths: List of input file/directory paths
            output_dir: Output directory path
            time_course_mode: Whether time course mode is enabled
            **kwargs: Additional processing parameters
            
        Returns:
            True if processing started successfully, False otherwise
        """
        try:
            # Validate inputs first
            if not self.validate_inputs(input_paths, output_dir, time_course_mode, **kwargs):
                return False
                
            # Convert paths to Path objects
            input_path_objects = [Path(p) for p in input_paths]
            output_path = Path(output_dir)
            
            # Start processing
            success = self.processing_manager.start_processing(
                input_paths=input_path_objects,
                output_dir=output_path,
                time_course_mode=time_course_mode,
                progress_callback=self._on_progress,
                status_callback=self._on_status,
                completion_callback=self._on_completion,
                **kwargs
            )
            
            if success:
                self.processing_started.emit()
                
            return success
            
        except Exception as e:
            logger.error(f"Error starting processing: {e}")
            self.processing_error.emit(f"Error starting processing: {e}")
            return False
            
    def cancel_processing(self) -> None:
        """Cancel the current processing operation."""
        self.processing_manager.cancel_processing()
        
    def pause_processing(self) -> None:
        """Pause the current processing operation."""
        self.processing_manager.pause_processing()
        
    def resume_processing(self) -> None:
        """Resume the current processing operation."""
        self.processing_manager.resume_processing()
        
    def is_processing(self) -> bool:
        """Check if processing is currently running."""
        return self.processing_manager.is_processing()
        
    @Slot(int)
    def _on_progress(self, value: int) -> None:
        """Handle progress updates from the processing worker."""
        self.main_window.on_progress_updated(value)
        
    @Slot(str)
    def _on_status(self, message: str) -> None:
        """Handle status updates from the processing worker."""
        self.main_window.on_status_updated(message)
        
    @Slot(ProcessingResult)
    def _on_completion(self, result: ProcessingResult) -> None:
        """Handle processing completion."""
        self.processing_completed.emit(result)
        
    def cleanup(self) -> None:
        """Clean up resources when the application is closing."""
        self.processing_manager.cleanup()