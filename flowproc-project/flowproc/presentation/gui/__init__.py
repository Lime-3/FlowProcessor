# flowproc/gui/__init__.py
"""
GUI package for FlowProc application.
Provides Qt-based interface with async processing capabilities.
"""
from .main import main
from .views.main_window import MainWindow
from .workers.processing_worker import ProcessingManager, ProcessingWorker, ProcessingState, ProcessingResult
from .views.widgets.drop_line_edit import DropLineEdit
from .views.widgets.progress_widget import ProgressWidget
from .views.dialogs.preview_dialog import PreviewDialog
from .controllers.main_controller import MainController
from .controllers.processing_controller import ProcessingController
from .workers.validation_worker import ValidationWorker, ValidationResult
from .config_handler import load_last_output_dir, save_last_output_dir

create_gui = main

__all__ = [
    'main',
    'create_gui',
    'MainWindow', 
    'ProcessingManager',
    'ProcessingWorker',
    'ProcessingState',
    'ProcessingResult',
    'DropLineEdit',
    'ProgressWidget',
    'PreviewDialog',
    'MainController',
    'ProcessingController',
    'ValidationWorker',
    'ValidationResult',
    'load_last_output_dir',
    'save_last_output_dir'
]