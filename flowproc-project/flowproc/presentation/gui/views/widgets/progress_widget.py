"""
Custom Progress Widget for displaying processing progress.

This widget provides a more sophisticated progress display with
status messages, time estimates, and visual feedback.
"""

import time
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, 
    QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPalette, QColor

class ProgressWidget(QWidget):
    """
    Custom progress widget with enhanced features.
    
    Features:
    - Progress bar with percentage display
    - Status message display
    - Time elapsed/remaining estimates
    - Cancel button
    - Visual styling
    """
    
    # Signals
    cancel_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.start_time: Optional[float] = None
        self.last_progress = 0
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_time_display)
        
        self._setup_ui()
        self._setup_styling()
        
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Time and controls frame
        time_controls_frame = QFrame()
        time_controls_layout = QHBoxLayout(time_controls_frame)
        time_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Time display
        self.time_label = QLabel("Time: --:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        
        time_controls_layout.addWidget(self.time_label)
        time_controls_layout.addStretch()
        time_controls_layout.addWidget(self.cancel_button)
        
        # Add widgets to main layout
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(time_controls_frame)
        
    def _setup_styling(self) -> None:
        """Apply custom styling to the widget."""
        # Set dark theme colors
        self.setStyleSheet("""
            QProgressWidget {
                background-color: #2b2b2b;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 3px;
                text-align: center;
                background-color: #1e1e1e;
            }
            
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
            
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                color: #ffffff;
                padding: 5px 15px;
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
        """)
        
    def start_progress(self, status_message: str = "Processing...") -> None:
        """
        Start the progress tracking.
        
        Args:
            status_message: Initial status message to display
        """
        self.start_time = time.time()
        self.last_progress = 0
        self.progress_bar.setValue(0)
        self.status_label.setText(status_message)
        self.cancel_button.setEnabled(True)
        self.update_timer.start(1000)  # Update every second
        
    def update_progress(self, value: int, status_message: Optional[str] = None) -> None:
        """
        Update the progress display.
        
        Args:
            value: Progress value (0-100)
            status_message: Optional status message to update
        """
        self.progress_bar.setValue(value)
        self.last_progress = value
        
        if status_message:
            self.status_label.setText(status_message)
            
    def complete_progress(self, status_message: str = "Completed") -> None:
        """
        Mark progress as complete.
        
        Args:
            status_message: Final status message
        """
        self.progress_bar.setValue(100)
        self.status_label.setText(status_message)
        self.cancel_button.setEnabled(False)
        self.update_timer.stop()
        
    def reset_progress(self) -> None:
        """Reset the progress widget to initial state."""
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        self.time_label.setText("Time: --:--")
        self.cancel_button.setEnabled(False)
        self.update_timer.stop()
        self.start_time = None
        self.last_progress = 0
        
    def _update_time_display(self) -> None:
        """Update the time display with elapsed time and estimates."""
        if self.start_time is None:
            return
            
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)
        
        if self.last_progress > 0:
            # Estimate remaining time
            if self.last_progress < 100:
                estimated_total = elapsed * 100 / self.last_progress
                remaining = estimated_total - elapsed
                remaining_str = self._format_time(remaining)
                time_text = f"Time: {elapsed_str} / Est. remaining: {remaining_str}"
            else:
                time_text = f"Time: {elapsed_str}"
        else:
            time_text = f"Time: {elapsed_str}"
            
        self.time_label.setText(time_text)
        
    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
        
    def set_cancel_enabled(self, enabled: bool) -> None:
        """Enable or disable the cancel button."""
        self.cancel_button.setEnabled(enabled)
        
    def is_progress_active(self) -> bool:
        """Check if progress tracking is currently active."""
        return self.start_time is not None and self.update_timer.isActive()