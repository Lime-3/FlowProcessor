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


# Convenience functions for direct aggregation service usage
def create_aggregation_service(df: pd.DataFrame, sid_col: str = "SampleID") -> AggregationService:
    """Create a new aggregation service instance."""
    return AggregationService(df, sid_col)


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
    service = AggregationService(df, sid_col)
    try:
        agg_methods = {col: agg_method for col in value_cols}
        return service.export_aggregate(value_cols, group_cols, agg_methods)
    finally:
        service.cleanup()


def flow_cytometry_aggregate(
    df: pd.DataFrame,
    metric_name: str,
    raw_cols: List[str],
    sid_col: str = "SampleID",
    config: Optional[AggregationConfig] = None
) -> List[pd.DataFrame]:
    """
    Flow cytometry aggregation using unified service.
    
    Args:
        df: DataFrame to aggregate
        metric_name: Name of the metric
        raw_cols: List of column names to aggregate
        sid_col: Sample ID column name
        config: Aggregation configuration (auto-detected if None)
        
    Returns:
        List of aggregated DataFrames
    """
    service = AggregationService(df, sid_col)
    try:
        return service.flow_cytometry_aggregate(metric_name, raw_cols, config)
    finally:
        service.cleanup()


def aggregate_all_metrics(
    df: pd.DataFrame,
    metrics: Optional[List[str]] = None,
    sid_col: str = "SampleID",
    config: Optional[AggregationConfig] = None
) -> AggregationResult:
    """
    Aggregate all metrics using unified service.
    
    Args:
        df: DataFrame to aggregate
        metrics: List of metric names to process (None for all)
        sid_col: Sample ID column name
        config: Aggregation configuration (auto-detected if None)
        
    Returns:
        AggregationResult with processed DataFrames and metadata
    """
    service = AggregationService(df, sid_col)
    try:
        return service.aggregate_all_metrics(metrics, config)
    finally:
        service.cleanup() 