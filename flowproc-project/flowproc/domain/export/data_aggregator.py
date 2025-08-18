"""Aggregate data for Excel output using the unified aggregation service."""

from typing import Dict, List, Tuple, Optional, Any, Union, Sequence
import pandas as pd
import numpy as np
import logging
from ..aggregation import generic_aggregate, AggregationService

logger = logging.getLogger(__name__)


class DataAggregator:
    """Aggregates flow cytometry data by groups and replicates using unified service."""
    
    def __init__(self, agg_method: str = 'mean'):
        """
        Initialize data aggregator.
        
        Args:
            agg_method: Default aggregation method
        """
        self.agg_method = agg_method
        self._service: Optional[AggregationService] = None
        
    def _get_service(self, df: pd.DataFrame, sid_col: str = "SampleID") -> AggregationService:
        """Get or create aggregation service."""
        if self._service is None:
            self._service = AggregationService(df, sid_col)
        else:
            self._service.set_data(df, sid_col)
        return self._service
        
    def aggregate_by_group(self, df: pd.DataFrame,
                          value_columns: List[str],
                          group_columns: Optional[List[str]] = None,
                          agg_methods: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Aggregate data by group using the unified aggregation service.
        
        Args:
            df: DataFrame to aggregate
            value_columns: Columns to aggregate
            group_columns: Columns to group by (default: ['Group'])
            agg_methods: Aggregation methods per column
            
        Returns:
            Aggregated DataFrame
        """
        if group_columns is None:
            group_columns = ['Group']
            
        if agg_methods is None:
            agg_methods = {col: self.agg_method for col in value_columns}
            
        # Use unified service for export aggregation
        service = self._get_service(df)
        try:
            return service.export_aggregate(value_columns, group_columns, agg_methods)
        finally:
            # Don't cleanup here as service might be reused
            pass
            
    def aggregate_with_stats(self, df: pd.DataFrame,
                            value_columns: List[str],
                            group_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Aggregate data with comprehensive statistics.
        
        Args:
            df: DataFrame to aggregate
            value_columns: Columns to aggregate
            group_columns: Columns to group by (default: ['Group'])
            
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
        service = self._get_service(df_clean)
        try:
            # Create aggregation methods for comprehensive stats
            agg_methods = {}
            for col in value_columns:
                agg_methods[f"{col}_mean"] = lambda x: x.mean()
                agg_methods[f"{col}_std"] = lambda x: x.std()
                agg_methods[f"{col}_sem"] = lambda x: x.std() / np.sqrt(len(x)) if len(x) > 0 else np.nan
                agg_methods[f"{col}_n"] = lambda x: len(x)
                
            # Aggregate using the service
            result = service.export_aggregate(value_columns, group_columns, agg_methods)
            
            # Flatten column names for better Excel formatting
            result.columns = [col.replace('_', ' ') for col in result.columns]
            
            return result
            
        finally:
            # Don't cleanup here as service might be reused
            pass
            
    def pivot_for_excel(self, df: pd.DataFrame,
                       index_cols: List[str],
                       column_col: str,
                       value_col: str,
                       fill_value: Any = None) -> pd.DataFrame:
        """
        Pivot data for Excel output.
        
        Args:
            df: DataFrame to pivot
            index_cols: Columns to use as index
            column_col: Column to pivot
            value_col: Values to display
            fill_value: Value for missing data
            
        Returns:
            Pivoted DataFrame
        """
        # Use pandas pivot_table for Excel-friendly output
        pivot_df = df.pivot_table(
            index=index_cols,
            columns=column_col,
            values=value_col,
            fill_value=fill_value,
            aggfunc='first'  # Take first value if duplicates
        )
        
        # Reset index to make it flat
        pivot_df = pivot_df.reset_index()
        
        # Flatten column names if they're multi-level
        if isinstance(pivot_df.columns, pd.MultiIndex):
            pivot_df.columns = [
                f"{col[0]}_{col[1]}" if col[1] else col[0]
                for col in pivot_df.columns
            ]
            
        return pivot_df
        
    def cleanup(self) -> None:
        """Clean up resources used by the aggregator."""
        if self._service is not None:
            self._service.cleanup()
            self._service = None
            
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


# Convenience function for backward compatibility
def aggregate_for_export(
    df: pd.DataFrame,
    value_columns: List[str],
    group_columns: Optional[List[str]] = None,
    agg_method: str = 'mean'
) -> pd.DataFrame:
    """
    Convenience function for export aggregation.
    
    Args:
        df: DataFrame to aggregate
        value_columns: Columns to aggregate
        group_columns: Columns to group by
        agg_method: Aggregation method to use
        
    Returns:
        Aggregated DataFrame ready for export
    """
    aggregator = DataAggregator(agg_method)
    try:
        return aggregator.aggregate_by_group(df, value_columns, group_columns)
    finally:
        aggregator.cleanup()