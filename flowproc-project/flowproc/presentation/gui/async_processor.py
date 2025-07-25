# flowproc/gui/async_processor.py
"""
Asynchronous processing module using QThread for non-blocking GUI operations.
Provides cancellable, progress-reporting file processing with proper thread safety.
"""
import logging
import gc
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import time

from PySide6.QtCore import QThread, Signal, QObject, QMutex, QMutexLocker, Slot
from PySide6.QtWidgets import QMessageBox

from ...config import AUTO_PARSE_GROUPS, USER_GROUPS, USER_REPLICATES, USER_GROUP_LABELS
from ...domain.export import process_csv, process_directory
from ...domain.parsing import load_and_parse_df

logger = logging.getLogger(__name__)


class ProcessingState(Enum):
    """Processing states for the worker thread."""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    CANCELLED = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class ProcessingTask:
    """Container for processing task parameters."""
    input_paths: List[Path]
    output_dir: Path
    time_course_mode: bool
    user_replicates: Optional[List[int]] = None
    auto_parse_groups: bool = True
    user_group_labels: Optional[List[str]] = None
    user_groups: Optional[List[int]] = None


@dataclass
class ProcessingResult:
    """Container for processing results."""
    processed_count: int = 0
    failed_count: int = 0
    error_messages: List[str] = field(default_factory=list)
    last_csv_path: Optional[Path] = None
    total_time: float = 0.0


class ProcessingWorker(QThread):
    """
    Worker thread for file processing operations.
    Emits signals for progress, status, and completion events.
    """
    
    # Signals
    progress_updated = Signal(int)  # Progress value (0-100)
    status_updated = Signal(str)    # Status message
    file_processed = Signal(str)    # Individual file completion
    error_occurred = Signal(str)    # Error message
    processing_completed = Signal(ProcessingResult)  # Final result
    state_changed = Signal(ProcessingState)  # State changes
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._state = ProcessingState.IDLE
        self._task: Optional[ProcessingTask] = None
        self._should_cancel = False
        self._should_pause = False
        
    @property
    def state(self) -> ProcessingState:
        """Thread-safe state getter."""
        with QMutexLocker(self._mutex):
            return self._state
            
    def _set_state(self, state: ProcessingState) -> None:
        """Thread-safe state setter with signal emission."""
        with QMutexLocker(self._mutex):
            if self._state != state:
                self._state = state
                self.state_changed.emit(state)
                logger.debug(f"Worker state changed to: {state.name}")
    
    def set_task(self, task: ProcessingTask) -> None:
        """Set the processing task."""
        with QMutexLocker(self._mutex):
            self._task = task
            self._should_cancel = False
            self._should_pause = False
            
    def cancel(self) -> None:
        """Request cancellation of the current operation."""
        with QMutexLocker(self._mutex):
            self._should_cancel = True
            logger.info("Cancellation requested")
            
    def pause(self) -> None:
        """Request pause of the current operation."""
        with QMutexLocker(self._mutex):
            self._should_pause = True
            
    def resume(self) -> None:
        """Resume paused operation."""
        with QMutexLocker(self._mutex):
            self._should_pause = False
            if self._state == ProcessingState.PAUSED:
                self._set_state(ProcessingState.RUNNING)
                
    def _check_cancellation(self) -> bool:
        """Check if cancellation was requested."""
        with QMutexLocker(self._mutex):
            return self._should_cancel
            
    def _check_pause(self) -> None:
        """Check and handle pause request."""
        while True:
            with QMutexLocker(self._mutex):
                if not self._should_pause:
                    break
                if self._state != ProcessingState.PAUSED:
                    self._set_state(ProcessingState.PAUSED)
            self.msleep(100)  # Sleep while paused
            
    def run(self) -> None:
        """Main processing loop executed in the worker thread."""
        if not self._task:
            logger.error("No task set for worker")
            return
            
        self._set_state(ProcessingState.RUNNING)
        result = ProcessingResult()
        start_time = time.time()
        
        try:
            total_items = len(self._task.input_paths)
            
            for idx, input_path in enumerate(self._task.input_paths):
                # Check for cancellation
                if self._check_cancellation():
                    self._set_state(ProcessingState.CANCELLED)
                    self.status_updated.emit("Processing cancelled")
                    break
                    
                # Check for pause
                self._check_pause()
                
                # Process single item
                success, error_msg, csv_path = self._process_single_path(input_path)
                
                if success:
                    result.processed_count += 1
                    if csv_path:
                        result.last_csv_path = csv_path
                    self.file_processed.emit(str(input_path))
                else:
                    result.failed_count += 1
                    if error_msg:
                        result.error_messages.append(error_msg)
                        self.error_occurred.emit(error_msg)
                
                # Update progress
                progress = int((idx + 1) / total_items * 100)
                self.progress_updated.emit(progress)
                
            # Set final state
            if self._check_cancellation():
                self._set_state(ProcessingState.CANCELLED)
            elif result.failed_count > 0:
                self._set_state(ProcessingState.ERROR)
            else:
                self._set_state(ProcessingState.COMPLETED)
                
        except (RuntimeError, ValueError, OSError, MemoryError) as e:
            logger.error(f"Worker thread error: {e}", exc_info=True)
            self._set_state(ProcessingState.ERROR)
            self.error_occurred.emit(str(e))
            result.error_messages.append(str(e))
        except Exception as e:
            logger.error(f"Unexpected worker thread error: {e}", exc_info=True)
            self._set_state(ProcessingState.ERROR)
            self.error_occurred.emit(f"Unexpected error: {e}")
            result.error_messages.append(f"Unexpected error: {e}")
            
        finally:
            # Always emit completion signal
            result.total_time = time.time() - start_time
            self.processing_completed.emit(result)
            self._set_state(ProcessingState.IDLE)
            
    def _process_single_path(self, input_path: Path) -> tuple[bool, Optional[str], Optional[Path]]:
        """
        Process a single file or directory.
        
        Returns:
            Tuple of (success, error_message, csv_path)
        """
        try:
            if input_path.is_file() and input_path.suffix.lower() == '.csv':
                # Check time data for time course mode
                if self._task.time_course_mode:
                    df, _ = load_and_parse_df(input_path)
                    try:
                        if 'Time' not in df.columns or df['Time'].isna().all():
                            msg = f"No time data in {input_path.name} for time course mode"
                            self.status_updated.emit(f"Skipping {input_path.name}: No time data")
                            return False, msg, None
                    finally:
                        # Explicit cleanup of DataFrame after time check
                        del df
                        gc.collect()  # Force garbage collection
                
                # Generate output filename
                suffix = '_Timecourse' if self._task.time_course_mode else '_Grouped'
                output_file = self._task.output_dir / f"{input_path.stem}_Processed{suffix}.xlsx"
                
                # Process the CSV
                self.status_updated.emit(f"Processing {input_path.name}...")
                process_csv(
                    input_path,
                    output_file,
                    time_course_mode=self._task.time_course_mode,
                    user_replicates=self._task.user_replicates,
                    auto_parse_groups=self._task.auto_parse_groups,
                    user_group_labels=self._task.user_group_labels,
                    user_groups=self._task.user_groups
                )
                
                self.status_updated.emit(f"Completed {input_path.name}")
                return True, None, input_path
                
            elif input_path.is_dir():
                # Process directory
                self.status_updated.emit(f"Processing directory {input_path.name}...")
                
                processed = process_directory(
                    input_path,
                    self._task.output_dir,
                    recursive=True,
                    pattern="*.csv",
                    status_callback=lambda msg: self.status_updated.emit(msg),
                    time_course_mode=self._task.time_course_mode,
                    user_replicates=self._task.user_replicates,
                    auto_parse_groups=self._task.auto_parse_groups,
                    user_group_labels=self._task.user_group_labels,
                    user_groups=self._task.user_groups
                )
                
                msg = f"Processed {processed} files from {input_path.name}"
                self.status_updated.emit(msg)
                return processed > 0, None if processed > 0 else "No files processed", None
                
            else:
                return False, f"Invalid path: {input_path}", None
                
        except Exception as e:
            error_msg = f"Error processing {input_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg, None


