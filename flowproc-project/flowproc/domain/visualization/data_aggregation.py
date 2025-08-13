"""
Data aggregation functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Optional
from ..aggregation import group_stats, group_stats_multi

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame


def aggregate_by_group_with_sem(df: DataFrame, y_col: str, group_col: str = 'Group') -> DataFrame:
    """
    Aggregate data by group with mean, standard deviation, and standard error of the mean.
    
    Args:
        df: DataFrame to aggregate
        y_col: Column to aggregate
        group_col: Column to group by (default: 'Group')
        
    Returns:
        Aggregated DataFrame with mean, std, count, and sem columns
    """
    # Delegate to centralized aggregation helper
    return group_stats(df, y_col, group_cols=group_col)


def aggregate_multiple_metrics_by_group(df: DataFrame, freq_cols: List[str], group_col: str = 'Group') -> DataFrame:
    """
    Aggregate multiple metrics by group for cell type comparison plots.
    
    Args:
        df: DataFrame to aggregate
        freq_cols: List of frequency columns to aggregate
        group_col: Column to group by (default: 'Group')
        
    Returns:
        Combined DataFrame with all metrics aggregated by group
    """
    # Centralized aggregation in long form
    combined_df = group_stats_multi(
        df,
        value_cols=freq_cols,
        group_cols=group_col,
        long_name='Cell Type',
        value_name='Value',
    )

    # Preserve existing label enhancements
    from .column_utils import build_unique_cell_type_labels, enhance_cell_type_name
    label_map = build_unique_cell_type_labels(freq_cols)
    combined_df['Cell Type'] = combined_df['Cell Type'].map(
        lambda original: enhance_cell_type_name(label_map.get(original, original), original)
    )

    return combined_df


def sample_data_if_large(df: DataFrame, sample_size: Optional[int] = None, 
                        total_rows_threshold: int = 5000) -> DataFrame:
    """
    Sample data if the dataset is large to improve performance.
    
    Args:
        df: DataFrame to potentially sample
        sample_size: Number of samples to take (if None, auto-determined)
        total_rows_threshold: Threshold above which to apply sampling
        
    Returns:
        Sampled DataFrame or original DataFrame if no sampling needed
    """
    total_rows = len(df)
    
    # Auto-apply sampling for large datasets if not explicitly set
    if sample_size is None and total_rows > total_rows_threshold:
        # Use analysis recommendations or default
        from .column_utils import analyze_data_size
        # Get all numeric columns for analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            analysis = analyze_data_size(df, numeric_cols)
            if analysis['suggested_sample_size']:
                sample_size = analysis['suggested_sample_size']
                logger.info(f"Auto-applying sample size: {sample_size}")
            else:
                sample_size = 1000
                logger.info(f"Auto-applying default sample size: {sample_size}")
    
    # Apply sampling if needed
    if sample_size and total_rows > sample_size:
        logger.info(f"Sampling data: {total_rows} rows -> {sample_size}")
        df = df.sample(n=sample_size, random_state=42)
    
    return df


def prepare_data_for_plotting(df: DataFrame, base_columns: List[str], value_col: str) -> DataFrame:
    """
    Prepare data for plotting by selecting relevant columns and dropping NaN values.
    
    Args:
        df: Input DataFrame
        base_columns: Base columns to include
        value_col: Value column to plot
        
    Returns:
        Prepared DataFrame for plotting
    """
    # Ensure all required columns exist
    required_cols = base_columns + [value_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}. Available: {list(df.columns)}")
    
    # Select relevant columns and drop NaN values
    plot_df = df[required_cols].copy()
    plot_df = plot_df.dropna(subset=[value_col])
    
    return plot_df 