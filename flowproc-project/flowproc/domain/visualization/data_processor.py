"""
Data processing logic for the visualization system.

This module handles all data transformation, aggregation, and preparation
needed for creating visualizations, using vectorized operations for performance.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np
from functools import lru_cache

from .models import ProcessedData
from .config import VisualizationConfig
from ...core.constants import KEYWORDS, METRIC_KEYWORDS
from ...core.exceptions import DataError as DataProcessingError
from ..processing.vectorized_aggregator import VectorizedAggregator, AggregationConfig
from ..processing.transform import map_replicates
from ..parsing import extract_tissue

logger = logging.getLogger(__name__)

# Type alias
DataFrame = pd.DataFrame


class DataProcessor:
    """
    Handles data processing for visualization using vectorized operations.
    
    This class is responsible for taking raw flow cytometry data and
    transforming it into a format suitable for visualization, including
    aggregation, filtering, and metadata extraction.
    
    Key features:
    - Vectorized operations for performance
    - Defensive copying to prevent data mutation
    - Comprehensive error handling and validation
    - Support for time-course and standard analysis modes
    """
    
    def __init__(self, df: DataFrame, sid_col: str, config: VisualizationConfig):
        """
        Initialize the data processor.
        
        Args:
            df: Input DataFrame (will be copied to prevent mutation)
            sid_col: Sample ID column name
            config: Visualization configuration
        """
        # Defensive copy to prevent mutation of original data
        self.df = df.copy() if not df.empty else df
        self.sid_col = sid_col
        self.config = config
        self.aggregator = VectorizedAggregator(self.df, sid_col)
        
        # Validate inputs
        self._validate_inputs()
    
    def _validate_inputs(self) -> None:
        """Validate input data and configuration."""
        if self.df.empty:
            raise DataProcessingError("DataFrame is empty")
        
        if self.sid_col not in self.df.columns:
            raise DataProcessingError(f"Sample ID column '{self.sid_col}' not found in DataFrame")
        
        if not isinstance(self.config, VisualizationConfig):
            raise DataProcessingError("Config must be a VisualizationConfig instance")
    
    def process(self) -> ProcessedData:
        """
        Process DataFrame for plotting using vectorized operations.
        
        This is the main entry point for data processing. It orchestrates
        all the necessary transformations and returns a ProcessedData container.
        
        Returns:
            ProcessedData container with aggregated results
            
        Raises:
            DataProcessingError: If processing fails
        """
        try:
            logger.info(f"Starting data processing for {len(self.df)} rows")
            
            # Step 1: Map replicates
            df_mapped, replicate_count = self._map_replicates()
            if replicate_count == 0:
                raise DataProcessingError("No replicates found")
            
            logger.debug(f"Mapped replicates: {replicate_count} replicates found")
            
            # Step 2: Apply filters
            df_filtered = self._apply_filters(df_mapped)
            
            # Step 3: Update aggregator with processed data
            self.aggregator.df = df_filtered
            
            # Step 4: Extract metadata
            groups, times, tissues_detected, group_map = self._extract_metadata(df_filtered)
            
            # Step 5: Create aggregation configuration
            agg_config = AggregationConfig(
                groups=groups,
                times=times,
                tissues_detected=tissues_detected,
                group_map=group_map,
                sid_col=self.sid_col,
                time_course_mode=self.config.time_course_mode
            )
            
            # Step 6: Determine metrics to process
            metrics = self._get_metrics_to_process()
            
            # Step 7: Aggregate data using vectorized operations
            aggregated_lists = self._aggregate_metrics(metrics, agg_config)
            
            logger.info(f"Processing completed: {len(aggregated_lists)} dataframes, {len(metrics)} metrics")
            
            return ProcessedData(
                dataframes=aggregated_lists,
                metrics=metrics,
                groups=groups,
                times=times,
                tissues_detected=tissues_detected,
                group_map=group_map,
                replicate_count=replicate_count
            )
            
        except DataProcessingError:
            raise  # Re-raise our own exceptions
        except Exception as e:
            logger.error(f"Unexpected error during data processing: {e}", exc_info=True)
            raise DataProcessingError(f"Data processing failed: {str(e)}") from e
    
    def _map_replicates(self) -> Tuple[DataFrame, int]:
        """
        Map replicates using the transform module.
        
        Returns:
            Tuple of (mapped DataFrame, replicate count)
        """
        try:
            user_replicates = self.config.user_replicates
            df_mapped, replicate_count = map_replicates(
                self.df, 
                self.sid_col, 
                user_replicates=user_replicates
            )
            
            logger.debug(f"Replicate mapping: {replicate_count} replicates")
            return df_mapped, replicate_count
            
        except Exception as e:
            raise DataProcessingError(f"Failed to map replicates: {str(e)}") from e
    
    def _apply_filters(self, df: DataFrame) -> DataFrame:
        """
        Apply tissue and subpopulation filters to the data.
        
        Args:
            df: DataFrame to filter
            
        Returns:
            Filtered DataFrame
        """
        df_filtered = df.copy()
        original_count = len(df_filtered)
        
        # Apply tissue filtering if specified
        if self.config.tissue_filter and 'Tissue' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['Tissue'] == self.config.tissue_filter]
            filtered_count = len(df_filtered)
            logger.info(f"Applied tissue filter '{self.config.tissue_filter}': {original_count} -> {filtered_count} rows")
            
            if df_filtered.empty:
                raise DataProcessingError(f"No data found for tissue '{self.config.tissue_filter}'")
        
        # Apply subpopulation filtering if specified (for time-course mode)
        if self.config.subpopulation_filter and self.config.time_course_mode:
            # Note: Subpopulation filtering is applied after aggregation
            # since subpopulations are created during the aggregation process
            logger.info(f"Subpopulation filter '{self.config.subpopulation_filter}' will be applied during visualization")
        
        return df_filtered
    
    def _extract_metadata(self, df: DataFrame) -> Tuple[List[int], List[Optional[float]], bool, Dict[int, str]]:
        """
        Extract metadata from the processed DataFrame.
        
        Args:
            df: Processed DataFrame
            
        Returns:
            Tuple of (groups, times, tissues_detected, group_map)
        """
        # Extract groups
        if 'Group' in df.columns:
            groups = sorted(df['Group'].unique())
        else:
            groups = [1]  # Default single group
        
        # Extract times
        if 'Time' in df.columns and df['Time'].notna().any():
            times = sorted(df['Time'].dropna().unique())
        else:
            times = [None]  # No time data
        
        # Check for multiple tissues
        tissues_detected = (
            'Tissue' in df.columns and 
            len(df['Tissue'].unique()) > 1
        )
        
        # Create group mapping
        group_map = self._create_group_map(groups)
        
        logger.debug(f"Metadata extracted: groups={groups}, times={times}, tissues={tissues_detected}")
        
        return groups, times, tissues_detected, group_map
    
    def _create_group_map(self, groups: List[int]) -> Dict[int, str]:
        """
        Create mapping from group numbers to human-readable labels.
        
        Args:
            groups: List of group numbers
            
        Returns:
            Dictionary mapping group numbers to labels
        """
        # Use user-provided labels if available
        if self.config.user_group_labels:
            group_map = {}
            for i, group in enumerate(groups):
                if i < len(self.config.user_group_labels):
                    group_map[group] = self.config.user_group_labels[i]
                else:
                    group_map[group] = f"Group {group}"
            return group_map
        
        # Use default labels
        return {group: f"Group {group}" for group in groups}
    
    def _get_metrics_to_process(self) -> List[str]:
        """
        Determine which metrics to process based on configuration.
        
        Returns:
            List of metric names to process
        """
        if self.config.metric:
            # Process specific metric
            return [self.config.metric]
        else:
            # Process all available metrics
            available_metrics = []
            for metric in KEYWORDS.keys():
                key_substring = KEYWORDS.get(metric, metric.lower())
                matching_cols = [
                    col for col in self.df.columns
                    if key_substring in col.lower()
                    and col not in {self.sid_col, 'Well', 'Group', 'Animal', 
                                  'Time', 'Replicate', 'Tissue'}
                    and not self.df[col].isna().all()
                ]
                if matching_cols:
                    available_metrics.append(metric)
            
            if not available_metrics:
                raise DataProcessingError("No valid metrics found in the data")
            
            logger.debug(f"Available metrics: {available_metrics}")
            return available_metrics
    
    def _aggregate_metrics(self, metrics: List[str], agg_config: AggregationConfig) -> List[DataFrame]:
        """
        Aggregate data for all specified metrics using vectorized operations.
        
        Args:
            metrics: List of metrics to aggregate
            agg_config: Aggregation configuration
            
        Returns:
            List of aggregated DataFrames
        """
        try:
            aggregated_lists = []
            
            for metric in metrics:
                # Find raw columns that match this metric
                key_substring = KEYWORDS.get(metric, metric.lower())
                raw_cols = [
                    col for col in self.df.columns
                    if key_substring in col.lower()
                    and col not in {self.sid_col, 'Well', 'Group', 'Animal', 
                                  'Time', 'Replicate', 'Tissue'}
                    and not self.df[col].isna().all()
                ]
                
                if raw_cols:
                    logger.debug(f"Processing metric '{metric}' with columns: {raw_cols}")
                    agg_dfs = self.aggregator.aggregate_metric(metric, raw_cols, agg_config)
                    if agg_dfs:
                        aggregated_lists.extend(agg_dfs)
                        logger.debug(f"Added {len(agg_dfs)} aggregated dataframes for metric '{metric}'")
                else:
                    logger.warning(f"No matching columns found for metric '{metric}'")
            
            return aggregated_lists
            
        except Exception as e:
            raise DataProcessingError(f"Failed to aggregate metrics: {str(e)}") from e
    
    @staticmethod
    def validate_data_for_processing(df: DataFrame, sid_col: str) -> List[str]:
        """
        Validate that the data is suitable for processing.
        
        Args:
            df: DataFrame to validate
            sid_col: Sample ID column name
            
        Returns:
            List of validation warnings (empty if no issues)
        """
        warnings = []
        
        if df.empty:
            warnings.append("DataFrame is empty")
            return warnings
        
        if sid_col not in df.columns:
            warnings.append(f"Sample ID column '{sid_col}' not found")
        
        # Check for required columns
        required_cols = ['Group', 'Animal']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            warnings.append(f"Missing recommended columns: {', '.join(missing_cols)}")
        
        # Check for data quality issues
        if df.duplicated().any():
            warnings.append("Duplicate rows detected")
        
        # Check for missing values in key columns
        key_cols = [col for col in ['Group', 'Animal', 'Time'] if col in df.columns]
        for col in key_cols:
            if df[col].isna().any():
                warnings.append(f"Missing values in {col} column")
        
        # Check for negative values in data columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        data_cols = [col for col in numeric_cols if col not in key_cols + [sid_col]]
        for col in data_cols:
            if (df[col] < 0).any():
                warnings.append(f"Negative values detected in {col}")
        
        return warnings
    
    @lru_cache(maxsize=128)
    def _get_tissue_info(self, sample_id: str) -> Optional[str]:
        """
        Extract tissue information from sample ID (cached for performance).
        
        Args:
            sample_id: Sample identifier
            
        Returns:
            Tissue name or None if not found
        """
        try:
            return extract_tissue(sample_id)
        except Exception:
            return None
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current processing state.
        
        Returns:
            Dictionary with processing information
        """
        return {
            'input_shape': self.df.shape,
            'sample_id_column': self.sid_col,
            'configuration': str(self.config),
            'has_time_data': 'Time' in self.df.columns and self.df['Time'].notna().any(),
            'has_tissue_data': 'Tissue' in self.df.columns,
            'unique_groups': len(self.df['Group'].unique()) if 'Group' in self.df.columns else 0,
            'data_columns': [col for col in self.df.columns 
                           if col not in {self.sid_col, 'Well', 'Group', 'Animal', 'Time', 'Replicate', 'Tissue'}],
        }


