"""Aggregate data for Excel output."""
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import logging
from ..aggregation import generic_aggregate

logger = logging.getLogger(__name__)


class DataAggregator:
    """Aggregates flow cytometry data by groups and replicates."""
    
    # Aggregation functions for different metrics
    AGG_FUNCTIONS = {
        'mean': np.mean,
        'median': np.median,
        'std': np.std,
        'sem': lambda x: np.std(x) / np.sqrt(len(x)),
        'cv': lambda x: np.std(x) / np.mean(x) * 100 if np.mean(x) != 0 else np.nan,
        'min': np.min,
        'max': np.max,
        'count': len,
    }
    
    def __init__(self, agg_method: str = 'mean'):
        """
        Initialize data aggregator.
        
        Args:
            agg_method: Default aggregation method
        """
        self.agg_method = agg_method
        
    def aggregate_by_group(self, df: pd.DataFrame,
                          value_columns: List[str],
                          group_columns: Optional[List[str]] = None,
                          agg_methods: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        Aggregate data by group columns.
        
        Args:
            df: DataFrame to aggregate
            value_columns: Columns to aggregate
            group_columns: Columns to group by
            agg_methods: Dictionary mapping columns to aggregation methods
            
        Returns:
            Aggregated DataFrame
        """
        if group_columns is None:
            group_columns = ['Group']
            
        # Filter to rows with data
        df_clean = df.dropna(subset=value_columns, how='all')
        
        if df_clean.empty:
            logger.warning("No data to aggregate")
            return pd.DataFrame()
            
        # Delegate to centralized generic aggregation
        return generic_aggregate(
            df_clean,
            value_cols=value_columns,
            group_cols=group_columns,
            agg_methods=agg_methods or {col: self.agg_method for col in value_columns},
        )
        
    def aggregate_with_stats(self, df: pd.DataFrame,
                            value_columns: List[str],
                            group_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Aggregate with multiple statistics.
        
        Args:
            df: DataFrame to aggregate
            value_columns: Columns to aggregate
            group_columns: Columns to group by
            
        Returns:
            DataFrame with mean, std, sem, and n for each value
        """
        if group_columns is None:
            group_columns = ['Group']
            
        # Filter to rows with data
        df_clean = df.dropna(subset=value_columns, how='all')
        
        if df_clean.empty:
            logger.warning("No data to aggregate")
            return pd.DataFrame()
            
        # Aggregate each statistic
        agg_dict = {}
        for col in value_columns:
            agg_dict[col] = ['mean', 'std', 'sem', 'count']
            
        # Custom aggregation
        result = df_clean.groupby(group_columns)[value_columns].agg(
            lambda x: pd.Series({
                'mean': x.mean(),
                'std': x.std(),
                'sem': x.std() / np.sqrt(len(x)) if len(x) > 0 else np.nan,
                'n': len(x)
            })
        )
        
        # Flatten column names
        result.columns = ['_'.join(col).strip() for col in result.columns.values]
        result = result.reset_index()
        
        return result
        
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
        # Create pivot table
        pivot = df.pivot_table(
            index=index_cols,
            columns=column_col,
            values=value_col,
            fill_value=fill_value,
            aggfunc='first'  # Assuming one value per cell
        )
        
        # Reset index to make index columns regular columns
        pivot = pivot.reset_index()
        
        # Sort columns if they're numeric
        if all(isinstance(col, (int, float)) for col in pivot.columns[len(index_cols):]):
            sorted_cols = (
                list(pivot.columns[:len(index_cols)]) +
                sorted(pivot.columns[len(index_cols):])
            )
            pivot = pivot[sorted_cols]
            
        return pivot
        
    def reshape_for_time_course(self, df: pd.DataFrame,
                               value_columns: List[str],
                               n_replicates: int) -> Dict[str, pd.DataFrame]:
        """
        Reshape data for time course output.
        
        Args:
            df: DataFrame with time course data
            value_columns: Columns containing values
            n_replicates: Number of replicates
            
        Returns:
            Dictionary mapping column names to reshaped DataFrames
        """
        if 'Time' not in df.columns:
            raise ValueError("Time column required for time course reshaping")
            
        results = {}
        
        for col in value_columns:
            # Pivot with time and group
            pivot = self.pivot_for_excel(
                df,
                index_cols=['Time', 'Group'],
                column_col='Replicate',
                value_col=col
            )
            
            # Ensure all replicates are present
            for rep in range(1, n_replicates + 1):
                if rep not in pivot.columns[2:]:  # After Time and Group
                    pivot[rep] = np.nan
                    
            # Sort replicate columns
            rep_cols = sorted([c for c in pivot.columns if isinstance(c, (int, float))])
            other_cols = [c for c in pivot.columns if c not in rep_cols]
            pivot = pivot[other_cols + rep_cols]
            
            results[col] = pivot
            
        return results