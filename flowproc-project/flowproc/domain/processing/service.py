"""
DataProcessingService - Coordinates data processing operations.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path

from ...core.exceptions import ProcessingError
from .aggregators import VectorizedAggregator
from .transformers import DataTransformer


class DataProcessingService:
    """Service for coordinating data processing operations."""
    
    def __init__(self):
        self.aggregator = VectorizedAggregator()
        self.transformer = DataTransformer()
        
    def process_data(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Process data according to the provided configuration."""
        try:
            result_df = df.copy()
            
            # Apply transformations if specified
            if config.get('transform', False):
                result_df = self.transformer.transform(result_df, config.get('transform_options', {}))
            
            # Apply aggregation if specified
            if config.get('aggregate', False):
                result_df = self.aggregator.aggregate(
                    result_df, 
                    config.get('group_by', []),
                    config.get('aggregation_methods', ['mean'])
                )
            
            return result_df
            
        except Exception as e:
            raise ProcessingError(f"Failed to process data: {str(e)}") from e
    
    def aggregate_data(self, df: pd.DataFrame, group_by: List[str], 
                      methods: List[str] = ['mean']) -> pd.DataFrame:
        """Aggregate data using specified grouping and methods."""
        try:
            return self.aggregator.aggregate(df, group_by, methods)
        except Exception as e:
            raise ProcessingError(f"Failed to aggregate data: {str(e)}") from e
    
    def transform_data(self, df: pd.DataFrame, options: Dict[str, Any]) -> pd.DataFrame:
        """Transform data using specified options."""
        try:
            return self.transformer.transform(df, options)
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
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for required fields
        if 'group_by' in config and not isinstance(config['group_by'], list):
            validation['errors'].append("group_by must be a list")
            validation['valid'] = False
        
        if 'aggregation_methods' in config and not isinstance(config['aggregation_methods'], list):
            validation['errors'].append("aggregation_methods must be a list")
            validation['valid'] = False
        
        # Check for valid aggregation methods
        valid_methods = ['mean', 'median', 'sum', 'count', 'std', 'min', 'max']
        if 'aggregation_methods' in config:
            for method in config['aggregation_methods']:
                if method not in valid_methods:
                    validation['warnings'].append(f"Unknown aggregation method: {method}")
        
        return validation 