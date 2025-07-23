"""
Custom exceptions for FlowProcessor.
"""


class ProcessingError(Exception):
    """Raised when general processing operations fail."""
    pass


class VisualizationError(Exception):
    """Raised when visualization fails."""
    pass


class DataProcessingError(VisualizationError):
    """Raised when data processing fails."""
    pass 