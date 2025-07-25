"""
Protocol definitions for flow cytometry processing.
"""

from typing import Protocol, Dict, Any, List
import pandas as pd


class ParserProtocol(Protocol):
    """Protocol for data parsers."""
    
    def parse(self, df: pd.DataFrame, columns: Dict[str, Any]) -> pd.DataFrame:
        """Parse the dataframe and return the result."""
        ...


class DataParser(Protocol):
    """Protocol for data parsers (alias for ParserProtocol)."""
    
    def parse(self, df: pd.DataFrame, columns: Dict[str, Any]) -> pd.DataFrame:
        """Parse the dataframe and return the result."""
        ...


class ProcessorProtocol(Protocol):
    """Protocol for data processors."""
    
    def process(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Process the dataframe and return the result."""
        ...


class DataProcessor(Protocol):
    """Protocol for data processors (alias for ProcessorProtocol)."""
    
    def process(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Process the dataframe and return the result."""
        ...


class ValidatorProtocol(Protocol):
    """Protocol for data validators."""
    
    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the dataframe and return validation results."""
        ...


class VisualizerProtocol(Protocol):
    """Protocol for data visualizers."""
    
    def visualize(self, df: pd.DataFrame, config: Dict[str, Any]) -> Any:
        """Visualize the dataframe and return the visualization."""
        ...


class ExporterProtocol(Protocol):
    """Protocol for data exporters."""
    
    def export(self, data: Any, filepath: str, config: Dict[str, Any]) -> None:
        """Export data to the specified filepath."""
        ...


class DataExporter(Protocol):
    """Protocol for data exporters (alias for ExporterProtocol)."""
    
    def export(self, data: Any, filepath: str, config: Dict[str, Any]) -> None:
        """Export data to the specified filepath."""
        ...


class ConfigProviderProtocol(Protocol):
    """Protocol for configuration providers."""
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        ...
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update the configuration."""
        ...


class ConfigurationManager(Protocol):
    """Protocol for configuration managers (alias for ConfigProviderProtocol)."""
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        ...
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update the configuration."""
        ...


class DataProviderProtocol(Protocol):
    """Protocol for data providers."""
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """Load data from the specified filepath."""
        ...
    
    def save_data(self, df: pd.DataFrame, filepath: str) -> None:
        """Save data to the specified filepath."""
        ...


class ServiceProtocol(Protocol):
    """Protocol for service classes."""
    
    def initialize(self) -> None:
        """Initialize the service."""
        ...
    
    def cleanup(self) -> None:
        """Clean up resources used by the service."""
        ...


class VisualizationRenderer(Protocol):
    """Protocol for visualization renderers."""
    
    def render(self, data: Any, config: Dict[str, Any]) -> Any:
        """Render visualization from data."""
        ...