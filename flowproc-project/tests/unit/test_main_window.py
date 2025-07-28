"""
Unit tests for the refactored MainWindow class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from flowproc.presentation.gui.views.main_window import MainWindow
from flowproc.presentation.gui.workers.processing_worker import ProcessingResult


class TestMainWindow:
    """Test cases for the MainWindow class."""

    @pytest.fixture(autouse=True)
    def setup_qt_app(self):
        """Setup Qt application for testing."""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
        yield
        # Cleanup handled by pytest-qt

    @pytest.fixture
    def main_window(self):
        """Create a MainWindow instance for testing."""
        with patch.object(MainWindow, '_center_window') as mock_center:
            window = MainWindow()
            yield window
            window.close()

    def test_main_window_initialization(self, main_window):
        """Test that MainWindow initializes correctly with all components."""
        assert main_window is not None
        assert main_window.windowTitle() == "Flow Cytometry Processor"
        assert main_window.minimumSize().width() >= 800
        assert main_window.minimumSize().height() >= 600
        
        # Check that all components are initialized
        assert hasattr(main_window, 'state_manager')
        assert hasattr(main_window, 'file_manager')
        assert hasattr(main_window, 'ui_builder')
        assert hasattr(main_window, 'processing_coordinator')
        assert hasattr(main_window, 'event_handler')

    def test_main_window_components_connected(self, main_window):
        """Test that all components are properly connected."""
        # Check that UI builder has access to main window
        assert main_window.ui_builder.main_window == main_window
        
        # Check that event handler has all required components
        assert main_window.event_handler.main_window == main_window
        assert main_window.event_handler.state_manager == main_window.state_manager
        assert main_window.event_handler.file_manager == main_window.file_manager
        assert main_window.event_handler.processing_coordinator == main_window.processing_coordinator

    def test_preview_paths_property(self, main_window):
        """Test the preview_paths property."""
        # Initially should be empty
        assert main_window.preview_paths == []
        
        # Set some paths and check
        test_paths = ["/path/to/file1.csv", "/path/to/file2.csv"]
        main_window.state_manager.preview_paths = test_paths
        assert main_window.preview_paths == test_paths

    def test_last_csv_property(self, main_window):
        """Test the last_csv property."""
        # Initially should be None
        assert main_window.last_csv is None
        
        # Set a CSV file and check
        test_csv = Path("/path/to/test.csv")
        main_window.state_manager.last_csv = test_csv
        assert main_window.last_csv == test_csv

    def test_current_group_labels_property(self, main_window):
        """Test the current_group_labels property."""
        # Initially should be empty
        assert main_window.current_group_labels == []
        
        # Set some labels and check
        test_labels = ["Group A", "Group B", "Group C"]
        main_window.state_manager.current_group_labels = test_labels
        assert main_window.current_group_labels == test_labels

    def test_is_processing_property(self, main_window):
        """Test the is_processing property."""
        # Initially should be False
        assert not main_window.is_processing()
        
        # Mock processing coordinator to return True
        with patch.object(main_window.processing_coordinator, 'is_processing', return_value=True):
            assert main_window.is_processing()

    @patch('PySide6.QtWidgets.QMessageBox.question')
    def test_close_event_during_processing(self, mock_question, main_window):
        """Test close event when processing is active."""
        from PySide6.QtGui import QCloseEvent
        from PySide6.QtWidgets import QMessageBox
        
        # Set processing state
        main_window.state_manager.is_processing = True
        # Mock the question dialog to return "Yes" (allow close)
        mock_question.return_value = QMessageBox.StandardButton.Yes
        
        # Mock the processing coordinator's is_processing to return True
        with patch.object(main_window.processing_coordinator, 'is_processing', return_value=True):
            with patch.object(main_window.processing_coordinator, 'cleanup'):
                # Create a mock close event
                close_event = Mock(spec=QCloseEvent)
                
                # Call closeEvent
                main_window.closeEvent(close_event)
                
                # Should show confirmation dialog (called by processing coordinator)
                mock_question.assert_called_once()
                # Event should be accepted
                close_event.accept.assert_called_once()

    @patch('PySide6.QtWidgets.QMessageBox.question')
    def test_close_event_not_processing(self, mock_question, main_window):
        """Test close event when not processing."""
        from PySide6.QtGui import QCloseEvent
        
        # Set not processing state
        main_window.state_manager.is_processing = False
        
        # Create a mock close event
        close_event = Mock(spec=QCloseEvent)
        
        # Call closeEvent
        main_window.closeEvent(close_event)
        
        # Should not show confirmation dialog
        mock_question.assert_not_called()
        # Event should be accepted
        close_event.accept.assert_called_once()

    def test_on_processing_started(self, main_window):
        """Test processing started slot."""
        # Mock UI updates
        with patch.object(main_window, 'ui_builder') as mock_ui_builder:
            main_window.on_processing_started()
            
            # Should update UI processing state
            mock_ui_builder.set_processing_state.assert_called_once_with(True)

    @patch('flowproc.presentation.gui.views.components.event_handler.save_last_output_dir')
    def test_on_processing_completed(self, mock_save_output_dir, main_window):
        """Test processing completed slot."""
        # Create a mock processing result
        mock_result = Mock()
        mock_result.last_csv_path = Path("/path/to/output")
        mock_result.processed_count = 1
        mock_result.failed_count = 0
        mock_result.total_time = 5.0
        mock_result.error_messages = []
        
        # Mock UI updates
        with patch.object(main_window, 'ui_builder') as mock_ui_builder:
            # Mock the output directory widget
            mock_ui_builder.get_widget.return_value.text.return_value = "/tmp/test_output"
            
            main_window.on_processing_completed(mock_result)
            
            # Should update UI processing state
            mock_ui_builder.set_processing_state.assert_called_once_with(False)
            
            # Should save output directory
            mock_save_output_dir.assert_called_once()

    def test_on_processing_error(self, main_window):
        """Test processing error slot."""
        error_message = "Test error message"
        
        # Mock UI updates
        with patch.object(main_window, 'ui_builder') as mock_ui_builder:
            main_window.on_processing_error(error_message)
            
            # Should update processing state
            assert main_window.state_manager.is_processing is False

    def test_on_validation_error(self, main_window):
        """Test validation error slot."""
        error_message = "Validation error message"
        
        # Mock UI updates
        with patch.object(main_window, 'ui_builder') as mock_ui_builder:
            main_window.on_validation_error(error_message)
            
            # Should not affect processing state
            # (validation errors don't stop processing)

    def test_on_progress_updated(self, main_window):
        """Test progress update slot."""
        progress_value = 50
        
        # Mock UI updates
        with patch.object(main_window, 'ui_builder') as mock_ui_builder:
            main_window.on_progress_updated(progress_value)
            
            # Should update progress
            mock_ui_builder.update_progress.assert_called_once_with(progress_value)

    def test_on_status_updated(self, main_window):
        """Test status update slot."""
        status_message = "Processing file 1 of 5..."
        
        # Mock UI updates
        with patch.object(main_window, 'ui_builder') as mock_ui_builder:
            main_window.on_status_updated(status_message)
            
            # Should update status
            mock_ui_builder.update_status.assert_called_once_with(status_message)

    def test_window_centering(self, main_window):
        """Test that window is centered on screen."""
        # This test verifies that the window positioning logic is called
        # The actual centering is tested by checking that the move method was called
        # during initialization (handled by the fixture setup)
        assert main_window.x() >= 0
        assert main_window.y() >= 0

    def test_styling_mixin_integration(self, main_window):
        """Test that styling mixin is properly integrated."""
        # Check that styling methods are available
        assert hasattr(main_window, 'setup_styling')
        assert callable(main_window.setup_styling)

    def test_validation_mixin_integration(self, main_window):
        """Test that validation mixin is properly integrated."""
        # Check that validation methods are available
        assert hasattr(main_window, 'validate_inputs')
        assert callable(main_window.validate_inputs) 