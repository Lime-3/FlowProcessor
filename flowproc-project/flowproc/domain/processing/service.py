"""
DataProcessingService - Generic data processing operations.

This service handles generic data processing operations using the unified
processing architecture. It delegates to the UnifiedProcessingService
for actual processing logic.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path

from ...core.exceptions import ProcessingError
from .core import UnifiedProcessingService, ProcessingConfig, ProcessingMode


class DataProcessingService:
    """
    Service for generic data processing operations.
    
    This service focuses on generic data transformations and aggregations,
    delegating to the unified processing architecture for actual processing.
    """
    
    def __init__(self):
        self.unified_service = UnifiedProcessingService()
        
    def process_data(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Process data according to the provided configuration."""
        try:
            unified_config = ProcessingConfig(
                mode=ProcessingMode.GENERIC,
                group_by=config.get('group_by', []),
                aggregation_methods=config.get('aggregation_methods', ['mean']),
                transform_options=config.get('transform_options', {}),
                filter_options=config.get('filter_options', {})
            )
            
            return self.unified_service.process_data(df, unified_config)
            
        except Exception as e:
            raise ProcessingError(f"Failed to process data: {str(e)}") from e
    
    def aggregate_data(self, df: pd.DataFrame, group_by: List[str], 
                      methods: List[str] = ['mean']) -> pd.DataFrame:
        """Aggregate data using specified grouping and methods."""
        try:
            config = ProcessingConfig(
                mode=ProcessingMode.GENERIC,
                group_by=group_by,
                aggregation_methods=methods
            )
            return self.unified_service.process_data(df, config)
        except Exception as e:
            raise ProcessingError(f"Failed to aggregate data: {str(e)}") from e
    
    def transform_data(self, df: pd.DataFrame, options: Dict[str, Any]) -> pd.DataFrame:
        """Transform data using specified options."""
        try:
            config = ProcessingConfig(
                mode=ProcessingMode.GENERIC,
                transform_options=options
            )
            return self.unified_service.process_data(df, config)
        except Exception as e:
            raise ProcessingError(f"Failed to transform data: {str(e)}") from e
    
    def get_processing_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get statistics about the data for processing decisions."""
        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'numeric_columns': [],
            'categorical_columns': [],
            'datetime_columns': []
        }
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats['numeric_columns'].append(col)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                stats['datetime_columns'].append(col)
            else:
                stats['categorical_columns'].append(col)
        
        return stats
    
    def validate_processing_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate processing configuration."""
        from ...core.validation import validate_config
        
        try:
            result = validate_config(config, 'processing')
            return result.to_dict()
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Configuration validation failed: {str(e)}"],
                'warnings': []
            } 