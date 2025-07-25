"""
Custom exceptions for flow cytometry processing.
"""


class FlowProcError(Exception):
    """Base exception for flow cytometry processing errors."""
    pass


class ParsingError(FlowProcError):
    """Raised when data parsing fails."""
    pass


class ProcessingError(FlowProcError):
    """Raised when data processing fails."""
    pass


class ValidationError(FlowProcError):
    """Raised when data validation fails."""
    pass


class VisualizationError(FlowProcError):
    """Raised when visualization operations fail."""
    pass


class ExportError(FlowProcError):
    """Raised when export operations fail."""
    pass


class ConfigurationError(FlowProcError):
    """Raised when configuration is invalid."""
    pass


class FileError(FlowProcError):
    """Raised when file operations fail."""
    pass


class DataError(FlowProcError):
    """Raised when data operations fail."""
    pass 