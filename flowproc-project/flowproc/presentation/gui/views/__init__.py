"""
GUI Views Module

This module contains the view classes that handle the user interface
components and their presentation logic.
"""

from .main_window import MainWindow

# Import components (will work after implementations are copied from artifact)
try:
    from .components import (
        UIBuilder, EventHandler, StateManager, 
        ProcessingCoordinator, FileManager
    )
    from .mixins import StylingMixin, ValidationMixin
    
    __all__ = [
        'MainWindow',
        'UIBuilder',
        'EventHandler', 
        'StateManager',
        'ProcessingCoordinator',
        'FileManager',
        'StylingMixin',
        'ValidationMixin'
    ]
except ImportError:
    # During migration, components may not be fully implemented yet
    __all__ = ['MainWindow']
