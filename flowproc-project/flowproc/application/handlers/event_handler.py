"""
Event handling for flow cytometry processing application.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of application events."""
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"
    PARSING_STARTED = "parsing_started"
    PARSING_COMPLETED = "parsing_completed"
    PARSING_FAILED = "parsing_failed"
    VISUALIZATION_STARTED = "visualization_started"
    VISUALIZATION_COMPLETED = "visualization_completed"
    VISUALIZATION_FAILED = "visualization_failed"
    EXPORT_STARTED = "export_started"
    EXPORT_COMPLETED = "export_completed"
    EXPORT_FAILED = "export_failed"
    VALIDATION_STARTED = "validation_started"
    VALIDATION_COMPLETED = "validation_completed"
    VALIDATION_FAILED = "validation_failed"
    ERROR_OCCURRED = "error_occurred"
    WARNING_OCCURRED = "warning_occurred"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    CONFIGURATION_CHANGED = "configuration_changed"


@dataclass
class Event:
    """Represents an application event."""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    user_id: Optional[str] = None


class EventHandler:
    """Handles application events and notifications."""
    
    def __init__(self):
        """Initialize the event handler."""
        self.event_listeners: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history_size = 1000
        self._lock = threading.Lock()
        
    def register_listener(self, event_type: EventType, listener: Callable) -> None:
        """
        Register a listener for a specific event type.
        
        Args:
            event_type: Type of event to listen for
            listener: Function to call when event occurs
        """
        with self._lock:
            if event_type not in self.event_listeners:
                self.event_listeners[event_type] = []
            self.event_listeners[event_type].append(listener)
        
        logger.debug(f"Registered listener for {event_type.value}")
    
    def unregister_listener(self, event_type: EventType, listener: Callable) -> None:
        """
        Unregister a listener for a specific event type.
        
        Args:
            event_type: Type of event
            listener: Function to unregister
        """
        with self._lock:
            if event_type in self.event_listeners:
                try:
                    self.event_listeners[event_type].remove(listener)
                    logger.debug(f"Unregistered listener for {event_type.value}")
                except ValueError:
                    logger.warning(f"Listener not found for {event_type.value}")
    
    def emit_event(self, event_type: EventType, data: Dict[str, Any] = None, 
                  source: str = "", user_id: Optional[str] = None) -> None:
        """
        Emit an event to all registered listeners.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source of the event
            user_id: User ID associated with the event
        """
        event = Event(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data or {},
            source=source,
            user_id=user_id
        )
        
        # Store in history
        with self._lock:
            self.event_history.append(event)
            if len(self.event_history) > self.max_history_size:
                self.event_history = self.event_history[-self.max_history_size:]
        
        # Notify listeners
        self._notify_listeners(event)
        
        logger.debug(f"Emitted event: {event_type.value} from {source}")
    
    def _notify_listeners(self, event: Event) -> None:
        """Notify all listeners for an event."""
        with self._lock:
            listeners = self.event_listeners.get(event.event_type, [])
        
        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in event listener for {event.event_type.value}: {e}")
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         limit: Optional[int] = None) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        with self._lock:
            if event_type:
                events = [e for e in self.event_history if e.event_type == event_type]
            else:
                events = self.event_history.copy()
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def clear_event_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self.event_history.clear()
        logger.info("Event history cleared")
    
    def get_event_summary(self) -> Dict[str, Any]:
        """Get summary of event history."""
        with self._lock:
            events = self.event_history.copy()
        
        if not events:
            return {
                'total_events': 0,
                'event_types': {},
                'recent_events': []
            }
        
        # Count event types
        event_types = {}
        for event in events:
            event_type = event.event_type.value
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            'total_events': len(events),
            'event_types': event_types,
            'recent_events': [self._event_to_dict(e) for e in events[-10:]],  # Last 10 events
            'first_event': events[0].timestamp.isoformat(),
            'last_event': events[-1].timestamp.isoformat()
        }
    
    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'data': event.data,
            'source': event.source,
            'user_id': event.user_id
        }


class EventLogger:
    """Logs events to various outputs."""
    
    def __init__(self, event_handler: EventHandler):
        """Initialize the event logger."""
        self.event_handler = event_handler
        self.setup_logging()
    
    def setup_logging(self) -> None:
        """Setup event logging."""
        # Register as listener for all events
        for event_type in EventType:
            self.event_handler.register_listener(event_type, self._log_event)
    
    def _log_event(self, event: Event) -> None:
        """Log an event."""
        log_message = f"Event: {event.event_type.value} from {event.source}"
        if event.data:
            log_message += f" - Data: {event.data}"
        
        # Log based on event type
        if event.event_type.value.endswith('_failed'):
            logger.error(log_message)
        elif event.event_type.value.endswith('_completed'):
            logger.info(log_message)
        elif event.event_type.value.endswith('_started'):
            logger.info(log_message)
        elif event.event_type == EventType.ERROR_OCCURRED:
            logger.error(log_message)
        elif event.event_type == EventType.WARNING_OCCURRED:
            logger.warning(log_message)
        else:
            logger.debug(log_message)


class EventNotifier:
    """Sends event notifications to external systems."""
    
    def __init__(self, event_handler: EventHandler):
        """Initialize the event notifier."""
        self.event_handler = event_handler
        self.notification_callbacks: List[Callable] = []
        self.setup_notifications()
    
    def setup_notifications(self) -> None:
        """Setup event notifications."""
        # Register as listener for important events
        important_events = [
            EventType.PROCESSING_FAILED,
            EventType.ERROR_OCCURRED,
            EventType.SYSTEM_HEALTH_CHECK
        ]
        
        for event_type in important_events:
            self.event_handler.register_listener(event_type, self._notify_event)
    
    def register_notification_callback(self, callback: Callable) -> None:
        """
        Register a notification callback.
        
        Args:
            callback: Function to call for notifications
        """
        self.notification_callbacks.append(callback)
        logger.debug("Registered notification callback")
    
    def _notify_event(self, event: Event) -> None:
        """Send notification for an event."""
        for callback in self.notification_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")


# Global event handler instance
event_handler = EventHandler()
event_logger = EventLogger(event_handler)
event_notifier = EventNotifier(event_handler)


def emit_processing_event(event_type: EventType, data: Dict[str, Any] = None, 
                         source: str = "processing", user_id: Optional[str] = None) -> None:
    """Emit a processing-related event."""
    event_handler.emit_event(event_type, data, source, user_id)


def emit_visualization_event(event_type: EventType, data: Dict[str, Any] = None,
                           source: str = "visualization", user_id: Optional[str] = None) -> None:
    """Emit a visualization-related event."""
    event_handler.emit_event(event_type, data, source, user_id)


def emit_export_event(event_type: EventType, data: Dict[str, Any] = None,
                     source: str = "export", user_id: Optional[str] = None) -> None:
    """Emit an export-related event."""
    event_handler.emit_event(event_type, data, source, user_id)


def emit_error_event(error: Exception, context: Dict[str, Any] = None,
                    source: str = "system", user_id: Optional[str] = None) -> None:
    """Emit an error event."""
    data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {}
    }
    event_handler.emit_event(EventType.ERROR_OCCURRED, data, source, user_id)


def emit_warning_event(warning_message: str, context: Dict[str, Any] = None,
                      source: str = "system", user_id: Optional[str] = None) -> None:
    """Emit a warning event."""
    data = {
        'warning_message': warning_message,
        'context': context or {}
    }
    event_handler.emit_event(EventType.WARNING_OCCURRED, data, source, user_id) 