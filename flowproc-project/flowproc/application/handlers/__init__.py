"""
Application handlers module for flow cytometry processing.
"""

from .error_handler import ErrorHandler, ErrorRecovery, handle_errors, handle_errors_with_context, setup_error_handling
from .event_handler import (
    EventHandler, EventLogger, EventNotifier, Event, EventType,
    event_handler, event_logger, event_notifier,
    emit_processing_event, emit_visualization_event, emit_export_event,
    emit_error_event, emit_warning_event
)

__all__ = [
    'ErrorHandler',
    'ErrorRecovery',
    'handle_errors',
    'handle_errors_with_context',
    'setup_error_handling',
    'EventHandler',
    'EventLogger',
    'EventNotifier',
    'Event',
    'EventType',
    'event_handler',
    'event_logger',
    'event_notifier',
    'emit_processing_event',
    'emit_visualization_event',
    'emit_export_event',
    'emit_error_event',
    'emit_warning_event'
] 