class ProcessingManager(QObject):
    """
    Manager for processing operations.
    Handles worker lifecycle, signals, and provides high-level interface.
    """
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._worker: Optional[ProcessingWorker] = None
        self._current_task: Optional[ProcessingTask] = None
        
    def start_processing(
        self,
        input_paths: List[Path],
        output_dir: Path,
        time_course_mode: bool,
        user_replicates: Optional[List[int]] = None,
        auto_parse_groups: bool = True,
        user_group_labels: Optional[List[str]] = None,
        user_groups: Optional[List[int]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        completion_callback: Optional[Callable[[ProcessingResult], None]] = None
    ) -> bool:
        """
        Start asynchronous processing.
        
        Returns:
            True if processing started successfully, False otherwise
        """
        # Check if already processing
        if self._worker and self._worker.isRunning():
            logger.warning("Processing already in progress")
            return False
            
        # Create task
        self._current_task = ProcessingTask(
            input_paths=input_paths,
            output_dir=output_dir,
            time_course_mode=time_course_mode,
            user_replicates=user_replicates,
            auto_parse_groups=auto_parse_groups,
            user_group_labels=user_group_labels,
            user_groups=user_groups
        )
        
        # Create and configure worker
        self._worker = ProcessingWorker(self)
        self._worker.set_task(self._current_task)
        
        # Connect signals
        if progress_callback:
            self._worker.progress_updated.connect(progress_callback)
        if status_callback:
            self._worker.status_updated.connect(status_callback)
        if completion_callback:
            self._worker.processing_completed.connect(completion_callback)
            
        # Connect internal handlers
        self._worker.error_occurred.connect(self._on_error)
        self._worker.state_changed.connect(self._on_state_changed)
        
        # Start processing
        self._worker.start()
        return True
        
    def cancel_processing(self) -> None:
        """Cancel current processing operation."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(5000)  # Wait up to 5 seconds
            if self._worker.isRunning():
                logger.warning("Worker did not stop gracefully, terminating")
                self._worker.terminate()
                self._worker.wait()
                
    def pause_processing(self) -> None:
        """Pause current processing operation."""
        if self._worker:
            self._worker.pause()
            
    def resume_processing(self) -> None:
        """Resume paused processing operation."""
        if self._worker:
            self._worker.resume()
            
    def is_processing(self) -> bool:
        """Check if processing is currently active."""
        return self._worker is not None and self._worker.isRunning()
        
    def get_state(self) -> ProcessingState:
        """Get current processing state."""
        if self._worker:
            return self._worker.state
        return ProcessingState.IDLE
        
    @Slot(str)
    def _on_error(self, error_msg: str) -> None:
        """Handle error signals from worker."""
        logger.error(f"Processing error: {error_msg}")
        
    @Slot(ProcessingState)
    def _on_state_changed(self, state: ProcessingState) -> None:
        """Handle state change signals from worker."""
        logger.info(f"Processing state changed to: {state.name}")
        
    def cleanup(self) -> None:
        """Clean up resources."""
        self.cancel_processing()
        if self._worker:
            self._worker.deleteLater()
            self._worker = None