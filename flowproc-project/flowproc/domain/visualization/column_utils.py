"""
Column detection and utility functions for flow cytometry visualization.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame


def detect_flow_columns(df: DataFrame) -> Dict[str, List[str]]:
    """
    Automatically detect flow cytometry column types.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary mapping column types to lists of column names
    """
    columns = list(df.columns)
    
    # Find frequency columns - be more flexible about detection
    freq_cols = []
    for col in columns:
        col_lower = col.lower()
        # Look for frequency indicators
        if any(indicator in col_lower for indicator in ['freq', 'frequency', '%']):
            freq_cols.append(col)
    
    # Find median columns
    median_cols = [col for col in columns if 'Median' in col]
    
    # Find geometric mean columns first (longer pattern)
    geo_mean_cols = []
    for col in columns:
        if any(indicator in col for indicator in ['Geometric Mean', 'Geo Mean', 'GeoMean']):
            geo_mean_cols.append(col)
    
    # Find mean columns (but exclude geometric mean columns)
    mean_cols = []
    for col in columns:
        if 'Mean' in col and col not in geo_mean_cols:
            mean_cols.append(col)
    
    # Find count columns
    count_cols = [col for col in columns if 'Count' in col]
    
    # Find CV columns
    cv_cols = [col for col in columns if 'CV' in col]
    
    # Find MAD columns
    mad_cols = [col for col in columns if 'MAD' in col]
    
    return {
        'frequencies': freq_cols,
        'medians': median_cols,
        'means': mean_cols,
        'counts': count_cols,
        'geometric_means': geo_mean_cols,
        'cvs': cv_cols,
        'mads': mad_cols,
        'all_metrics': freq_cols + median_cols + mean_cols + count_cols + geo_mean_cols + cv_cols + mad_cols
    }


def extract_cell_type_name(column_name: str) -> str:
    """
    Extract cell type name from column name.
    
    Args:
        column_name: Full column name
        
    Returns:
        Extracted cell type name
    """
    # Remove the common prefix and suffix
    if 'FlowAIGoodEvents/Singlets/Live/' in column_name:
        # Extract the cell type part
        parts = column_name.split('FlowAIGoodEvents/Singlets/Live/')
        if len(parts) > 1:
            cell_part = parts[1].split(' | ')[0]  # Remove the metric part
            # Clean up the cell type name
            if '/' in cell_part:
                cell_part = cell_part.split('/')[-1]  # Take the last part
            return cell_part
    return column_name


def create_enhanced_title(df: DataFrame, column_name: str, time_col: str = 'Time') -> str:
    """
    Create an enhanced title that includes both cell type and timepoint information.
    
    Args:
        df: DataFrame containing the data
        column_name: Name of the column (cell type)
        time_col: Name of the time column
        
    Returns:
        Enhanced title string with cell type and timepoint info
    """
    cell_type = extract_cell_type_name(column_name)
    
    # Get timepoint information if available
    time_info = ""
    if time_col in df.columns:
        time_values = df[time_col].dropna().unique()
        if len(time_values) > 0:
            # Format time values nicely
            time_strs = []
            for time_val in sorted(time_values):
                if isinstance(time_val, (int, float)):
                    if time_val >= 24:  # Convert to days if >= 24 hours
                        days = time_val / 24
                        if days.is_integer():
                            time_strs.append(f"Day {int(days)}")
                        else:
                            time_strs.append(f"Day {days:.1f}")
                    elif time_val >= 1:  # Show as hours
                        if time_val.is_integer():
                            time_strs.append(f"{int(time_val)}h")
                        else:
                            time_strs.append(f"{time_val:.1f}h")
                    else:  # Convert to minutes
                        minutes = time_val * 60
                        if minutes.is_integer():
                            time_strs.append(f"{int(minutes)}min")
                        else:
                            time_strs.append(f"{minutes:.1f}min")
                else:
                    time_strs.append(str(time_val))
            
            if len(time_strs) == 1:
                time_info = f" ({time_strs[0]})"
            elif len(time_strs) <= 3:
                time_info = f" ({', '.join(time_strs)})"
            else:
                time_info = f" ({time_strs[0]}-{time_strs[-1]})"
    
    return f"{cell_type}{time_info}"


def analyze_data_size(df: DataFrame, value_cols: List[str]) -> Dict[str, Any]:
    """
    Analyze data size and suggest performance optimizations.
    
    Args:
        df: Input DataFrame
        value_cols: List of value columns to analyze
        
    Returns:
        Dictionary with analysis results and recommendations
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    num_cell_types = len(value_cols)
    
    # Calculate estimated memory usage (rough approximation)
    estimated_memory_mb = (total_rows * total_cols * 8) / (1024 * 1024)  # 8 bytes per value
    
    # Determine complexity level
    if total_rows > 10000 or num_cell_types > 20:
        complexity = "high"
    elif total_rows > 5000 or num_cell_types > 10:
        complexity = "medium"
    else:
        complexity = "low"
    
    # Suggest optimizations
    recommendations = []
    suggested_max_cell_types = 10
    suggested_sample_size = None
    
    if complexity == "high":
        recommendations.append("High complexity detected - applying aggressive optimizations")
        suggested_max_cell_types = min(5, num_cell_types)
        suggested_sample_size = 500
    elif complexity == "medium":
        recommendations.append("Medium complexity detected - applying moderate optimizations")
        suggested_max_cell_types = min(10, num_cell_types)
        suggested_sample_size = 1000
    
    if num_cell_types > suggested_max_cell_types:
        recommendations.append(f"Limiting cell types from {num_cell_types} to {suggested_max_cell_types}")
    
    if suggested_sample_size and total_rows > suggested_sample_size * num_cell_types:
        recommendations.append(f"Sampling {suggested_sample_size} points per cell type")
    
    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "num_cell_types": num_cell_types,
        "estimated_memory_mb": estimated_memory_mb,
        "complexity": complexity,
        "recommendations": recommendations,
        "suggested_max_cell_types": suggested_max_cell_types,
        "suggested_sample_size": suggested_sample_size
    }


def get_base_columns(df: DataFrame, time_col: str) -> List[str]:
    """
    Get base columns for plotting, including required and optional columns.
    
    Args:
        df: DataFrame to analyze
        time_col: Time column name
        
    Returns:
        List of base column names
    """
    base_columns = ['Group']  # Always include Group
    optional_columns = ['Animal', 'Well', 'Tissue']
    
    for opt_col in optional_columns:
        if opt_col in df.columns and opt_col not in base_columns:
            base_columns.append(opt_col)
    
    if time_col not in base_columns:
        base_columns.append(time_col)
    
    return base_columns 