class DataProcessorFactory:
    """
    Factory for creating DataProcessor instances with different configurations.
    
    This factory provides convenient methods for creating processors
    optimized for different types of analysis.
    """
    
    @staticmethod
    def create_for_time_course(
        df: DataFrame, 
        sid_col: str, 
        metric: Optional[str] = None
    ) -> DataProcessor:
        """
        Create a processor optimized for time-course analysis.
        
        Args:
            df: Input DataFrame
            sid_col: Sample ID column name
            metric: Specific metric to analyze (optional)
            
        Returns:
            DataProcessor configured for time-course analysis
        """
        config = VisualizationConfig.create_time_course(metric=metric)
        return DataProcessor(df, sid_col, config)
    
    @staticmethod
    def create_for_standard_analysis(
        df: DataFrame, 
        sid_col: str, 
        metric: Optional[str] = None
    ) -> DataProcessor:
        """
        Create a processor for standard (non-time-course) analysis.
        
        Args:
            df: Input DataFrame
            sid_col: Sample ID column name  
            metric: Specific metric to analyze (optional)
            
        Returns:
            DataProcessor configured for standard analysis
        """
        config = VisualizationConfig(
            metric=metric,
            time_course_mode=False
        )
        return DataProcessor(df, sid_col, config)
    
    @staticmethod
    def create_with_filters(
        df: DataFrame,
        sid_col: str,
        tissue_filter: Optional[str] = None,
        subpopulation_filter: Optional[str] = None,
        **config_kwargs
    ) -> DataProcessor:
        """
        Create a processor with specific data filters.
        
        Args:
            df: Input DataFrame
            sid_col: Sample ID column name
            tissue_filter: Tissue to filter by
            subpopulation_filter: Subpopulation to filter by
            **config_kwargs: Additional configuration parameters
            
        Returns:
            DataProcessor with specified filters
        """
        config = VisualizationConfig(
            tissue_filter=tissue_filter,
            subpopulation_filter=subpopulation_filter,
            **config_kwargs
        )
        return DataProcessor(df, sid_col, config)


