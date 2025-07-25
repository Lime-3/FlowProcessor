"""
Global error handling for flow cytometry processing.
"""

import logging
import traceback
import sys
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime

from ...core.exceptions import FlowProcError
from ...infrastructure.monitoring.metrics import metrics_collector

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Global error handler for the application."""
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_callbacks: Dict[str, Callable] = {}
        self.error_history: list = []
        self.max_history_size = 1000
        
    def register_error_callback(self, error_type: str, callback: Callable) -> None:
        """
        Register a callback for specific error types.
        
        Args:
            error_type: Type of error to handle
            callback: Function to call when error occurs
        """
        self.error_callbacks[error_type] = callback
        logger.debug(f"Registered error callback for {error_type}")
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an error and return error information.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            Dictionary with error information
        """
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # Log the error
        logger.error(f"Error occurred: {error_info['error_type']}: {error_info['error_message']}")
        logger.debug(f"Error context: {error_info['context']}")
        
        # Store in history
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
        
        # Call registered callbacks
        self._call_error_callbacks(error_info)
        
        # Record metrics
        metrics_collector.end_operation(
            context.get('operation_id', 'unknown'),
            success=False,
            error_message=error_info['error_message']
        )
        
        return error_info
    
    def _call_error_callbacks(self, error_info: Dict[str, Any]) -> None:
        """Call registered error callbacks."""
        error_type = error_info['error_type']
        
        # Call specific error type callback
        if error_type in self.error_callbacks:
            try:
                self.error_callbacks[error_type](error_info)
            except Exception as e:
                logger.error(f"Error in callback for {error_type}: {e}")
        
        # Call general error callback
        if 'general' in self.error_callbacks:
            try:
                self.error_callbacks['general'](error_info)
            except Exception as e:
                logger.error(f"Error in general callback: {e}")
    
    def get_error_history(self, limit: Optional[int] = None) -> list:
        """
        Get error history.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of error information dictionaries
        """
        if limit is None:
            return self.error_history.copy()
        else:
            return self.error_history[-limit:]
    
    def clear_error_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()
        logger.info("Error history cleared")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error history."""
        if not self.error_history:
            return {
                'total_errors': 0,
                'error_types': {},
                'recent_errors': []
            }
        
        # Count error types
        error_types = {}
        for error_info in self.error_history:
            error_type = error_info['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'recent_errors': self.error_history[-10:],  # Last 10 errors
            'first_error': self.error_history[0]['timestamp'],
            'last_error': self.error_history[-1]['timestamp']
        }


def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors in functions.
    
    Args:
        func: Function to wrap with error handling
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get error handler instance
            error_handler = getattr(sys.modules[__name__], '_error_handler', None)
            if error_handler:
                context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
                error_handler.handle_error(e, context)
            else:
                # Fallback to basic logging
                logger.error(f"Error in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
            raise
    return wrapper


def handle_errors_with_context(context: Dict[str, Any]) -> Callable:
    """
    Decorator to handle errors with specific context.
    
    Args:
        context: Context information to include with errors
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error handler instance
                error_handler = getattr(sys.modules[__name__], '_error_handler', None)
                if error_handler:
                    error_context = context.copy()
                    error_context.update({
                        'function': func.__name__,
                        'module': func.__module__,
                        'args': str(args),
                        'kwargs': str(kwargs)
                    })
                    error_handler.handle_error(e, error_context)
                else:
                    # Fallback to basic logging
                    logger.error(f"Error in {func.__name__}: {e}")
                    logger.debug(traceback.format_exc())
                raise
        return wrapper
    return decorator


class ErrorRecovery:
    """Handles error recovery strategies."""
    
    def __init__(self):
        """Initialize error recovery."""
        self.recovery_strategies: Dict[str, Callable] = {}
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable) -> None:
        """
        Register a recovery strategy for an error type.
        
        Args:
            error_type: Type of error to handle
            strategy: Recovery function to call
        """
        self.recovery_strategies[error_type] = strategy
        logger.debug(f"Registered recovery strategy for {error_type}")
    
    def attempt_recovery(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Attempt to recover from an error.
        
        Args:
            error: The exception that occurred
            context: Additional context
            
        Returns:
            True if recovery was successful, False otherwise
        """
        error_type = type(error).__name__
        
        if error_type in self.recovery_strategies:
            try:
                logger.info(f"Attempting recovery for {error_type}")
                result = self.recovery_strategies[error_type](error, context)
                if result:
                    logger.info(f"Recovery successful for {error_type}")
                else:
                    logger.warning(f"Recovery failed for {error_type}")
                return result
            except Exception as recovery_error:
                logger.error(f"Error during recovery for {error_type}: {recovery_error}")
                return False
        
        logger.debug(f"No recovery strategy found for {error_type}")
        return False


# Global error handler instance
_error_handler = ErrorHandler()
error_recovery = ErrorRecovery()


def setup_error_handling() -> None:
    """Setup global error handling."""
    # Register default error callbacks
    _error_handler.register_error_callback('general', _default_error_callback)
    _error_handler.register_error_callback('ParsingError', _parsing_error_callback)
    _error_handler.register_error_callback('ProcessingError', _processing_error_callback)
    _error_handler.register_error_callback('ValidationError', _validation_error_callback)
    
    # Register default recovery strategies
    error_recovery.register_recovery_strategy('FileNotFoundError', _file_not_found_recovery)
    error_recovery.register_recovery_strategy('PermissionError', _permission_error_recovery)
    
    logger.info("Error handling setup completed")


def _default_error_callback(error_info: Dict[str, Any]) -> None:
    """Default error callback."""
    logger.error(f"Default error handler: {error_info['error_type']}: {error_info['error_message']}")


def _parsing_error_callback(error_info: Dict[str, Any]) -> None:
    """Callback for parsing errors."""
    logger.error(f"Parsing error: {error_info['error_message']}")
    # Could add specific parsing error handling here


def _processing_error_callback(error_info: Dict[str, Any]) -> None:
    """Callback for processing errors."""
    logger.error(f"Processing error: {error_info['error_message']}")
    # Could add specific processing error handling here


def _validation_error_callback(error_info: Dict[str, Any]) -> None:
    """Callback for validation errors."""
    logger.error(f"Validation error: {error_info['error_message']}")
    # Could add specific validation error handling here


def _file_not_found_recovery(error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
    """Recovery strategy for file not found errors."""
    logger.info("Attempting file not found recovery")
    # Could implement file search or alternative file handling
    return False


def _permission_error_recovery(error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
    """Recovery strategy for permission errors."""
    logger.info("Attempting permission error recovery")
    # Could implement permission fixing or alternative access methods
    return False 