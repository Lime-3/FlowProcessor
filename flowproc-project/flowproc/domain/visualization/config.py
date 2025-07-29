"""
Configuration for the visualization domain.

This module re-exports configuration classes from visualization_config.py to maintain
backward compatibility and fix import connectivity issues.
"""

# Import all configuration classes from the actual implementation
from .visualization_config import (
    VisualizationConfig,
    ValidationResult,
    ConfigurationValidator,
    ConfigPresets
)

# Re-export for backward compatibility
__all__ = [
    'VisualizationConfig',
    'ValidationResult',
    'ConfigurationValidator',
    'ConfigPresets'
] 