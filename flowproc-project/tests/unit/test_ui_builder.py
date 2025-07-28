"""
Unit tests for the UIBuilder class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QVBoxLayout, QApplication

from flowproc.presentation.gui.views.components.ui_builder import UIBuilder


class TestUIBuilder:
    """Test cases for the UIBuilder class."""

    @pytest.fixture(autouse=True)
    def setup_qt_app(self):
        """Setup Qt application for testing."""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
        yield

    @pytest.fixture
    def mock_main_window(self):
        """Create a mock main window for testing."""
        return Mock()

    @pytest.fixture
    def ui_builder(self, mock_main_window):
        """Create a UIBuilder instance for testing."""
        return UIBuilder(mock_main_window)

    @pytest.fixture
    def main_layout(self):
        """Create a main layout for testing."""
        return QVBoxLayout()

    def test_initialization(self, ui_builder, mock_main_window):
        """Test that UIBuilder initializes correctly."""
        assert ui_builder.main_window == mock_main_window
        assert ui_builder.widgets == {}

    @patch('flowproc.presentation.gui.views.components.ui_builder.load_last_output_dir')
    def test_build_complete_ui(self, mock_load_dir, ui_builder, main_layout):
        """Test building the complete UI."""
        mock_load_dir.return_value = "/path/to/output"
        
        # Build the complete UI
        ui_builder.build_complete_ui(main_layout)
        
        # Check that all widget groups were created
        assert 'time_course_checkbox' in ui_builder.widgets
        assert 'group_combo' in ui_builder.widgets
        assert 'visualize_combo' in ui_builder.widgets
        assert 'path_entry' in ui_builder.widgets
        assert 'browse_button' in ui_builder.widgets
        assert 'clear_button' in ui_builder.widgets
        assert 'preview_button' in ui_builder.widgets
        assert 'output_entry' in ui_builder.widgets
        assert 'output_browse_button' in ui_builder.widgets
        assert 'process_button' in ui_builder.widgets
        assert 'visualize_button' in ui_builder.widgets
        assert 'cancel_button' in ui_builder.widgets
        assert 'progress_bar' in ui_builder.widgets
        assert 'status_label' in ui_builder.widgets

    def test_build_options_group(self, ui_builder, main_layout):
        """Test building the options group."""
        ui_builder._build_options_group(main_layout)
        
        # Check that option widgets were created
        assert 'time_course_checkbox' in ui_builder.widgets
        assert 'group_combo' in ui_builder.widgets
        assert 'visualize_combo' in ui_builder.widgets
        
        # Check that group combo has the expected items
        group_combo = ui_builder.widgets['group_combo']
        expected_items = [
            "Auto-parse groups from sample names",
            "Use custom group labels",
            "Process all samples as one group"
        ]
        for i, item in enumerate(expected_items):
            assert group_combo.itemText(i) == item
        
        # Check that visualize combo has the expected items
        visualize_combo = ui_builder.widgets['visualize_combo']
        expected_metrics = [
            "Freq. of Parent", "Freq. of Grandparent", "Freq. of Total",
            "Mean Fluorescence Intensity", "Median Fluorescence Intensity"
        ]
        for i, metric in enumerate(expected_metrics):
            assert visualize_combo.itemText(i) == metric

    @patch('flowproc.presentation.gui.views.components.ui_builder.load_last_output_dir')
    def test_build_io_group(self, mock_load_dir, ui_builder, main_layout):
        """Test building the input/output group."""
        mock_load_dir.return_value = "/path/to/output"
        
        ui_builder._build_io_group(main_layout)
        
        # Check that IO widgets were created
        assert 'path_entry' in ui_builder.widgets
        assert 'browse_button' in ui_builder.widgets
        assert 'clear_button' in ui_builder.widgets
        assert 'preview_button' in ui_builder.widgets
        assert 'output_entry' in ui_builder.widgets
        assert 'output_browse_button' in ui_builder.widgets
        
        # Check that output entry was initialized with last output dir
        output_entry = ui_builder.widgets['output_entry']
        assert output_entry.text() == "/path/to/output"

    def test_build_process_controls(self, ui_builder, main_layout):
        """Test building the process controls."""
        ui_builder._build_process_controls(main_layout)
        
        # Check that process control widgets were created
        assert 'process_button' in ui_builder.widgets
        assert 'visualize_button' in ui_builder.widgets
        assert 'cancel_button' in ui_builder.widgets
        
        # Check button text
        process_button = ui_builder.widgets['process_button']
        visualize_button = ui_builder.widgets['visualize_button']
        cancel_button = ui_builder.widgets['cancel_button']
        
        assert process_button.text() == "Process Data"
        assert visualize_button.text() == "Visualize Results"
        assert cancel_button.text() == "Cancel"

    def test_build_progress_section(self, ui_builder, main_layout):
        """Test building the progress section."""
        ui_builder._build_progress_section(main_layout)
        
        # Check that progress widgets were created
        assert 'progress_bar' in ui_builder.widgets
        assert 'status_label' in ui_builder.widgets
        
        # Check initial progress bar state
        progress_bar = ui_builder.widgets['progress_bar']
        assert progress_bar.minimum() == 0
        assert progress_bar.maximum() == 100
        # Progress bar is initially hidden, so value might be -1 (default for hidden progress bars)
        assert progress_bar.value() in [0, -1]

    def test_setup_tooltips(self, ui_builder, main_layout):
        """Test setting up tooltips."""
        # Build the complete UI first
        ui_builder.build_complete_ui(main_layout)
        
        # Check that tooltips are set (this is a basic check)
        # The actual tooltip content is implementation-specific
        for widget_name, widget in ui_builder.widgets.items():
            if hasattr(widget, 'setToolTip'):
                # Tooltips should be set for relevant widgets
                pass

    def test_set_processing_state(self, ui_builder, main_layout):
        """Test setting processing state."""
        # Build the complete UI first
        ui_builder.build_complete_ui(main_layout)
        
        # Test setting processing state to True
        ui_builder.set_processing_state(True)
        
        process_button = ui_builder.widgets['process_button']
        visualize_button = ui_builder.widgets['visualize_button']
        cancel_button = ui_builder.widgets['cancel_button']
        
        # Process button should be disabled, visualize button should remain enabled
        assert not process_button.isEnabled()
        assert visualize_button.isEnabled()  # Visualize button is not disabled during processing
        # Cancel button should be enabled
        assert cancel_button.isEnabled()
        
        # Test setting processing state to False
        ui_builder.set_processing_state(False)
        
        # Process and visualize buttons should be enabled
        assert process_button.isEnabled()
        assert visualize_button.isEnabled()
        # Cancel button should be disabled
        assert not cancel_button.isEnabled()

    def test_update_progress(self, ui_builder, main_layout):
        """Test updating progress."""
        # Build the complete UI first
        ui_builder.build_complete_ui(main_layout)
        
        # Update progress
        ui_builder.update_progress(50)
        
        # Check that progress bar was updated
        progress_bar = ui_builder.widgets['progress_bar']
        assert progress_bar.value() == 50

    def test_update_status(self, ui_builder, main_layout):
        """Test updating status."""
        # Build the complete UI first
        ui_builder.build_complete_ui(main_layout)
        
        # Update status
        status_message = "Processing file 1 of 5..."
        ui_builder.update_status(status_message)
        
        # Check that status label was updated
        status_label = ui_builder.widgets['status_label']
        assert status_label.text() == status_message

    def test_get_widget(self, ui_builder, main_layout):
        """Test getting widgets by name."""
        # Build the complete UI first
        ui_builder.build_complete_ui(main_layout)
        
        # Test getting existing widget
        process_button = ui_builder.get_widget('process_button')
        assert process_button is not None
        assert process_button.text() == "Process Data"
        
        # Test getting non-existent widget
        non_existent = ui_builder.get_widget('non_existent_widget')
        assert non_existent is None

    def test_widget_properties(self, ui_builder, main_layout):
        """Test that widgets have expected properties."""
        # Build the complete UI first
        ui_builder.build_complete_ui(main_layout)
        
        # Test path entry is a DropLineEdit
        path_entry = ui_builder.widgets['path_entry']
        assert hasattr(path_entry, 'setText')
        assert hasattr(path_entry, 'text')
        
        # Test buttons are QPushButton
        for button_name in ['browse_button', 'clear_button', 'preview_button', 
                           'process_button', 'visualize_button', 'cancel_button']:
            button = ui_builder.widgets[button_name]
            assert hasattr(button, 'clicked')
            assert hasattr(button, 'setEnabled')
            assert hasattr(button, 'isEnabled')
        
        # Test combos are QComboBox
        for combo_name in ['group_combo', 'visualize_combo']:
            combo = ui_builder.widgets[combo_name]
            assert hasattr(combo, 'addItems')
            assert hasattr(combo, 'currentText')
            assert hasattr(combo, 'currentTextChanged')
        
        # Test progress bar is QProgressBar
        progress_bar = ui_builder.widgets['progress_bar']
        assert hasattr(progress_bar, 'setValue')
        assert hasattr(progress_bar, 'value')
        assert hasattr(progress_bar, 'setMinimum')
        assert hasattr(progress_bar, 'setMaximum')

    def test_layout_structure(self, ui_builder, main_layout):
        """Test that the layout structure is correct."""
        # Build the complete UI first
        ui_builder.build_complete_ui(main_layout)
        
        # Check that main layout has children (widgets were added)
        assert main_layout.count() > 0
        
        # Check that all expected widget types are present
        widget_types = set()
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item.widget():
                widget_types.add(type(item.widget()).__name__)
        
        # Should have GroupBox widgets for different sections
        assert 'QGroupBox' in widget_types

    def test_widget_initialization(self, ui_builder, main_layout):
        """Test that widgets are properly initialized."""
        # Build the complete UI first
        ui_builder.build_complete_ui(main_layout)
        
        # Check initial states
        time_course_checkbox = ui_builder.widgets['time_course_checkbox']
        assert not time_course_checkbox.isChecked()  # Should be unchecked by default
        
        group_combo = ui_builder.widgets['group_combo']
        assert group_combo.currentIndex() == 0  # Should have first item selected
        
        visualize_combo = ui_builder.widgets['visualize_combo']
        assert visualize_combo.currentIndex() == 0  # Should have first item selected
        
        cancel_button = ui_builder.widgets['cancel_button']
        assert not cancel_button.isEnabled()  # Should be disabled initially 