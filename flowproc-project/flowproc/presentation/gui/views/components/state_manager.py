# File: flowproc/presentation/gui/views/components/state_manager.py
"""
State management for the main window.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class WindowState:
    """Container for main window state."""
    preview_paths: List[str] = field(default_factory=list)
    last_csv: Optional[Path] = None
    current_group_labels: List[str] = field(default_factory=list)
    is_processing: bool = False
    last_output_dir: Optional[str] = None


class StateManager:
    """
    Manages the application state for the main window.
    
    Centralizes state management to avoid scattered state across the UI.
    """

    def __init__(self, main_window=None) -> None:
        self._state = WindowState()
        self._state_observers: List[callable] = []
        self.main_window = main_window

    @property
    def preview_paths(self) -> List[str]:
        """Get current preview paths."""
        return self._state.preview_paths.copy()

    @preview_paths.setter
    def preview_paths(self, paths: List[str]) -> None:
        """Set preview paths and notify observers."""
        self._state.preview_paths = paths.copy()
        self._notify_observers('preview_paths')
        logger.debug(f"Preview paths updated: {len(paths)} paths")

    @property
    def last_csv(self) -> Optional[Path]:
        """Get the last processed CSV file."""
        return self._state.last_csv

    @last_csv.setter
    def last_csv(self, path: Optional[Path]) -> None:
        """Set the last CSV file."""
        self._state.last_csv = path
        self._notify_observers('last_csv')
        logger.debug(f"Last CSV updated: {path}")

    @property
    def current_group_labels(self) -> List[str]:
        """Get current group labels."""
        return self._state.current_group_labels.copy()

    @current_group_labels.setter
    def current_group_labels(self, labels: List[str]) -> None:
        """Set current group labels."""
        self._state.current_group_labels = labels.copy()
        self._notify_observers('current_group_labels')
        logger.debug(f"Group labels updated: {labels}")

    @property
    def is_processing(self) -> bool:
        """Check if processing is active."""
        return self._state.is_processing

    @is_processing.setter
    def is_processing(self, value: bool) -> None:
        """Set processing state."""
        self._state.is_processing = value
        self._notify_observers('is_processing')
        logger.debug(f"Processing state: {value}")

    @property
    def last_output_dir(self) -> Optional[str]:
        """Get the last output directory."""
        return self._state.last_output_dir

    @last_output_dir.setter
    def last_output_dir(self, path: Optional[str]) -> None:
        """Set the last output directory."""
        self._state.last_output_dir = path
        self._notify_observers('last_output_dir')
        logger.debug(f"Last output directory updated: {path}")

    def clear_preview_data(self) -> None:
        """Clear all preview-related data."""
        self._state.preview_paths = []
        self._state.last_csv = None
        self._notify_observers('preview_data_cleared')
        logger.debug("Preview data cleared")

    def update_status(self, message: str) -> None:
        """Update status message (delegates to main window if available)."""
        # This method is called by event handlers to update the status
        # The actual status update is handled by the main window's UI builder
        logger.debug(f"Status update: {message}")

    def add_observer(self, observer: callable) -> None:
        """Add a state observer."""
        if observer not in self._state_observers:
            self._state_observers.append(observer)

    def remove_observer(self, observer: callable) -> None:
        """Remove a state observer."""
        if observer in self._state_observers:
            self._state_observers.remove(observer)

    def _notify_observers(self, event: str) -> None:
        """Notify all observers of a state change."""
        for observer in self._state_observers:
            try:
                observer(event, self._state)
            except Exception as e:
                logger.error(f"Error notifying observer {observer}: {e}")

    def get_state_snapshot(self) -> WindowState:
        """Get a snapshot of the current state."""
        return WindowState(
            preview_paths=self._state.preview_paths.copy(),
            last_csv=self._state.last_csv,
            current_group_labels=self._state.current_group_labels.copy(),
            is_processing=self._state.is_processing,
            last_output_dir=self._state.last_output_dir
        )

    def restore_state(self, state: WindowState) -> None:
        """Restore state from a snapshot."""
        self._state = state
        self._notify_observers('state_restored')
        logger.debug("State restored from snapshot")
