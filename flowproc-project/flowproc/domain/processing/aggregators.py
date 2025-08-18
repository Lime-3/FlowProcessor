"""
Data aggregation components for flow cytometry data processing.

This module provides processing-specific aggregation interfaces that use
the unified aggregation service for actual processing.
"""

from typing import Dict, List, Any, Optional, Union, Sequence
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
import logging
import time

from ...core.exceptions import ProcessingError
from ..aggregation import AggregationService, AggregationConfig, AggregationResult

logger = logging.getLogger(__name__)


@dataclass
class AggregationStats:
    """Statistics for aggregation operations."""
    total_groups: int = 0
    total_metrics: int = 0
    total_samples: int = 0
    groups_processed: int = 0
    metrics_processed: int = 0
    failed_groups: List[str] = field(default_factory=list)
    failed_metrics: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    memory_usage: float = 0.0


class DataAggregator:
    """Base class for data aggregation strategies using unified service."""
    
    def __init__(self, df: Optional[pd.DataFrame] = None, sid_col: str = "SampleID"):
        """
        Initialize aggregator with optional data.
        
        Args:
            df: Input DataFrame
            sid_col: Sample ID column name
        """
        self.service = AggregationService(df, sid_col) if df is not None else None
        self.sid_col = sid_col
        
    def set_data(self, df: pd.DataFrame, sid_col: Optional[str] = None) -> None:
        """Set or update the data for aggregation."""
        if sid_col:
            self.sid_col = sid_col
        if self.service is None:
            self.service = AggregationService(df, self.sid_col)
        else:
            self.service.set_data(df, self.sid_col)
            
    def aggregate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """Aggregate data frame using unified service."""
        if self.service is None:
            self.set_data(df)
            
        # Determine aggregation type based on kwargs
        if 'value_cols' in kwargs and 'group_cols' in kwargs:
            return self.service.export_aggregate(
                kwargs['value_cols'], 
                kwargs['group_cols'], 
                kwargs.get('agg_methods')
            )
        elif 'value_col' in kwargs and 'group_cols' in kwargs:
            return self.service.simple_aggregate(
                kwargs['value_col'], 
                kwargs['group_cols']
            )
        else:
            raise ValueError("Must specify either value_cols+group_cols or value_col+group_cols")
            
    def flow_cytometry_aggregate(
        self,
        metric_name: str,
        raw_cols: List[str],
        config: Optional[AggregationConfig] = None
    ) -> List[pd.DataFrame]:
        """Aggregate flow cytometry data using unified service."""
        if self.service is None:
            raise ValueError("No data set. Call set_data() first.")
        return self.service.flow_cytometry_aggregate(metric_name, raw_cols, config)
        
    def aggregate_all_metrics(
        self,
        metrics: Optional[List[str]] = None,
        config: Optional[AggregationConfig] = None
    ) -> AggregationResult:
        """Aggregate all metrics using unified service."""
        if self.service is None:
            raise ValueError("No data set. Call set_data() first.")
        return self.service.aggregate_all_metrics(metrics, config)
        
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.service is not None:
            self.service.cleanup()
            self.service = None
            
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


class ProcessingAggregator(DataAggregator):
    """Specialized aggregator for processing workflows."""
    
    def __init__(self, df: Optional[pd.DataFrame] = None, sid_col: str = "SampleID"):
        super().__init__(df, sid_col)
        
    def process_with_aggregation(
        self,
        df: pd.DataFrame,
        processing_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Process data with aggregation based on configuration.
        
        Args:
            df: Input DataFrame
            processing_config: Processing configuration
            
        Returns:
            Processed DataFrame
        """
        self.set_data(df)
        
        # Extract aggregation parameters
        group_by = processing_config.get('group_by', ['Group'])
        agg_methods = processing_config.get('aggregation_methods', ['mean'])
        value_cols = processing_config.get('value_cols', [])
        
        if not value_cols:
            # Auto-detect numeric columns if not specified
            value_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # Filter out metadata columns
            value_cols = [col for col in value_cols if col not in 
                         ['Group', 'Animal', 'Replicate', 'Time', 'Well']]
        
        # Perform aggregation
        result = self.aggregate(
            df, 
            value_cols=value_cols, 
            group_cols=group_by, 
            agg_methods={col: agg_methods[0] for col in value_cols}
        )
        
        return result


# Convenience functions for backward compatibility
def create_processing_aggregator(df: pd.DataFrame, sid_col: str = "SampleID") -> ProcessingAggregator:
    """Create a new processing aggregator instance."""
    return ProcessingAggregator(df, sid_col)


def aggregate_for_processing(
    df: pd.DataFrame,
    value_cols: List[str],
    group_cols: List[str],
    agg_method: str = 'mean',
    sid_col: str = "SampleID"
) -> pd.DataFrame:
    """
    Convenience function for processing aggregation.
    
    Args:
        df: DataFrame to aggregate
        value_cols: Columns to aggregate
        group_cols: Columns to group by
        agg_method: Aggregation method to use
        sid_col: Sample ID column name
        
    Returns:
        Aggregated DataFrame
    """
    aggregator = ProcessingAggregator(df, sid_col)
    try:
        return aggregator.aggregate(
            df, 
            value_cols=value_cols, 
            group_cols=group_cols, 
            agg_methods={col: agg_method for col in value_cols}
        )
    finally:
        aggregator.cleanup() 