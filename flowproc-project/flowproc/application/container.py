from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Type, TypeVar

from flowproc.core.protocols import (
    DataParser, DataProcessor, DataExporter, 
    VisualizationRenderer, ConfigurationManager
)
from flowproc.domain.parsing.service import ParseService
from flowproc.domain.processing.service import DataProcessingService
from flowproc.domain.export.service import ExportService
from flowproc.domain.visualization.service import PlotlyRenderer
from flowproc.infrastructure.config.settings import FileConfigManager

T = TypeVar('T')


class Container:
    """Dependency injection container using the Service Locator pattern."""
    
    def __init__(self) -> None:
        self._services: Dict[Type[Any], Any] = {}
        self._singletons: Dict[Type[Any], Any] = {}
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default service implementations."""
        self.register(DataParser, ParseService)
        self.register(DataProcessor, DataProcessingService)
        self.register(DataExporter, ExportService)
        self.register(VisualizationRenderer, PlotlyRenderer)
        self.register(ConfigurationManager, FileConfigManager)
    
    def register(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a service implementation for an interface."""
        self._services[interface] = implementation
    
    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance for an interface."""
        self._singletons[interface] = instance
    
    def get(self, interface: Type[T]) -> T:
        """Get a service instance."""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Get registered implementation
        if interface not in self._services:
            raise ValueError(f"No implementation registered for {interface}")
        
        implementation = self._services[interface]
        return implementation()
    
    @lru_cache(maxsize=128)
    def get_singleton(self, interface: Type[T]) -> T:
        """Get or create a singleton instance."""
        if interface in self._singletons:
            return self._singletons[interface]
        
        instance = self.get(interface)
        self._singletons[interface] = instance
        return instance


# Global container instance
container = Container()