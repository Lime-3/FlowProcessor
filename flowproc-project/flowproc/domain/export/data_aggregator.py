"""Aggregate data for Excel output using the unified aggregation service."""

from typing import Dict, List, Tuple, Optional, Any, Union, Sequence
import pandas as pd
import numpy as np
import logging
from ..aggregation import generic_aggregate, AggregationService

logger = logging.getLogger(__name__)


# Convenience functions for direct aggregation service usage
def aggregate_by_group(
    df: pd.DataFrame,
    value_columns: List[str],
    group_columns: Optional[List[str]] = None,
    agg_methods: Optional[Dict[str, str]] = None,
    sid_col: str = "SampleID"
) -> pd.DataFrame:
    """
    Aggregate data by group using the unified aggregation service.
    
    Args:
        df: DataFrame to aggregate
        value_columns: Columns to aggregate
        group_columns: Columns to group by (default: ['Group'])
        agg_methods: Aggregation methods per column
        sid_col: Sample ID column name
        
    Returns:
        Aggregated DataFrame
    """
    if group_columns is None:
        group_columns = ['Group']
        
    if agg_methods is None:
        agg_methods = {col: 'mean' for col in value_columns}
        
    # Use unified service for export aggregation
    service = AggregationService(df, sid_col)
    try:
        return service.export_aggregate(value_columns, group_columns, agg_methods)
    finally:
        service.cleanup()


def aggregate_with_stats(
    df: pd.DataFrame,
    value_columns: List[str],
    group_columns: Optional[List[str]] = None,
    sid_col: str = "SampleID"
) -> pd.DataFrame:
    """
    Aggregate data with comprehensive statistics.
    
    Args:
        df: DataFrame to aggregate
        value_columns: Columns to aggregate
        group_columns: Columns to group by (default: ['Group'])
        sid_col: Sample ID column name
        
    Returns:
        DataFrame with mean, std, sem, and count for each value column
    """
    if group_columns is None:
        group_columns = ['Group']
        
    # Filter to rows with data
    df_clean = df.dropna(subset=value_columns, how='all')
    
    if df_clean.empty:
        logger.warning("No data to aggregate")
        return pd.DataFrame()
        
    # Use unified service for comprehensive aggregation
    service = AggregationService(df_clean, sid_col)
    try:
        # Create aggregation methods for comprehensive stats
        # We need to create separate aggregations for each statistic
        final_result = None
        
        for col in value_columns:
            # Aggregate mean
            mean_result = service.export_aggregate([col], group_columns, {col: 'mean'})
            mean_result = mean_result.rename(columns={col: f"{col}_mean"})
            
            # Aggregate std
            std_result = service.export_aggregate([col], group_columns, {col: 'std'})
            std_result = std_result.rename(columns={col: f"{col}_std"})
            
            # Aggregate count
            count_result = service.export_aggregate([col], group_columns, {col: 'count'})
            count_result = count_result.rename(columns={col: f"{col}_n"})
            
            # Calculate SEM (std / sqrt(n))
            sem_result = count_result.copy()
            sem_result[f"{col}_sem"] = std_result[f"{col}_std"] / np.sqrt(count_result[f"{col}_n"])
            
            # Merge all results
            if final_result is None:
                final_result = mean_result.copy()
                final_result[f"{col}_std"] = std_result[f"{col}_std"]
                final_result[f"{col}_sem"] = sem_result[f"{col}_sem"]
                final_result[f"{col}_n"] = count_result[f"{col}_n"]
                # Remove the generic 'N' column since we have specific count columns
                if 'N' in final_result.columns:
                    final_result = final_result.drop(columns=['N'])
            else:
                # Merge with suffixes to avoid column conflicts
                final_result = final_result.merge(mean_result, on=group_columns, suffixes=('', '_mean'))
                final_result = final_result.merge(std_result, on=group_columns, suffixes=('', '_std'))
                final_result = final_result.merge(sem_result, on=group_columns, suffixes=('', '_sem'))
                final_result = final_result.merge(count_result, on=group_columns, suffixes=('', '_count'))
                
        return final_result
        
    finally:
        service.cleanup()


def aggregate_by_replicate(
    df: pd.DataFrame,
    value_columns: List[str],
    group_columns: Optional[List[str]] = None,
    agg_methods: Optional[Dict[str, str]] = None,
    sid_col: str = "SampleID"
) -> pd.DataFrame:
    """
    Aggregate data by replicate using the unified aggregation service.
    
    Args:
        df: DataFrame to aggregate
        value_columns: Columns to aggregate
        group_columns: Columns to group by (default: ['Group', 'Replicate'])
        agg_methods: Aggregation methods per column
        sid_col: Sample ID column name
        
    Returns:
        Aggregated DataFrame with replicate-level data
    """
    if group_columns is None:
        group_columns = ['Group', 'Replicate']
        
    if agg_methods is None:
        agg_methods = {col: 'mean' for col in value_columns}
        
    # Use unified service for export aggregation
    service = AggregationService(df, sid_col)
    try:
        return service.export_aggregate(value_columns, group_columns, agg_methods)
    finally:
        service.cleanup()


def create_export_aggregator(agg_method: str = 'mean'):
    """
    Create an export aggregator with the specified method.
    
    This function is provided for backward compatibility but is deprecated.
    Use the direct functions instead.
    
    Args:
        agg_method: Default aggregation method
        
    Returns:
        Deprecated aggregator object
    """
    import warnings
    warnings.warn(
        "create_export_aggregator is deprecated. Use direct functions instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    class DeprecatedExportAggregator:
        def __init__(self, method):
            self.method = method
            
        def aggregate_by_group(self, df, value_columns, group_columns=None, agg_methods=None):
            if agg_methods is None:
                agg_methods = {col: self.method for col in value_columns}
            return aggregate_by_group(df, value_columns, group_columns, agg_methods)
            
        def aggregate_with_stats(self, df, value_columns, group_columns=None):
            return aggregate_with_stats(df, value_columns, group_columns)
            
        def aggregate_by_replicate(self, df, value_columns, group_columns=None, agg_methods=None):
            if agg_methods is None:
                agg_methods = {col: self.method for col in value_columns}
            return aggregate_by_replicate(df, value_columns, group_columns, agg_methods)
    
    return DeprecatedExportAggregator(agg_method)