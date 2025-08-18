"""
Unified aggregation service for flow cytometry data processing.

This service consolidates all complex aggregation logic while keeping simple
statistical functions in core.py. It provides a clean interface for different
aggregation needs without duplication.
"""

import logging
import gc
import time
from typing import List, Dict, Optional, Any, Union, Sequence
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from .core import group_stats, group_stats_multi, generic_aggregate
from ..parsing.tissue_parser import extract_tissue
from ...core.constants import Constants, KEYWORDS

logger = logging.getLogger(__name__)

# Type aliases
DataFrame = pd.DataFrame


@dataclass
class AggregationConfig:
    """Configuration for aggregation operations."""
    groups: List[int] = field(default_factory=list)
    times: List[Optional[float]] = field(default_factory=list)
    tissues_detected: bool = False
    group_map: Dict[int, str] = field(default_factory=dict)
    sid_col: str = "SampleID"
    time_course_mode: bool = False
    include_sem: bool = True
    split_by_tissue: bool = True


@dataclass
class AggregationResult:
    """Result container for aggregation operations."""
    dataframes: List[pd.DataFrame] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    memory_usage: float = 0.0
    config: Optional[AggregationConfig] = None


class AggregationService:
    """
    Unified aggregation service that consolidates all complex aggregation logic.
    
    This service provides:
    - Simple statistical aggregation (delegates to core.py)
    - Complex flow cytometry aggregation (tissue parsing, time courses)
    - Performance optimization and memory management
    - Consistent interfaces for different use cases
    """
    
    def __init__(self, df: Optional[DataFrame] = None, sid_col: str = "SampleID"):
        """
        Initialize aggregation service.
        
        Args:
            df: Input DataFrame (can be set later)
            sid_col: Name of sample ID column
        """
        self.df = df.copy() if df is not None else None
        self.sid_col = sid_col
        self._config: Optional[AggregationConfig] = None
        
    def set_data(self, df: DataFrame, sid_col: Optional[str] = None) -> None:
        """Set or update the data for aggregation."""
        if sid_col:
            self.sid_col = sid_col
        self.df = df.copy()
        self._config = None  # Reset config when data changes
        
    def get_config(self) -> AggregationConfig:
        """Get or auto-detect aggregation configuration."""
        if self._config is None:
            self._config = self._auto_detect_config()
        return self._config
        
    def simple_aggregate(
        self, 
        value_col: str, 
        group_cols: Union[str, Sequence[str]] = "Group"
    ) -> DataFrame:
        """
        Simple aggregation using core functions.
        
        Args:
            value_col: Column to aggregate
            group_cols: Column(s) to group by
            
        Returns:
            DataFrame with mean, std, count, sem
        """
        return group_stats(self.df, value_col, group_cols)
        
    def multi_aggregate(
        self,
        value_cols: Sequence[str],
        group_cols: Union[str, Sequence[str]] = "Group",
        long_name: str = "Variable",
        value_name: str = "Value"
    ) -> DataFrame:
        """
        Multi-column aggregation using core functions.
        
        Args:
            value_cols: Columns to aggregate
            group_cols: Column(s) to group by
            long_name: Name for the variable column
            value_name: Name for the value column
            
        Returns:
            Long-form DataFrame with all metrics
        """
        return group_stats_multi(
            self.df, value_cols, group_cols, long_name, value_name
        )
        
    def flow_cytometry_aggregate(
        self,
        metric_name: str,
        raw_cols: List[str],
        config: Optional[AggregationConfig] = None
    ) -> List[DataFrame]:
        """
        Flow cytometry specific aggregation with tissue parsing and time courses.
        
        Args:
            metric_name: Name of the metric
            raw_cols: List of column names to aggregate
            config: Aggregation configuration (auto-detected if None)
            
        Returns:
            List of aggregated DataFrames (one per tissue if multiple detected)
        """
        if not raw_cols:
            logger.debug(f"No columns for metric '{metric_name}'")
            return []
            
        start_time = time.time()
        
        # Get or auto-detect configuration
        if config is None:
            config = self.get_config()
            
        # Prepare data with tissue extraction
        working_df = self._prepare_flow_data()
        
        if working_df.empty:
            logger.warning("No valid data for aggregation")
            return []
            
        # Melt to long format for efficient aggregation
        melted = self._melt_for_aggregation(working_df, raw_cols, config)
        
        if melted.empty:
            logger.warning(f"No valid data after melting for metric '{metric_name}'")
            return []
            
        # Perform aggregation
        agg_result = self._perform_aggregation(melted, config, metric_name)
        
        # Split by tissue if needed
        result_dfs = self._split_by_tissue(agg_result, config)
        
        logger.debug(
            f"Aggregated {metric_name} in {time.time() - start_time:.3f}s "
            f"({len(melted)} rows -> {len(agg_result)} aggregated)"
        )
        
        return result_dfs
        
    def aggregate_all_metrics(
        self,
        metrics: Optional[List[str]] = None,
        config: Optional[AggregationConfig] = None
    ) -> AggregationResult:
        """
        Aggregate all metrics using flow cytometry logic.
        
        Args:
            metrics: List of metric names to process (None for all)
            config: Aggregation configuration (auto-detected if None)
            
        Returns:
            AggregationResult with processed DataFrames and metadata
        """
        start_time = time.time()
        
        # Get configuration
        if config is None:
            config = self.get_config()
            
        # Determine metrics to process
        if metrics is None:
            metrics = list(KEYWORDS.keys())
            
        result = AggregationResult()
        result.config = config
        
        # Process each metric
        for metric_name in metrics:
            key_substring = KEYWORDS.get(metric_name, metric_name.lower())
            
            # Find matching columns
            raw_cols = [
                col for col in self.df.columns
                if key_substring in col.lower()
                and col not in {self.sid_col, 'Well', 'Group', 'Animal', 
                              'Time', 'Replicate', 'Tissue'}
                and not self.df[col].isna().all()
            ]
            
            if raw_cols:
                agg_dfs = self.flow_cytometry_aggregate(metric_name, raw_cols, config)
                if agg_dfs:
                    result.dataframes.extend(agg_dfs)
                    result.metrics.append(metric_name)
                    
        # Calculate final metrics
        result.processing_time = time.time() - start_time
        
        if result.dataframes:
            final_memory = sum(
                df.memory_usage(deep=True).sum() for df in result.dataframes
            ) / 1e6  # MB
            result.memory_usage = final_memory
            
        logger.info(
            f"Unified aggregation completed: "
            f"{len(result.metrics)} metrics, "
            f"{len(result.dataframes)} DataFrames, "
            f"{result.processing_time:.3f}s, "
            f"{result.memory_usage:.1f}MB memory"
        )
        
        return result
        
    def export_aggregate(
        self,
        value_cols: Sequence[str],
        group_cols: Union[str, Sequence[str]],
        agg_methods: Optional[Dict[str, Union[str, callable]]] = None
    ) -> DataFrame:
        """
        Export-focused aggregation using core functions.
        
        Args:
            value_cols: Columns to aggregate
            group_cols: Column(s) to group by
            agg_methods: Aggregation methods per column
            
        Returns:
            DataFrame formatted for export
        """
        return generic_aggregate(self.df, value_cols, group_cols, agg_methods)
        
    def cleanup(self) -> None:
        """Clean up memory used by the service."""
        try:
            if hasattr(self, 'df') and self.df is not None:
                del self.df
                self.df = None
            gc.collect()
        except Exception as e:
            logger.debug(f"Cleanup warning: {e}")
            
    def _prepare_flow_data(self) -> DataFrame:
        """Prepare data with tissue extraction and validation."""
        if self.df is None:
            return pd.DataFrame()
            
        working_df = self.df.copy()
        
        # Vectorized tissue extraction
        if self.sid_col in working_df.columns:
            working_df['Tissue'] = working_df[self.sid_col].apply(extract_tissue)
        else:
            working_df['Tissue'] = Constants.UNKNOWN_TISSUE.value
            
        # Ensure numeric types for grouping columns
        for col in ['Group', 'Animal', 'Replicate']:
            if col in working_df.columns:
                working_df[col] = pd.to_numeric(working_df[col], errors='coerce')
                
        # Handle time column
        if 'Time' in working_df.columns:
            working_df['Time'] = pd.to_numeric(working_df['Time'], errors='coerce')
        else:
            working_df['Time'] = np.nan
            
        # Filter to replicate data only
        if 'Replicate' in working_df.columns:
            replicate_mask = working_df['Replicate'].notna()
            working_df = working_df[replicate_mask]
            
        return working_df
        
    def _melt_for_aggregation(
        self, 
        df: DataFrame, 
        raw_cols: List[str], 
        config: AggregationConfig
    ) -> DataFrame:
        """Melt DataFrame to long format for aggregation."""
        # Define ID variables
        id_vars = [self.sid_col, 'Group', 'Animal', 'Replicate', 'Tissue']
        if config.time_course_mode:
            id_vars.append('Time')
            
        # Only include columns that exist
        id_vars = [col for col in id_vars if col in df.columns]
        value_vars = [col for col in raw_cols if col in df.columns]
        
        if not value_vars:
            return pd.DataFrame()
            
        melted = pd.melt(
            df,
            id_vars=id_vars,
            value_vars=value_vars,
            var_name='Subpopulation',
            value_name='Value'
        )
        
        # Drop rows with missing values and convert to numeric
        melted = melted.dropna(subset=['Value'])
        melted['Value'] = pd.to_numeric(melted['Value'], errors='coerce')
        melted = melted.dropna(subset=['Value'])
        
        # Clean subpopulation names
        melted['Subpopulation'] = melted['Subpopulation'].apply(self._clean_subpopulation_name)
        
        return melted
        
    def _perform_aggregation(
        self, 
        melted: DataFrame, 
        config: AggregationConfig, 
        metric_name: str
    ) -> DataFrame:
        """Perform the actual aggregation."""
        # Define grouping columns
        group_cols = ['Group', 'Subpopulation']
        if 'Tissue' in melted.columns:
            group_cols.insert(1, 'Tissue')
        if config.time_course_mode and 'Time' in melted.columns:
            group_cols.insert(0, 'Time')
            
        # Aggregate
        agg_result = melted.groupby(group_cols, dropna=False).agg(
            Mean=('Value', 'mean'),
            Std=('Value', 'std'),
            Count=('Value', 'count')
        ).reset_index()
        
        # Replace NaN std with 0 for single-value groups
        agg_result.loc[agg_result['Count'] == 1, 'Std'] = 0.0
        
        # Add metadata
        agg_result['Group_Label'] = agg_result['Group'].map(config.group_map)
        agg_result['Metric'] = metric_name
        
        # Add SEM if requested
        if config.include_sem:
            agg_result['SEM'] = np.where(
                (agg_result['Count'] > 1) & agg_result['Std'].notna(),
                agg_result['Std'] / np.sqrt(agg_result['Count']),
                0.0
            )
            
        return agg_result
        
    def _split_by_tissue(
        self, 
        agg_result: DataFrame, 
        config: AggregationConfig
    ) -> List[DataFrame]:
        """Split results by tissue if multiple tissues detected."""
        if not config.split_by_tissue or 'Tissue' not in agg_result.columns:
            return [agg_result]
            
        unique_tissues = agg_result['Tissue'].unique()
        if len(unique_tissues) <= 1:
            return [agg_result]
            
        # Create separate dataframes for each tissue
        result_dfs = []
        for tissue in unique_tissues:
            tissue_df = agg_result[agg_result['Tissue'] == tissue].copy()
            if not tissue_df.empty:
                result_dfs.append(tissue_df)
                
        logger.debug(f"Split data into {len(result_dfs)} tissue-specific dataframes")
        return result_dfs
        
    def _clean_subpopulation_name(self, col_name: str) -> str:
        """Clean subpopulation name while preserving context."""
        try:
            # Take the gating path portion before the metric separator
            path_part = col_name.split('|', 1)[0].strip()
            parts = [p.strip() for p in path_part.split('/') if p.strip()]
            if not parts:
                return col_name

            leaf = parts[-1]
            # If the leaf is a generic GFP marker, prepend the previous node for context
            leaf_norm = leaf.replace(' ', '').lower()
            if leaf_norm.startswith('gfp') or leaf_norm in {'gfp-a+', 'gfp+', 'gfp-a-', 'gfp-'}:
                if len(parts) >= 2:
                    prev = parts[-2]
                    return f"{prev} {leaf}".strip()
                return leaf

            return leaf
        except Exception:
            return col_name
            
    def _auto_detect_config(self) -> AggregationConfig:
        """Auto-detect aggregation configuration from data."""
        if self.df is None or self.df.empty:
            return AggregationConfig(sid_col=self.sid_col)
            
        # Get unique values efficiently
        groups = sorted(self.df['Group'].dropna().unique().astype(int)) if 'Group' in self.df.columns else []
        
        # Check for time data
        if 'Time' in self.df.columns:
            times = sorted(self.df['Time'].dropna().unique())
            time_course_mode = len(times) > 1 or (len(times) == 1 and not np.isnan(times[0]))
        else:
            times = [None]
            time_course_mode = False
            
        # Check for multiple tissues
        tissues_detected = self.df['Tissue'].nunique() > 1 if 'Tissue' in self.df.columns else False
        
        # Create group mapping
        group_map = {g: f"Group {int(g)}" for g in groups}
        
        return AggregationConfig(
            groups=groups,
            times=times,
            tissues_detected=tissues_detected,
            group_map=group_map,
            sid_col=self.sid_col,
            time_course_mode=time_course_mode
        )
        
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


# Convenience functions for backward compatibility
def create_aggregation_service(df: DataFrame, sid_col: str = "SampleID") -> AggregationService:
    """Create a new aggregation service instance."""
    return AggregationService(df, sid_col)


def simple_group_stats(df: DataFrame, value_col: str, group_cols: Union[str, Sequence[str]] = "Group") -> DataFrame:
    """Simple aggregation using core functions."""
    return group_stats(df, value_col, group_cols)


def multi_group_stats(
    df: DataFrame,
    value_cols: Sequence[str],
    group_cols: Union[str, Sequence[str]] = "Group",
    long_name: str = "Variable",
    value_name: str = "Value"
) -> DataFrame:
    """Multi-column aggregation using core functions."""
    return group_stats_multi(df, value_cols, group_cols, long_name, value_name)
