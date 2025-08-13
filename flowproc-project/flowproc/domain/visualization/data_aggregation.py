"""
Data aggregation functions for flow cytometry visualization.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Optional

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
    # Aggregate data by Group
    agg_df = df.groupby(group_col)[y_col].agg(['mean', 'std', 'count']).reset_index()
    
    # Replace NaN means with 0.0 for visualization (happens when all values in group are NaN)
    agg_df['mean'] = agg_df['mean'].fillna(0.0)
    
    # Calculate SEM (Standard Error of the Mean)
    # Handle cases where std is NaN (single value in group) or count is 1
    agg_df['sem'] = np.where(
        (agg_df['count'] > 1) & agg_df['std'].notna(),
        agg_df['std'] / np.sqrt(agg_df['count']),
        0  # Use 0 for SEM when there's only one value or std is NaN
    )
    
    return agg_df


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
    plot_data = []
    
    # Check if we have multiple tissues
    # For single metric plots, don't separate by tissue - combine all data
    # This creates cleaner plots with cell types as the main distinction
    tissues_detected = False  # Disable tissue separation for now to fix plotting issues
    
    # Build stable labels once for all columns using only '/' and '|'
    from .column_utils import build_unique_cell_type_labels, enhance_cell_type_name
    label_map = build_unique_cell_type_labels(freq_cols)

    for col in freq_cols:
        # Extract label and then enhance if context requires (e.g., GFP tag already present)
        basic_cell_type = label_map.get(col, col)
        cell_type = enhance_cell_type_name(basic_cell_type, col)
        
        if tissues_detected:
            # When multiple tissues detected, aggregate by Group AND Tissue separately
            for tissue in df['Tissue'].unique():
                tissue_df = df[df['Tissue'] == tissue]
                if not tissue_df.empty:
                    agg_df = aggregate_by_group_with_sem(tissue_df, col, group_col)
                    agg_df['Cell Type'] = f"{cell_type} ({tissue})"  # Include tissue in cell type name
                    plot_data.append(agg_df)
        else:
            # Single tissue or no tissue info - aggregate by Group only
            agg_df = aggregate_by_group_with_sem(df, col, group_col)
            agg_df['Cell Type'] = cell_type
            plot_data.append(agg_df)
    
    # Combine all data
    combined_df = pd.concat(plot_data, ignore_index=True)
    
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