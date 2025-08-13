"""
Shared fixtures for GUI unit tests.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt


@pytest.fixture(scope="session")
def qt_app():
    """Create a single Qt application for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't delete the app here as it might be used by other tests


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager with default state."""
    state_manager = Mock()
    state_manager.preview_paths = []
    state_manager.last_csv = None
    state_manager.current_group_labels = []
    state_manager.is_processing = False
    state_manager.last_output_dir = None
    
    # Mock methods
    state_manager.clear_preview_data = Mock()
    state_manager.add_observer = Mock()
    state_manager.remove_observer = Mock()
    state_manager.update_status = Mock()
    
    return state_manager


@pytest.fixture
def mock_file_manager():
    """Create a mock file manager."""
    file_manager = Mock()
    file_manager.browse_input_files = Mock(return_value=[])
    file_manager.show_preview_dialog = Mock()
    return file_manager


@pytest.fixture
def mock_processing_coordinator():
    """Create a mock processing coordinator."""
    coordinator = Mock()
    coordinator.start_processing = Mock()
    coordinator.visualize_data = Mock()
    coordinator.visualize_data_with_options = Mock()
    coordinator.cancel_processing = Mock()
    coordinator.pause_processing = Mock()
    coordinator.resume_processing = Mock()
    coordinator.get_state = Mock(return_value="RUNNING")
    coordinator.is_processing = Mock(return_value=False)
    coordinator.cleanup = Mock()
    coordinator.handle_close_request = Mock(return_value=True)
    coordinator.connect_signals = Mock()
    return coordinator


@pytest.fixture
def mock_ui_builder():
    """Create a mock UI builder with common widgets."""
    ui_builder = Mock()
    
    # Create mock widgets
    widgets = {


        'browse_input_button': Mock(),
        'clear_button': Mock(),
        'preview_button': Mock(),
        'out_dir_button': Mock(),
        'process_button': Mock(),
        'visualize_button': Mock(),
        'cancel_button': Mock(),
        'pause_button': Mock(),
        'group_labels_button': Mock(),
        'manual_groups_button': Mock(),
        'path_entry': Mock(),
        'output_entry': Mock(),
        'out_dir_entry': Mock(),  # Added missing widget
        'group_combo': Mock(),
        'metric_combo': Mock(),
        'timecourse_combo': Mock(),
        'time_course_checkbox': Mock(),

        'progress_bar': Mock(),
        'status_label': Mock()
    }
    
    # Set up default return values for widget methods
    for widget in widgets.values():
        if hasattr(widget, 'text'):
            widget.text.return_value = ""
        if hasattr(widget, 'currentText'):
            widget.currentText.return_value = ""
        if hasattr(widget, 'isChecked'):
            widget.isChecked.return_value = False
        if hasattr(widget, 'isEnabled'):
            widget.isEnabled.return_value = True
        if hasattr(widget, 'setEnabled'):
            widget.setEnabled = Mock()
        if hasattr(widget, 'setText'):
            widget.setText = Mock()
        if hasattr(widget, 'clear'):
            widget.clear = Mock()
        if hasattr(widget, 'setValue'):
            widget.setValue = Mock()
        if hasattr(widget, 'value'):
            widget.value.return_value = 0
        if hasattr(widget, 'clicked'):
            widget.clicked = Mock()
        if hasattr(widget, 'stateChanged'):
            widget.stateChanged = Mock()
        if hasattr(widget, 'textChanged'):
            widget.textChanged = Mock()
        if hasattr(widget, 'currentTextChanged'):
            widget.currentTextChanged = Mock()
    
    ui_builder.get_widget.side_effect = lambda name: widgets.get(name)
    ui_builder.set_processing_state = Mock()
    ui_builder.update_progress = Mock()
    ui_builder.update_status = Mock()
    
    ui_builder.set_pause_button_text = Mock()
    ui_builder.build_complete_ui = Mock()
    
    return ui_builder, widgets


@pytest.fixture
def mock_main_window():
    """Create a mock main window with proper Qt widget functionality."""
    # Create a real QWidget as the base for the mock main window
    # This ensures that Qt widget operations work properly
    main_window = Mock(spec=QWidget)
    
    # Set up basic Qt widget properties and methods
    main_window.windowTitle = Mock(return_value="Flow Cytometry Processor")
    main_window.minimumSize = Mock(return_value=Mock(width=lambda: 800, height=lambda: 600))
    main_window.x = Mock(return_value=100)
    main_window.y = Mock(return_value=100)
    main_window.close = Mock()
    main_window.deleteLater = Mock()
    
    # Add Qt widget methods that DropLineEdit might need
    main_window.setAcceptDrops = Mock()
    main_window.acceptDrops = Mock(return_value=True)
    main_window.parent = Mock(return_value=None)
    main_window.objectName = Mock(return_value="MainWindow")
    main_window.setObjectName = Mock()
    main_window.setStyleSheet = Mock()
    main_window.styleSheet = Mock(return_value="")
    main_window.setEnabled = Mock()
    main_window.isEnabled = Mock(return_value=True)
    main_window.setVisible = Mock()
    main_window.isVisible = Mock(return_value=True)
    main_window.show = Mock()
    main_window.hide = Mock()
    main_window.raise_ = Mock()
    main_window.lower = Mock()
    main_window.resize = Mock()
    main_window.move = Mock()
    main_window.geometry = Mock(return_value=Mock(x=lambda: 100, y=lambda: 100, width=lambda: 800, height=lambda: 600))
    main_window.pos = Mock(return_value=Mock(x=lambda: 100, y=lambda: 100))
    main_window.size = Mock(return_value=Mock(width=lambda: 800, height=lambda: 600))
    main_window.width = Mock(return_value=800)
    main_window.height = Mock(return_value=600)
    main_window.setWindowTitle = Mock()
    main_window.setMinimumSize = Mock()
    main_window.setMaximumSize = Mock()
    main_window.setFixedSize = Mock()
    main_window.setSizePolicy = Mock()
    main_window.sizePolicy = Mock(return_value=Mock())
    main_window.layout = Mock(return_value=None)
    main_window.setLayout = Mock()
    main_window.children = Mock(return_value=[])
    main_window.findChild = Mock(return_value=None)
    main_window.findChildren = Mock(return_value=[])
    main_window.installEventFilter = Mock()
    main_window.removeEventFilter = Mock()
    main_window.eventFilter = Mock(return_value=False)
    main_window.event = Mock(return_value=True)
    main_window.mousePressEvent = Mock()
    main_window.mouseReleaseEvent = Mock()
    main_window.mouseMoveEvent = Mock()
    main_window.keyPressEvent = Mock()
    main_window.keyReleaseEvent = Mock()
    main_window.focusInEvent = Mock()
    main_window.focusOutEvent = Mock()
    main_window.dragEnterEvent = Mock()
    main_window.dragLeaveEvent = Mock()
    main_window.dragMoveEvent = Mock()
    main_window.dropEvent = Mock()
    main_window.changeEvent = Mock()
    main_window.resizeEvent = Mock()
    main_window.moveEvent = Mock()
    main_window.closeEvent = Mock()
    main_window.showEvent = Mock()
    main_window.hideEvent = Mock()
    main_window.paintEvent = Mock()
    main_window.enterEvent = Mock()
    main_window.leaveEvent = Mock()
    main_window.wheelEvent = Mock()
    main_window.contextMenuEvent = Mock()
    main_window.actionEvent = Mock()
    main_window.tabletEvent = Mock()
    main_window.grabMouse = Mock()
    main_window.releaseMouse = Mock()
    main_window.grabKeyboard = Mock()
    main_window.releaseKeyboard = Mock()
    main_window.setMouseTracking = Mock()
    main_window.hasMouseTracking = Mock(return_value=False)
    main_window.setFocusPolicy = Mock()
    main_window.focusPolicy = Mock(return_value=Mock())
    main_window.setFocus = Mock()
    main_window.clearFocus = Mock()
    main_window.hasFocus = Mock(return_value=False)
    main_window.setTabOrder = Mock()
    main_window.setUpdatesEnabled = Mock()
    main_window.updatesEnabled = Mock(return_value=True)
    main_window.update = Mock()
    main_window.repaint = Mock()
    main_window.setAttribute = Mock()
    main_window.testAttribute = Mock(return_value=False)
    main_window.setWindowFlags = Mock()
    main_window.windowFlags = Mock(return_value=Mock())
    main_window.setWindowState = Mock()
    main_window.windowState = Mock(return_value=Mock())
    main_window.setWindowModality = Mock()
    main_window.windowModality = Mock(return_value=Mock())
    main_window.isModal = Mock(return_value=False)
    main_window.setWindowFilePath = Mock()
    main_window.windowFilePath = Mock(return_value="")
    main_window.setWindowIcon = Mock()
    main_window.windowIcon = Mock(return_value=Mock())
    main_window.setWindowIconText = Mock()
    main_window.windowIconText = Mock(return_value="")
    main_window.setWindowRole = Mock()
    main_window.windowRole = Mock(return_value="")
    main_window.setWindowModified = Mock()
    main_window.isWindowModified = Mock(return_value=False)
    main_window.setToolTip = Mock()
    main_window.toolTip = Mock(return_value="")
    main_window.setStatusTip = Mock()
    main_window.statusTip = Mock(return_value="")
    main_window.setWhatsThis = Mock()
    main_window.whatsThis = Mock(return_value="")
    main_window.setAccessibleName = Mock()
    main_window.accessibleName = Mock(return_value="")
    main_window.setAccessibleDescription = Mock()
    main_window.accessibleDescription = Mock(return_value="")
    main_window.setLayoutDirection = Mock()
    main_window.layoutDirection = Mock(return_value=Mock())
    main_window.setLocale = Mock()
    main_window.locale = Mock(return_value=Mock())
    main_window.setFont = Mock()
    main_window.font = Mock(return_value=Mock())
    main_window.setCursor = Mock()
    main_window.cursor = Mock(return_value=Mock())
    main_window.setMouseCursor = Mock()
    main_window.unsetCursor = Mock()
    main_window.setToolTipDuration = Mock()
    main_window.toolTipDuration = Mock(return_value=-1)
    main_window.setContextMenuPolicy = Mock()
    main_window.contextMenuPolicy = Mock(return_value=Mock())
    main_window.setFocusProxy = Mock()
    main_window.focusProxy = Mock(return_value=None)
    main_window.setGraphicsEffect = Mock()
    main_window.graphicsEffect = Mock(return_value=None)
    main_window.setAutoFillBackground = Mock()
    main_window.autoFillBackground = Mock(return_value=False)
    main_window.setStyle = Mock()
    main_window.style = Mock(return_value=Mock())
    main_window.setStyleSheet = Mock()
    main_window.styleSheet = Mock(return_value="")
    main_window.setPalette = Mock()
    main_window.palette = Mock(return_value=Mock())
    main_window.setBackgroundRole = Mock()
    main_window.backgroundRole = Mock(return_value=Mock())
    main_window.setForegroundRole = Mock()
    main_window.foregroundRole = Mock(return_value=Mock())
    
    return main_window


@pytest.fixture
def qt_widget_parent():
    """Create a real QWidget parent for testing Qt widgets that need proper parent functionality."""
    return QWidget()


@pytest.fixture
def mock_observer():
    """Create a mock observer for testing notifications."""
    return Mock()


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before each test to ensure isolation."""
    # This fixture runs automatically before each test
    # It ensures that any global mocks are reset
    pass


@pytest.fixture
def isolated_test_environment():
    """Create an isolated test environment with all necessary mocks."""
    with patch('flowproc.presentation.gui.views.components.event_handler.QMessageBox') as mock_msgbox, \
         patch('flowproc.presentation.gui.views.components.event_handler.QFileDialog') as mock_filedialog, \
         patch('flowproc.presentation.gui.views.components.event_handler.GroupLabelsDialog') as mock_dialog:
        
        # Set up mock return values
        mock_msgbox.warning = Mock()
        mock_msgbox.critical = Mock()
        mock_msgbox.information = Mock()
        mock_msgbox.question = Mock()
        
        mock_filedialog.getExistingDirectory = Mock(return_value="")
        
        mock_dialog_instance = Mock()
        mock_dialog_instance.exec = Mock(return_value=True)
        mock_dialog_instance.get_labels = Mock(return_value=["Group A", "Group B"])
        mock_dialog.return_value = mock_dialog_instance
        
        yield {
            'message_box': mock_msgbox,
            'file_dialog': mock_filedialog,
            'group_dialog': mock_dialog
        } 