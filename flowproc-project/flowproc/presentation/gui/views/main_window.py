# File: flowproc/presentation/gui/views/main_window.py
"""
Refactored main window that delegates responsibilities to focused modules.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QSizePolicy, QVBoxLayout, QWidget

from .components.ui_builder import UIBuilder
from .components.event_handler import EventHandler
from .components.state_manager import StateManager
from .components.processing_coordinator import ProcessingCoordinator
from .components.file_manager import FileManager
from .mixins.styling_mixin import StylingMixin
from .mixins.validation_mixin import ValidationMixin
from ..workers.processing_worker import ProcessingResult

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow, StylingMixin, ValidationMixin):
    """
    Main application window with delegated responsibilities.
    
    This refactored main window focuses solely on:
    - Window lifecycle management
    - High-level coordination between components
    - Qt-specific window behavior
    """

    def __init__(self) -> None:
        super().__init__()
        
        # Initialize core components
        self.state_manager = StateManager()
        self.file_manager = FileManager(self.state_manager)
        self.ui_builder = UIBuilder(self)
        self.processing_coordinator = ProcessingCoordinator(self, self.state_manager)
        self.event_handler = EventHandler(
            self, 
            self.state_manager, 
            self.file_manager, 
            self.processing_coordinator
        )
        
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._center_window()

    def _setup_window(self) -> None:
        """Configure basic window properties."""
        self.setWindowTitle("Flow Cytometry Processor")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Setup styling and icon
        self.setup_styling()  # From StylingMixin

    def _setup_ui(self) -> None:
        """Initialize the user interface."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)
        
        # Build UI components
        self.ui_builder.build_complete_ui(self.main_layout)

    def _connect_signals(self) -> None:
        """Connect signals between components."""
        self.event_handler.connect_all_signals()
        self.processing_coordinator.connect_signals()

    def _center_window(self) -> None:
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.size()
            self.move(
                (screen_size.width() - self.width()) // 2,
                (screen_size.height() - self.height()) // 2
            )

    # Public interface for external coordination
    @property
    def preview_paths(self) -> List[str]:
        """Get current preview paths."""
        return self.state_manager.preview_paths

    @property
    def last_csv(self) -> Optional[Path]:
        """Get the last processed CSV file."""
        return self.state_manager.last_csv

    @property
    def current_group_labels(self) -> List[str]:
        """Get current group labels."""
        return self.state_manager.current_group_labels

    def is_processing(self) -> bool:
        """Check if processing is currently running."""
        return self.processing_coordinator.is_processing()

    # Qt Event handlers
    def closeEvent(self, event) -> None:
        """Handle window close event with proper cleanup."""
        if self.processing_coordinator.handle_close_request():
            self.processing_coordinator.cleanup()
            event.accept()
        else:
            event.ignore()

    # Signal handlers (called by processing coordinator)
    @Slot()
    def on_processing_started(self) -> None:
        """Handle processing start event."""
        self.ui_builder.set_processing_state(True)

    @Slot(ProcessingResult)
    def on_processing_completed(self, result: ProcessingResult) -> None:
        """Handle processing completion."""
        self.ui_builder.set_processing_state(False)
        self.event_handler.handle_processing_completion(result)

    @Slot(str)
    def on_processing_error(self, error_message: str) -> None:
        """Handle processing error."""
        self.ui_builder.set_processing_state(False)
        self.event_handler.handle_processing_error(error_message)

    @Slot(str)
    def on_validation_error(self, error_message: str) -> None:
        """Handle validation error."""
        self.event_handler.handle_validation_error(error_message)

    @Slot(int)
    def on_progress_updated(self, value: int) -> None:
        """Handle progress updates."""
        self.ui_builder.update_progress(value)

    @Slot(str)
    def on_status_updated(self, message: str) -> None:
        """Handle status updates."""
        self.ui_builder.update_status(message)