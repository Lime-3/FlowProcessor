"""
Unit tests for the EventHandler class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from flowproc.presentation.gui.views.components.event_handler import EventHandler


class TestEventHandler:
    """Test cases for the EventHandler class."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        main_window = Mock()
        state_manager = Mock()
        file_manager = Mock()
        processing_coordinator = Mock()
        
        return main_window, state_manager, file_manager, processing_coordinator

    @pytest.fixture
    def event_handler(self, mock_components):
        """Create an EventHandler instance for testing."""
        main_window, state_manager, file_manager, processing_coordinator = mock_components
        return EventHandler(main_window, state_manager, file_manager, processing_coordinator)

    def test_initialization(self, event_handler, mock_components):
        """Test that EventHandler initializes correctly."""
        main_window, state_manager, file_manager, processing_coordinator = mock_components
        
        assert event_handler.main_window == main_window
        assert event_handler.state_manager == state_manager
        assert event_handler.file_manager == file_manager
        assert event_handler.processing_coordinator == processing_coordinator

    def test_connect_all_signals(self, event_handler):
        """Test that all signals are connected."""
        # Mock UI builder and widgets
        mock_ui_builder = Mock()
        mock_widgets = {
            'browse_button': Mock(),
            'clear_button': Mock(),
            'preview_button': Mock(),
            'output_browse_button': Mock(),
            'process_button': Mock(),
            'visualize_button': Mock(),
            'cancel_button': Mock(),
            'group_combo': Mock()
        }
        
        mock_ui_builder.get_widget.side_effect = lambda name: mock_widgets[name]
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Connect signals
        event_handler.connect_all_signals()
        
        # Check that all buttons are connected
        mock_widgets['browse_button'].clicked.connect.assert_called_once()
        mock_widgets['clear_button'].clicked.connect.assert_called_once()
        mock_widgets['preview_button'].clicked.connect.assert_called_once()
        mock_widgets['output_browse_button'].clicked.connect.assert_called_once()
        mock_widgets['process_button'].clicked.connect.assert_called_once()
        mock_widgets['visualize_button'].clicked.connect.assert_called_once()
        mock_widgets['cancel_button'].clicked.connect.assert_called_once()
        mock_widgets['group_combo'].currentTextChanged.connect.assert_called_once()

    def test_browse_input_success(self, event_handler):
        """Test successful file browsing."""
        # Mock file manager to return paths
        test_paths = ["/path/to/file1.csv", "/path/to/file2.csv"]
        event_handler.file_manager.browse_input_files.return_value = test_paths
        
        # Mock UI builder
        mock_ui_builder = Mock()
        mock_path_entry = Mock()
        mock_ui_builder.get_widget.return_value = mock_path_entry
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call browse_input
        event_handler.browse_input()
        
        # Check that file manager was called
        event_handler.file_manager.browse_input_files.assert_called_once()
        
        # Check that path entry was updated
        mock_path_entry.setText.assert_called_once_with("/path/to/file1.csv; /path/to/file2.csv")
        
        # Check that state was updated
        assert event_handler.state_manager.preview_paths == test_paths

    def test_browse_input_cancelled(self, event_handler):
        """Test file browsing when cancelled."""
        # Mock file manager to return empty list (cancelled)
        event_handler.file_manager.browse_input_files.return_value = []
        
        # Mock UI builder
        mock_ui_builder = Mock()
        mock_path_entry = Mock()
        mock_ui_builder.get_widget.return_value = mock_path_entry
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call browse_input
        event_handler.browse_input()
        
        # Check that path entry was not updated
        mock_path_entry.setText.assert_not_called()

    def test_clear_input(self, event_handler):
        """Test clearing input."""
        # Mock UI builder
        mock_ui_builder = Mock()
        mock_path_entry = Mock()
        mock_ui_builder.get_widget.return_value = mock_path_entry
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call clear_input
        event_handler.clear_input()
        
        # Check that path entry was cleared
        mock_path_entry.clear.assert_called_once()
        
        # Check that state was cleared
        event_handler.state_manager.clear_preview_data.assert_called_once()

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.warning')
    def test_preview_csv_no_paths(self, mock_warning, event_handler):
        """Test preview CSV when no paths are available."""
        # Set empty preview paths
        event_handler.state_manager.preview_paths = []
        
        # Call preview_csv
        event_handler.preview_csv()
        
        # Check that warning was shown
        mock_warning.assert_called_once()
        args, kwargs = mock_warning.call_args
        assert "No valid CSV files available for preview" in args[2]  # The message is the third argument

    def test_preview_csv_with_paths(self, event_handler):
        """Test preview CSV when paths are available."""
        # Set preview paths
        test_paths = ["/path/to/file1.csv", "/path/to/file2.csv"]
        event_handler.state_manager.preview_paths = test_paths
        
        # Call preview_csv
        event_handler.preview_csv()
        
        # Check that file manager was called
        event_handler.file_manager.show_preview_dialog.assert_called_once_with(test_paths)

    @patch('flowproc.presentation.gui.views.components.event_handler.QFileDialog.getExistingDirectory')
    @patch('flowproc.presentation.gui.views.components.event_handler.save_last_output_dir')
    def test_browse_output_success(self, mock_save_dir, mock_dir_dialog, event_handler):
        """Test successful output directory browsing."""
        # Mock directory dialog return
        mock_dir_dialog.return_value = "/path/to/output"
        
        # Mock UI builder
        mock_ui_builder = Mock()
        mock_output_entry = Mock()
        mock_ui_builder.get_widget.return_value = mock_output_entry
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call browse_output
        event_handler.browse_output()
        
        # Check that output entry was updated
        mock_output_entry.setText.assert_called_once_with("/path/to/output")
        
        # Check that save function was called
        mock_save_dir.assert_called_once_with("/path/to/output")

    @patch('flowproc.presentation.gui.views.components.event_handler.QFileDialog.getExistingDirectory')
    def test_browse_output_cancelled(self, mock_dir_dialog, event_handler):
        """Test output directory browsing when cancelled."""
        # Mock directory dialog return (empty selection)
        mock_dir_dialog.return_value = ""
        
        # Mock UI builder
        mock_ui_builder = Mock()
        mock_output_entry = Mock()
        mock_ui_builder.get_widget.return_value = mock_output_entry
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call browse_output
        event_handler.browse_output()
        
        # Check that output entry was not updated
        mock_output_entry.setText.assert_not_called()

    def test_process_data_validation_failure(self, event_handler):
        """Test process data when validation fails."""
        # Mock validation to fail
        event_handler._validate_inputs = Mock(return_value=False)
        
        # Call process_data
        event_handler.process_data()
        
        # Check that processing coordinator was not called
        event_handler.processing_coordinator.start_processing.assert_not_called()

    def test_process_data_validation_success(self, event_handler):
        """Test process data when validation succeeds."""
        # Mock validation to succeed
        event_handler._validate_inputs = Mock(return_value=True)
        
        # Mock UI builder
        mock_ui_builder = Mock()
        mock_widgets = {
            'path_entry': Mock(text=lambda: "/path/to/file.csv"),
            'output_entry': Mock(text=lambda: "/path/to/output"),
            'group_combo': Mock(currentText=lambda: "Group Mode"),
            'metric_combo': Mock(currentText=lambda: "Mean"),
            'timecourse_combo': Mock(currentText=lambda: "Time Course"),
            'time_course_checkbox': Mock(isChecked=lambda: False)
        }
        mock_ui_builder.get_widget.side_effect = lambda name: mock_widgets[name]
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call process_data
        event_handler.process_data()
        
        # Check that processing coordinator was called
        event_handler.processing_coordinator.start_processing.assert_called_once()

    def test_visualize_results(self, event_handler):
        """Test visualize results."""
        # Set last_csv so visualization can proceed
        event_handler.state_manager.last_csv = Path("/path/to/results.csv")
        
        # Mock UI builder
        mock_ui_builder = Mock()
        mock_widgets = {
            'visualize_combo': Mock(currentText=lambda: "Mean"),
            'time_course_checkbox': Mock(isChecked=lambda: False)
        }
        mock_ui_builder.get_widget.side_effect = lambda name: mock_widgets[name]
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call visualize_results
        event_handler.visualize_results()
        
        # Check that processing coordinator was called
        event_handler.processing_coordinator.visualize_data.assert_called_once()

    def test_cancel_processing(self, event_handler):
        """Test cancel processing."""
        # Call cancel_processing
        event_handler.cancel_processing()
        
        # Check that processing coordinator was called
        event_handler.processing_coordinator.cancel_processing.assert_called_once()

    @patch('flowproc.presentation.gui.views.components.event_handler.GroupLabelsDialog')
    def test_on_group_mode_changed(self, mock_dialog_class, event_handler):
        """Test group mode change handling."""
        # Mock dialog
        mock_dialog = Mock()
        mock_dialog.exec.return_value = True
        mock_dialog.get_labels.return_value = ["Group A", "Group B"]
        mock_dialog_class.return_value = mock_dialog
        
        # Call on_group_mode_changed with custom group labels text
        event_handler.on_group_mode_changed("Use custom group labels")
        
        # Check that dialog was created and executed
        mock_dialog_class.assert_called_once_with(event_handler.main_window)
        mock_dialog.exec.assert_called_once()
        mock_dialog.get_labels.assert_called_once()
        
        # Check that state was updated
        assert event_handler.state_manager.current_group_labels == ["Group A", "Group B"]

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.information')
    def test_handle_processing_completion(self, mock_info, event_handler):
        """Test handling processing completion."""
        # Create mock result
        mock_result = Mock()
        mock_result.output_csv = Path("/path/to/output")
        mock_result.success = True
        
        # Call handle_processing_completion
        event_handler.handle_processing_completion(mock_result)
        
        # Check that state was updated
        assert event_handler.state_manager.last_csv == Path("/path/to/output")
        
        # Check that information dialog was shown
        mock_info.assert_called_once()

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.critical')
    def test_handle_processing_error(self, mock_critical, event_handler):
        """Test handling processing error."""
        error_message = "Processing failed"
        
        # Call handle_processing_error
        event_handler.handle_processing_error(error_message)
        
        # Check that critical dialog was shown
        mock_critical.assert_called_once()

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.warning')
    def test_handle_validation_error(self, mock_warning, event_handler):
        """Test handling validation error."""
        error_message = "Validation failed"
        
        # Call handle_validation_error
        event_handler.handle_validation_error(error_message)
        
        # Check that warning dialog was shown
        mock_warning.assert_called_once()

    def test_validate_inputs_success(self, event_handler):
        """Test input validation success."""
        # Mock UI builder with valid inputs
        mock_ui_builder = Mock()
        mock_widgets = {
            'path_entry': Mock(text=lambda: "/path/to/file.csv"),
            'output_entry': Mock(text=lambda: "/path/to/output"),
            'group_combo': Mock(currentText=lambda: "Group Mode"),
            'metric_combo': Mock(currentText=lambda: "Mean")
        }
        mock_ui_builder.get_widget.side_effect = lambda name: mock_widgets[name]
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call _validate_inputs
        result = event_handler._validate_inputs()
        
        # Should return True for valid inputs
        assert result is True

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.warning')
    def test_validate_inputs_failure(self, mock_warning, event_handler):
        """Test input validation failure."""
        # Set empty preview paths (invalid)
        event_handler.state_manager.preview_paths = []
        
        # Mock UI builder
        mock_ui_builder = Mock()
        mock_widgets = {
            'output_entry': Mock(text=lambda: "/path/to/output")
        }
        mock_ui_builder.get_widget.side_effect = lambda name: mock_widgets[name]
        event_handler.main_window.ui_builder = mock_ui_builder
        
        # Call _validate_inputs
        result = event_handler._validate_inputs()
        
        # Should return False for invalid inputs
        assert result is False
        
        # Should show warning dialog
        mock_warning.assert_called_once() 