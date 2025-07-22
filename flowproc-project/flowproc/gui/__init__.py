# flowproc/gui/__init__.py
"""
GUI package for FlowProc application.
Provides Qt-based interface with async processing capabilities.
"""
from .main import main
from .window import MainWindow
from .async_processor import ProcessingManager, ProcessingWorker, ProcessingState, ProcessingResult
from .visualizer import visualize_metric

create_gui = main

__all__ = [
    'main',
    'create_gui',
    'MainWindow', 
    'ProcessingManager',
    'ProcessingWorker',
    'ProcessingState',
    'ProcessingResult',
    'visualize_metric'
]