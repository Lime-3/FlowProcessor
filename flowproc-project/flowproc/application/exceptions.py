from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Any


class FlowProcError(Exception):
    """Base exception for FlowProc errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[dict] = None,
        caused_by: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.caused_by = caused_by
    
    def __str__(self) -> str:
        result = self.message
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            result += f" ({details_str})"
        if self.caused_by:
            result += f" caused by {type(self.caused_by).__name__}: {self.caused_by}"
        return result


class DataParsingError(FlowProcError):
    """Raised when data parsing fails."""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[Path] = None,
        line_number: Optional[int] = None,
        caused_by: Optional[Exception] = None
    ) -> None:
        details = {}
        if file_path:
            details["file"] = str(file_path)
        if line_number:
            details["line"] = line_number
        
        super().__init__(message, details, caused_by)
        self.file_path = file_path
        self.line_number = line_number


class DataValidationError(FlowProcError):
    """Raised when data validation fails."""
    
    def __init__(
        self, 
        message: str, 
        validation_errors: Optional[List[str]] = None,
        caused_by: Optional[Exception] = None
    ) -> None:
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        
        super().__init__(message, details, caused_by)
        self.validation_errors = validation_errors or []


class ProcessingError(FlowProcError):
    """Raised when data processing fails."""
    
    def __init__(
        self, 
        message: str, 
        failed_files: Optional[List[Path]] = None,
        caused_by: Optional[Exception] = None
    ) -> None:
        details = {}
        if failed_files:
            details["failed_files"] = [str(f) for f in failed_files]
        
        super().__init__(message, details, caused_by)
        self.failed_files = failed_files or []


class VisualizationError(FlowProcError):
    """Raised when visualization generation fails."""
    pass


class ConfigurationError(FlowProcError):
    """Raised when configuration is invalid."""
    pass


class ExportError(FlowProcError):
    """Raised when data export fails."""
    
    def __init__(
        self, 
        message: str, 
        output_path: Optional[Path] = None,
        caused_by: Optional[Exception] = None
    ) -> None:
        details = {}
        if output_path:
            details["output_path"] = str(output_path)
        
        super().__init__(message, details, caused_by)
        self.output_path = output_path