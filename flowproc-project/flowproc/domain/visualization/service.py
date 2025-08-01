"""
VisualizationService - Coordinates visualization operations.

DEPRECATED: This service is deprecated in favor of UnifiedVisualizationService.
This file is maintained for backward compatibility only.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import plotly.graph_objects as go
import logging
import warnings

from ...core.exceptions import VisualizationError
from .unified_service import UnifiedVisualizationService, get_unified_visualization_service

logger = logging.getLogger(__name__)


class VisualizationService:
    """
    Service for coordinating visualization operations.
    
    DEPRECATED: This service is deprecated in favor of UnifiedVisualizationService.
    This class is maintained for backward compatibility only.
    
    All plot creation methods have been moved to the new PlotFactory architecture.
    Please migrate to UnifiedVisualizationService for new code.
    """
    
    def __init__(self):
        warnings.warn(
            "VisualizationService is deprecated. Use UnifiedVisualizationService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._unified_service = get_unified_visualization_service()
        
    def create_plot(self, df: pd.DataFrame, plot_type: str, 
                   config: Dict[str, Any]) -> go.Figure:
        """
        Create a plot using the specified type and configuration.
        
        DEPRECATED: This method delegates to UnifiedVisualizationService.
        """
        return self._unified_service.create_plot(df, plot_type, config)
    
    def create_dashboard(self, dataframes: List[pd.DataFrame], 
                        plots_config: List[Dict[str, Any]]) -> go.Figure:
        """
        Create a dashboard with multiple plots.
        
        DEPRECATED: This method delegates to UnifiedVisualizationService.
        """
        return self._unified_service.create_dashboard(dataframes, plots_config)
    
    def save_plot(self, fig: go.Figure, filepath: str, format: str = 'html') -> None:
        """
        Save a plot to file.
        
        DEPRECATED: This method delegates to UnifiedVisualizationService.
        """
        self._unified_service.save_plot(fig, filepath, format)
    
    def get_available_plot_types(self) -> List[str]:
        """
        Get list of available plot types.
        
        DEPRECATED: This method delegates to UnifiedVisualizationService.
        """
        return self._unified_service.get_available_plot_types()
    
    def get_available_themes(self) -> List[str]:
        """
        Get list of available themes.
        
        DEPRECATED: This method delegates to UnifiedVisualizationService.
        """
        return self._unified_service.get_available_themes()
    
    def validate_plot_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate plot configuration.
        
        DEPRECATED: This method delegates to UnifiedVisualizationService.
        """
        return self._unified_service.validate_plot_config(config)


# Convenience function for backward compatibility
def get_visualization_service() -> VisualizationService:
    """
    Get a visualization service instance.
    
    DEPRECATED: Use get_unified_visualization_service() instead.
    """
    warnings.warn(
        "get_visualization_service() is deprecated. Use get_unified_visualization_service() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return VisualizationService() 