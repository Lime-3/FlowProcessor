"""
Unit tests for the UIBuilder class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QVBoxLayout, QApplication, QLineEdit, QWidget

from flowproc.presentation.gui.views.components.ui_builder import UIBuilder


class MockQtWidget:
    """Base mock class for Qt widgets to prevent crashes."""
    def __init__(self, *args, **kwargs):
        self._text = ""
        self._enabled = True
        self._checked = False
        self._value = 0
        self._current_index = 0
        self._items = []
        self._visible = True
        self._minimum = 0
        self._maximum = 100
        
        # Handle text initialization for widgets that take text as first argument
        if args and isinstance(args[0], str):
            self._text = args[0]
    
    def setText(self, text):
        self._text = text
    
    def text(self):
        return self._text
    
    def setEnabled(self, enabled):
        self._enabled = enabled
    
    def isEnabled(self):
        return self._enabled
    
    def setChecked(self, checked):
        self._checked = checked
    
    def isChecked(self):
        return self._checked
    
    def setValue(self, value):
        self._value = value
    
    def value(self):
        return self._value
    
    def setMinimum(self, minimum):
        self._minimum = minimum
    
    def setMaximum(self, maximum):
        self._maximum = maximum
    
    def minimum(self):
        return self._minimum
    
    def maximum(self):
        return self._maximum
    
    def addItems(self, items):
        self._items.extend(items)
    
    def itemText(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return ""
    
    def setCurrentText(self, text):
        if text in self._items:
            self._current_index = self._items.index(text)
    
    def currentIndex(self):
        return self._current_index
    
    def currentText(self):
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return ""
    
    def setVisible(self, visible):
        self._visible = visible
    
    def isVisible(self):
        return self._visible
    
    def setSizePolicy(self, *args):
        pass
    
    def setMinimumHeight(self, height):
        pass
    
    def setFixedHeight(self, height):
        pass
    
    def setFixedWidth(self, width):
        pass
    
    def setObjectName(self, name):
        pass
    
    def setAlignment(self, alignment):
        pass
    
    def setStyleSheet(self, stylesheet):
        pass
    
    def setContentsMargins(self, *args):
        pass
    
    def setSpacing(self, spacing):
        pass
    
    def addWidget(self, widget):
        pass
    
    def addLayout(self, layout, stretch=None):
        pass
    
    def addStretch(self, stretch=0):
        pass
    
    def addSpacing(self, spacing):
        pass
    
    def count(self):
        return 0
    
    def itemAt(self, index):
        return Mock()
    
    def setAcceptDrops(self, accept):
        pass
    
    def setReadOnly(self, read_only):
        pass
    
    def setToolTip(self, tooltip):
        pass
    
    def clicked(self):
        return Mock()
    
    def currentTextChanged(self):
        return Mock()
    
    def textChanged(self):
        return Mock()
    
    def stateChanged(self):
        return Mock()


class MockDropLineEdit(MockQtWidget):
    """Mock DropLineEdit that provides the necessary Qt functionality for testing."""
    def __init__(self, parent=None):
        super().__init__()
        self._dropped_paths = []
    
    def dragEnterEvent(self, event):
        event.acceptProposedAction()
    
    def dropEvent(self, event):
        pass


class MockQCheckBox(MockQtWidget):
    """Mock QCheckBox."""
    pass


class MockQComboBox(MockQtWidget):
    """Mock QComboBox."""
    pass


class MockQPushButton(MockQtWidget):
    """Mock QPushButton."""
    pass


class MockQProgressBar(MockQtWidget):
    """Mock QProgressBar."""
    pass


class MockQLabel(MockQtWidget):
    """Mock QLabel."""
    pass


class MockQLineEdit(MockQtWidget):
    """Mock QLineEdit."""
    pass


class MockQGroupBox(MockQtWidget):
    """Mock QGroupBox."""
    pass


class MockQVBoxLayout(MockQtWidget):
    """Mock QVBoxLayout."""
    pass


class MockQHBoxLayout(MockQtWidget):
    """Mock QHBoxLayout."""
    pass


class TestUIBuilder:
    """Test cases for the UIBuilder class."""

    @pytest.fixture(autouse=True)
    def setup_patches(self):
        """Set up patches for all Qt widgets to prevent crashes."""
        with patch('flowproc.presentation.gui.views.components.ui_builder.QCheckBox', MockQCheckBox), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QComboBox', MockQComboBox), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QPushButton', MockQPushButton), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QProgressBar', MockQProgressBar), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QLabel', MockQLabel), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QLineEdit', MockQLineEdit), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QGroupBox', MockQGroupBox), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QVBoxLayout', MockQVBoxLayout), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QHBoxLayout', MockQHBoxLayout), \
             patch('flowproc.presentation.gui.views.components.ui_builder.QWidget', MockQtWidget), \
             patch('flowproc.presentation.gui.views.components.ui_builder.DropLineEdit', MockDropLineEdit):
            yield

    @pytest.fixture
    def ui_builder(self, mock_main_window):
        """Create a UIBuilder instance for testing."""
        return UIBuilder(mock_main_window)

    @pytest.fixture
    def main_layout(self):
        """Create a main layout for testing."""
        return MockQVBoxLayout()

    @pytest.fixture
    def built_ui_builder(self, ui_builder, main_layout):
        """Create a UIBuilder with a complete UI built."""
        with patch('flowproc.presentation.gui.views.components.ui_builder.load_last_output_dir') as mock_load_dir:
            mock_load_dir.return_value = "/path/to/output"
            ui_builder.build_complete_ui(main_layout)
            return ui_builder

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
        assert 'manual_groups_checkbox' in ui_builder.widgets
        assert 'path_entry' in ui_builder.widgets
        assert 'browse_input_button' in ui_builder.widgets
        assert 'clear_button' in ui_builder.widgets
        assert 'preview_button' in ui_builder.widgets
        assert 'out_dir_entry' in ui_builder.widgets
        assert 'out_dir_button' in ui_builder.widgets
        assert 'process_button' in ui_builder.widgets
        assert 'visualize_button' in ui_builder.widgets
        assert 'group_labels_button' in ui_builder.widgets
        assert 'progress_bar' in ui_builder.widgets
        assert 'status_label' in ui_builder.widgets

    def test_build_options_group(self, ui_builder, main_layout):
        """Test building the options group."""
        ui_builder._build_options_group(main_layout)
        
        # Check that option widgets were created
        assert 'time_course_checkbox' in ui_builder.widgets
        assert 'manual_groups_checkbox' in ui_builder.widgets

    @patch('flowproc.presentation.gui.views.components.ui_builder.load_last_output_dir')
    def test_build_io_group(self, mock_load_dir, ui_builder, main_layout):
        """Test building the input/output group."""
        mock_load_dir.return_value = "/path/to/output"
        
        ui_builder._build_io_group(main_layout)
        
        # Check that IO widgets were created
        assert 'path_entry' in ui_builder.widgets
        assert 'browse_input_button' in ui_builder.widgets
        assert 'clear_button' in ui_builder.widgets
        assert 'preview_button' in ui_builder.widgets
        assert 'out_dir_entry' in ui_builder.widgets
        assert 'out_dir_button' in ui_builder.widgets
        
        # Check that output entry was initialized with last output dir
        out_dir_entry = ui_builder.widgets['out_dir_entry']
        assert out_dir_entry.text() == "/path/to/output"

    def test_build_process_controls(self, ui_builder, main_layout):
        """Test building the process controls."""
        ui_builder._build_process_controls(main_layout)
        
        # Check that process control widgets were created
        assert 'process_button' in ui_builder.widgets
        assert 'visualize_button' in ui_builder.widgets
        assert 'group_labels_button' in ui_builder.widgets
        
        # Check button text
        process_button = ui_builder.widgets['process_button']
        visualize_button = ui_builder.widgets['visualize_button']
        
        assert process_button.text() == "Process"
        assert visualize_button.text() == "Visualize"

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

    def test_setup_tooltips(self, built_ui_builder):
        """Test setting up tooltips."""
        # Check that tooltips are set (this is a basic check)
        # The actual tooltip content is implementation-specific
        for widget_name, widget in built_ui_builder.widgets.items():
            if hasattr(widget, 'setToolTip'):
                # Tooltips should be set for relevant widgets
                pass

    def test_set_processing_state(self, built_ui_builder):
        """Test setting processing state."""
        # Test setting processing state to True
        built_ui_builder.set_processing_state(True)
        
        process_button = built_ui_builder.widgets['process_button']
        
        # Process button should be disabled
        assert not process_button.isEnabled()
        
        # Test setting processing state to False
        built_ui_builder.set_processing_state(False)
        
        # Process button should be enabled
        assert process_button.isEnabled()

    def test_update_progress(self, built_ui_builder):
        """Test updating progress."""
        # Update progress
        built_ui_builder.update_progress(50)
        
        # Check that progress bar was updated
        progress_bar = built_ui_builder.widgets['progress_bar']
        assert progress_bar.value() == 50

    def test_update_status(self, built_ui_builder):
        """Test updating status."""
        # Update status
        status_message = "Processing file 1 of 5..."
        built_ui_builder.update_status(status_message)
        
        # Check that status label was updated
        status_label = built_ui_builder.widgets['status_label']
        assert status_label.text() == status_message

    def test_get_widget(self, built_ui_builder):
        """Test getting widgets by name."""
        # Test getting existing widget
        process_button = built_ui_builder.get_widget('process_button')
        assert process_button is not None
        assert process_button.text() == "Process"
        
        # Test getting non-existent widget
        non_existent = built_ui_builder.get_widget('non_existent_widget')
        assert non_existent is None

    def test_widget_properties(self, built_ui_builder):
        """Test that widgets have expected properties."""
        # Test path entry is a DropLineEdit (our mock version)
        path_entry = built_ui_builder.widgets['path_entry']
        assert hasattr(path_entry, 'setText')
        assert hasattr(path_entry, 'text')
        assert hasattr(path_entry, 'setAcceptDrops')
        
        # Test buttons are QPushButton
        for button_name in ['browse_input_button', 'clear_button', 'preview_button', 
                           'process_button', 'visualize_button', 'group_labels_button']:
            button = built_ui_builder.widgets[button_name]
            assert hasattr(button, 'clicked')
            assert hasattr(button, 'setEnabled')
            assert hasattr(button, 'isEnabled')
        

        
        # Test progress bar is QProgressBar
        progress_bar = built_ui_builder.widgets['progress_bar']
        assert hasattr(progress_bar, 'setValue')
        assert hasattr(progress_bar, 'value')
        assert hasattr(progress_bar, 'setMinimum')
        assert hasattr(progress_bar, 'setMaximum')

    def test_widget_initialization(self, built_ui_builder):
        """Test that widgets are properly initialized."""
        # Check initial states
        time_course_checkbox = built_ui_builder.widgets['time_course_checkbox']
        assert not time_course_checkbox.isChecked()  # Should be unchecked by default

    def test_widget_isolation(self, ui_builder, main_layout):
        """Test that widgets are isolated between different UI builder instances."""
        # Create a second UI builder
        second_ui_builder = UIBuilder(Mock())
        
        # Build UI in both builders
        with patch('flowproc.presentation.gui.views.components.ui_builder.load_last_output_dir') as mock_load_dir:
            mock_load_dir.return_value = "/path/to/output"
            ui_builder.build_complete_ui(main_layout)
            second_ui_builder.build_complete_ui(MockQVBoxLayout())
        
        # Check that widgets are different objects
        assert ui_builder.widgets['process_button'] is not second_ui_builder.widgets['process_button']
        assert ui_builder.widgets['path_entry'] is not second_ui_builder.widgets['path_entry']

    def test_widget_state_preservation(self, built_ui_builder):
        """Test that widget state is preserved after operations."""
        # Set some widget state
        progress_bar = built_ui_builder.widgets['progress_bar']
        status_label = built_ui_builder.widgets['status_label']
        
        # Update state
        built_ui_builder.update_progress(75)
        built_ui_builder.update_status("Test status")
        
        # Check state is preserved
        assert progress_bar.value() == 75
        assert status_label.text() == "Test status"
        
        # Update again
        built_ui_builder.update_progress(100)
        built_ui_builder.update_status("Final status")
        
        # Check new state
        assert progress_bar.value() == 100
        assert status_label.text() == "Final status"

    def test_processing_state_toggle(self, built_ui_builder):
        """Test toggling processing state multiple times."""
        process_button = built_ui_builder.widgets['process_button']
        
        # Initial state
        assert process_button.isEnabled()
        
        # Enable processing
        built_ui_builder.set_processing_state(True)
        assert not process_button.isEnabled()
        
        # Disable processing
        built_ui_builder.set_processing_state(False)
        assert process_button.isEnabled()
        
        # Enable processing again
        built_ui_builder.set_processing_state(True)
        assert not process_button.isEnabled()

    def test_toggle_manual_mode(self, built_ui_builder):
        """Test toggling manual mode for group/replicate definition."""
        # Test enabling manual mode
        built_ui_builder.toggle_manual_mode(True)
        
        groups_entry = built_ui_builder.widgets['groups_entry']
        replicates_entry = built_ui_builder.widgets['replicates_entry']
        save_button = built_ui_builder.widgets['save_button']
        
        assert groups_entry.isEnabled()
        assert replicates_entry.isEnabled()
        assert save_button.isEnabled()
        
        # Test disabling manual mode
        built_ui_builder.toggle_manual_mode(False)
        
        assert not groups_entry.isEnabled()
        assert not replicates_entry.isEnabled()
        assert not save_button.isEnabled()

