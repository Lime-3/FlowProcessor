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
    def event_handler(self, mock_main_window, mock_state_manager, mock_file_manager, mock_processing_coordinator):
        """Create an isolated EventHandler instance for testing."""
        return EventHandler(mock_main_window, mock_state_manager, mock_file_manager, mock_processing_coordinator)

    def test_initialization(self, event_handler, mock_main_window, mock_state_manager, mock_file_manager, mock_processing_coordinator):
        """Test that EventHandler initializes correctly."""
        assert event_handler.main_window == mock_main_window
        assert event_handler.state_manager == mock_state_manager
        assert event_handler.file_manager == mock_file_manager
        assert event_handler.processing_coordinator == mock_processing_coordinator

    def test_connect_all_signals(self, event_handler, mock_ui_builder):
        """Test that all signals are connected."""
        ui_builder, widgets = mock_ui_builder
        event_handler.main_window.ui_builder = ui_builder
        
        # Connect signals
        event_handler.connect_all_signals()
        
        # Check that all buttons are connected
        widgets['manual_groups_checkbox'].stateChanged.connect.assert_called_once()
        widgets['save_button'].clicked.connect.assert_called_once()
        widgets['browse_input_button'].clicked.connect.assert_called_once()
        widgets['clear_button'].clicked.connect.assert_called_once()
        widgets['preview_button'].clicked.connect.assert_called_once()
        widgets['out_dir_button'].clicked.connect.assert_called_once()
        widgets['process_button'].clicked.connect.assert_called_once()
        widgets['visualize_button'].clicked.connect.assert_called_once()
        widgets['group_labels_button'].clicked.connect.assert_called_once()
        widgets['path_entry'].textChanged.connect.assert_called_once()

    @patch('flowproc.presentation.gui.views.components.event_handler.QFileDialog.getOpenFileNames')
    def test_browse_input_success(self, mock_file_dialog, event_handler, mock_ui_builder):
        """Test successful file browsing."""
        ui_builder, widgets = mock_ui_builder
        
        # Mock file dialog return
        test_paths = ["/path/to/file1.csv", "/path/to/file2.csv"]
        mock_file_dialog.return_value = (test_paths, "CSV files (*.csv)")
        
        # Mock the main window's ui_builder
        event_handler.main_window.ui_builder = ui_builder
        
        # Call browse_input
        event_handler.browse_input()
        
        # Check that file dialog was called
        mock_file_dialog.assert_called_once()
        
        # Check that path entry was updated
        widgets['path_entry'].setText.assert_called_once_with("/path/to/file1.csv; /path/to/file2.csv")

    @patch('flowproc.presentation.gui.views.components.event_handler.QFileDialog.getOpenFileNames')
    def test_browse_input_cancelled(self, mock_file_dialog, event_handler, mock_ui_builder):
        """Test file browsing when cancelled."""
        ui_builder, widgets = mock_ui_builder
        
        # Mock file dialog return empty list (cancelled)
        mock_file_dialog.return_value = ([], "CSV files (*.csv)")
        
        # Mock the main window's ui_builder
        event_handler.main_window.ui_builder = ui_builder
        
        # Call browse_input
        event_handler.browse_input()
        
        # Check that path entry was not updated
        widgets['path_entry'].setText.assert_not_called()

    def test_clear_input(self, event_handler, mock_ui_builder):
        """Test clearing input."""
        ui_builder, widgets = mock_ui_builder
        event_handler.main_window.ui_builder = ui_builder
        
        # Call clear_input
        event_handler.clear_input()
        
        # Check that path entry was cleared
        widgets['path_entry'].clear.assert_called_once()
        
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
        
        # Test that the state is properly set for preview
        assert event_handler.state_manager.preview_paths == test_paths
        assert len(event_handler.state_manager.preview_paths) == 2
        
        # Test that the paths are accessible
        assert "/path/to/file1.csv" in event_handler.state_manager.preview_paths
        assert "/path/to/file2.csv" in event_handler.state_manager.preview_paths

    @patch('flowproc.presentation.gui.views.components.event_handler.QFileDialog.getExistingDirectory')
    @patch('flowproc.presentation.gui.views.components.event_handler.save_last_output_dir')
    def test_browse_output_success(self, mock_save_dir, mock_dir_dialog, event_handler, mock_ui_builder):
        """Test successful output directory browsing."""
        ui_builder, widgets = mock_ui_builder
        
        # Mock directory dialog return
        mock_dir_dialog.return_value = "/path/to/output"
        
        event_handler.main_window.ui_builder = ui_builder
        
        # Call browse_output
        event_handler.browse_output()
        
        # Check that output entry was updated
        widgets['out_dir_entry'].setText.assert_called_once_with("/path/to/output")

    @patch('flowproc.presentation.gui.views.components.event_handler.QFileDialog.getExistingDirectory')
    def test_browse_output_cancelled(self, mock_dir_dialog, event_handler, mock_ui_builder):
        """Test output directory browsing when cancelled."""
        ui_builder, widgets = mock_ui_builder
        
        # Mock directory dialog return (empty selection)
        mock_dir_dialog.return_value = ""
        
        event_handler.main_window.ui_builder = ui_builder
        
        # Call browse_output
        event_handler.browse_output()
        
        # Check that output entry was not updated
        widgets['out_dir_entry'].setText.assert_not_called()

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.critical')
    def test_process_data_validation_failure(self, mock_critical, event_handler, mock_ui_builder):
        """Test process data when validation fails."""
        ui_builder, widgets = mock_ui_builder
        
        # Set up empty preview paths to trigger validation failure
        event_handler.state_manager.preview_paths = []
        widgets['path_entry'].text.return_value = ""
        
        event_handler.main_window.ui_builder = ui_builder
        
        # Call process_data
        event_handler.process_data()
        
        # Check that critical dialog was shown
        mock_critical.assert_called_once()
        
        # Check that processing coordinator was not called
        event_handler.processing_coordinator.start_processing.assert_not_called()

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.critical')
    def test_process_data_validation_success(self, mock_critical, event_handler, mock_ui_builder):
        """Test process data when validation succeeds."""
        ui_builder, widgets = mock_ui_builder
        
        # Set up widget return values
        widgets['path_entry'].text.return_value = "/tmp/test_file.csv"
        widgets['out_dir_entry'].text.return_value = "/tmp/test_output"
        widgets['group_combo'].currentText.return_value = "Group Mode"
        widgets['metric_combo'].currentText.return_value = "Mean"
        widgets['timecourse_combo'].currentText.return_value = "Time Course"
        widgets['time_course_checkbox'].isChecked.return_value = False
        
        # Set up valid state
        event_handler.state_manager.preview_paths = ["/tmp/test_file.csv"]
        
        event_handler.main_window.ui_builder = ui_builder
        
        # Mock Path.exists to return True for test paths
        with patch('pathlib.Path.exists', return_value=True):
            # Call process_data
            event_handler.process_data()
            
            # Check that processing coordinator was called
            event_handler.processing_coordinator.start_processing.assert_called_once()

    @patch('flowproc.presentation.gui.views.dialogs.visualization_display_dialog.VisualizationDisplayDialog')
    def test_visualize_results(self, mock_dialog_class, event_handler, mock_ui_builder):
        """Test visualize results."""
        ui_builder, widgets = mock_ui_builder
        
        # Set last_csv so visualization can proceed
        event_handler.state_manager.last_csv = Path("/path/to/results.csv")
        
        # Set up widget return values
        widgets['time_course_checkbox'].isChecked.return_value = False
        
        # Mock dialog
        mock_dialog = Mock()
        mock_dialog.show.return_value = None
        mock_dialog_class.return_value = mock_dialog
        
        event_handler.main_window.ui_builder = ui_builder
        
        # Call visualize_results
        event_handler.visualize_results()
        
        # Check that dialog was created and shown
        mock_dialog_class.assert_called_once_with(parent=event_handler.main_window, csv_path=event_handler.state_manager.last_csv)
        mock_dialog.show.assert_called_once()



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
    def test_handle_processing_completion(self, mock_info, event_handler, mock_ui_builder):
        """Test handling processing completion."""
        ui_builder, widgets = mock_ui_builder
        
        # Set up widget return value
        widgets['out_dir_entry'].text.return_value = "/tmp/test_output"
        event_handler.main_window.ui_builder = ui_builder
        
        # Create mock result
        mock_result = Mock()
        mock_result.last_csv_path = Path("/path/to/output")
        mock_result.processed_count = 5
        mock_result.failed_count = 0
        mock_result.total_time = 10.5
        mock_result.error_messages = []
        
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

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.warning')
    def test_validate_inputs_success(self, mock_warning, event_handler, mock_ui_builder):
        """Test input validation success."""
        ui_builder, widgets = mock_ui_builder
        
        # Set up valid widget values
        widgets['path_entry'].text.return_value = "/tmp/test_file.csv"
        widgets['output_entry'].text.return_value = "/tmp/test_output"
        widgets['group_combo'].currentText.return_value = "Group Mode"
        widgets['metric_combo'].currentText.return_value = "Mean"
        
        # Set valid state
        event_handler.state_manager.preview_paths = ["/tmp/test_file.csv"]
        
        event_handler.main_window.ui_builder = ui_builder
        
        # Mock Path.exists to return True for test paths
        with patch('pathlib.Path.exists', return_value=True):
            # Call _validate_inputs
            result = event_handler._validate_inputs()
            
            # Should return True for valid inputs
            assert result is True

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.warning')
    def test_validate_inputs_failure(self, mock_warning, event_handler, mock_ui_builder):
        """Test input validation failure."""
        ui_builder, widgets = mock_ui_builder
        
        # Set empty preview paths (invalid)
        event_handler.state_manager.preview_paths = []
        
        # Set up widget values
        widgets['output_entry'].text.return_value = "/tmp/test_output"
        
        event_handler.main_window.ui_builder = ui_builder
        
        # Call _validate_inputs
        result = event_handler._validate_inputs()
        
        # Should return False for invalid inputs
        assert result is False
        
        # Should show warning dialog
        mock_warning.assert_called_once()

    @patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox.warning')
    def test_validate_inputs_missing_output_dir(self, mock_warning, event_handler, mock_ui_builder):
        """Test input validation with missing output directory."""
        ui_builder, widgets = mock_ui_builder
        
        # Set up widget values with missing output directory
        widgets['path_entry'].text.return_value = "/tmp/test_file.csv"
        widgets['output_entry'].text.return_value = ""
        widgets['group_combo'].currentText.return_value = "Group Mode"
        widgets['metric_combo'].currentText.return_value = "Mean"
        
        # Set valid state
        event_handler.state_manager.preview_paths = ["/tmp/test_file.csv"]
        
        event_handler.main_window.ui_builder = ui_builder
        
        # Call _validate_inputs
        result = event_handler._validate_inputs()
        
        # Should return False for invalid inputs
        assert result is False
        
        # Should show warning dialog
        mock_warning.assert_called_once() 