# Utility functions for data processing
def preprocess_flowcytometry_data(df: DataFrame, sid_col: str) -> DataFrame:
    """
    Apply standard preprocessing steps to flow cytometry data.
    
    Args:
        df: Raw DataFrame
        sid_col: Sample ID column name
        
    Returns:
        Preprocessed DataFrame
    """
    df_processed = df.copy()
    
    # Remove rows with all NaN values
    df_processed = df_processed.dropna(how='all')
    
    # Remove columns with all NaN values
    df_processed = df_processed.dropna(axis=1, how='all')
    
    # Convert numeric columns to appropriate types
    numeric_columns = df_processed.select_dtypes(include=['object']).columns
    for col in numeric_columns:
        if col != sid_col:  # Don't convert sample ID column
            try:
                df_processed[col] = pd.to_numeric(df_processed[col])
            except (ValueError, TypeError):
                pass  # Keep as original type if conversion fails
    
    # Sort by sample ID for consistent processing
    if sid_col in df_processed.columns:
        df_processed = df_processed.sort_values(sid_col)
    
    return df_processed


def detect_data_characteristics(df: DataFrame) -> Dict[str, Any]:
    """
    Detect characteristics of the flow cytometry data.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary with data characteristics
    """
    characteristics = {
        'shape': df.shape,
        'has_time_data': 'Time' in df.columns and df['Time'].notna().any(),
        'has_tissue_data': 'Tissue' in df.columns,
        'has_group_data': 'Group' in df.columns,
        'num_groups': len(df['Group'].unique()) if 'Group' in df.columns else 0,
        'num_tissues': len(df['Tissue'].unique()) if 'Tissue' in df.columns else 0,
        'time_points': sorted(df['Time'].dropna().unique().tolist()) if 'Time' in df.columns else [],
        'data_columns': [col for col in df.columns 
                        if col not in {'SampleID', 'Well', 'Group', 'Animal', 'Time', 'Replicate', 'Tissue'}],
        'missing_data_percentage': (df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100,
    }
    
    return characteristics
