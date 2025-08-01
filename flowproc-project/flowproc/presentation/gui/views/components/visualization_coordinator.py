"""
Visualization Coordinator

This coordinator manages the interaction between the options dialog and display dialog
for a clean separation of visualization configuration and display.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QDialog
from PySide6.QtCore import QObject, Signal

from ..dialogs.visualization_options_dialog import VisualizationOptionsDialog, VisualizationOptions
from ..dialogs.visualization_display_dialog import VisualizationDisplayDialog

logger = logging.getLogger(__name__)


class VisualizationCoordinator(QObject):
    """
    Coordinates visualization options configuration and plot display.
    
    This class manages the workflow between:
    1. Options configuration dialog
    2. Plot display dialog
    """
    
    # Signals
    visualization_started = Signal()
    visualization_completed = Signal()
    visualization_error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.options_dialog: Optional[VisualizationOptionsDialog] = None
        self.display_dialog: Optional[VisualizationDisplayDialog] = None
        self.current_csv_path: Optional[Path] = None
    
    def start_visualization(self, csv_path: Path, parent_widget=None):
        """
        Start the visualization workflow.
        
        Args:
            csv_path: Path to the CSV file to visualize
            parent_widget: Parent widget for dialogs
        """
        try:
            self.current_csv_path = csv_path
            self.visualization_started.emit()
            
            # Show options dialog first
            self._show_options_dialog(parent_widget)
            
        except Exception as e:
            error_msg = f"Failed to start visualization: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.visualization_error.emit(error_msg)
    
    def update_visualization(self, options: VisualizationOptions):
        """
        Update the current visualization with new options.
        
        Args:
            options: New visualization options
        """
        try:
            if self.display_dialog and self.display_dialog.isVisible():
                self.display_dialog.set_options(options)
                logger.info("Visualization updated with new options")
            else:
                logger.warning("No active visualization dialog to update")
                
        except Exception as e:
            error_msg = f"Failed to update visualization: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.visualization_error.emit(error_msg)
    
    def _show_options_dialog(self, parent_widget=None):
        """Show the options configuration dialog."""
        try:
            # Create options dialog
            self.options_dialog = VisualizationOptionsDialog(
                parent=parent_widget,
                csv_path=self.current_csv_path
            )
            
            # Connect the options configured signal
            self.options_dialog.options_configured.connect(self._on_options_configured)
            
            # Show the dialog
            result = self.options_dialog.exec()
            
            if result != QDialog.DialogCode.Accepted:
                # User cancelled
                self.visualization_completed.emit()
                
        except Exception as e:
            error_msg = f"Failed to show options dialog: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.visualization_error.emit(error_msg)
    
    # Removed show_options_dialog method - no longer needed with inline configuration
    
    def _on_options_configured(self, options: VisualizationOptions):
        """Handle options configuration completion."""
        try:
            # Show the display dialog with the configured options
            self._show_display_dialog(options)
            
        except Exception as e:
            error_msg = f"Failed to process options: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.visualization_error.emit(error_msg)
    
    def _show_display_dialog(self, options: VisualizationOptions):
        """Show the plot display dialog."""
        try:
            # If display dialog already exists, update it with new options
            if self.display_dialog and self.display_dialog.isVisible():
                self.display_dialog.set_options(options)
                return
            
            # Create new display dialog
            self.display_dialog = VisualizationDisplayDialog(
                parent=self.options_dialog.parent() if self.options_dialog else None,
                csv_path=self.current_csv_path,
                options=options
            )
            
            # Connect the plot generated signal
            self.display_dialog.plot_generated.connect(self._on_plot_generated)
            
            # Show the dialog (non-modal)
            self.display_dialog.show()
            
            # Emit completed signal since dialog is now open
            self.visualization_completed.emit()
            
        except Exception as e:
            error_msg = f"Failed to show display dialog: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.visualization_error.emit(error_msg)
    
    def _on_plot_generated(self):
        """Handle plot generation completion."""
        logger.info("Plot generated successfully")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.options_dialog:
                self.options_dialog.deleteLater()
                self.options_dialog = None
            
            if self.display_dialog:
                self.display_dialog.deleteLater()
                self.display_dialog = None
                
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}") 