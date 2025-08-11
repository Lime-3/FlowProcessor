"""
Column detection and utility functions for flow cytometry visualization.
"""

import logging
import pandas as pd
from typing import Dict, List, Any

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
    Extract cell type name from column name and format it appropriately.
    
    Args:
        column_name: Full column name
        
    Returns:
        Extracted and formatted cell type name
    """
    # Handle different prefix patterns
    prefixes = [
        'FlowAIGoodEvents/Singlets/Live/',
        'Singlets/Live/',
        'Singlets/Live/'
    ]
    
    for prefix in prefixes:
        if prefix in column_name:
            # Extract the cell type part
            parts = column_name.split(prefix)
            if len(parts) > 1:
                cell_part = parts[1].split(' | ')[0]  # Remove the metric part
                # Clean up the cell type name
                if '/' in cell_part:
                    # Take the meaningful parts after Singlets/Live
                    path_parts = cell_part.split('/')
                    if len(path_parts) > 2 and path_parts[0] == 'Singlets' and path_parts[1] == 'Live':
                        # Skip Singlets/Live and take the meaningful cell type parts
                        meaningful_parts = path_parts[2:]
                        if len(meaningful_parts) == 1:
                            return meaningful_parts[0]
                        elif len(meaningful_parts) == 2:
                            # Combine parent and child cell types
                            return f"{meaningful_parts[0]}/{meaningful_parts[1]}"
                        else:
                            # Take the last two meaningful parts
                            return f"{meaningful_parts[-2]}/{meaningful_parts[-1]}"
                    else:
                        # Take the last meaningful part
                        return path_parts[-1]
                return cell_part
    
    # Fallback: try to extract from the beginning if no prefix matches
    if ' | ' in column_name:
        cell_part = column_name.split(' | ')[0]
        if '/' in cell_part:
            # Parse the hierarchical path to extract the cell type
            path_parts = cell_part.split('/')
            
            # Handle the specific format: Scatter/Singlets - FSC/Singlets - SSC/Live/CD45+/T Cells/CD4/GFP-A+
            # We need to identify the cell type before the GFP marker
            
            # Find the position of "Live" in the path
            live_index = -1
            for i, part in enumerate(path_parts):
                if 'Live' in part:
                    live_index = i
                    break
            
            if live_index >= 0 and live_index < len(path_parts) - 1:
                # Take parts after "Live" but before any GFP markers
                meaningful_parts = path_parts[live_index + 1:]
                
                # Remove GFP markers and empty parts
                clean_parts = []
                for part in meaningful_parts:
                    if part and not part.startswith('GFP') and not part.endswith('+'):
                        clean_parts.append(part)
                    elif part.endswith('+') and not part.startswith('GFP'):
                        # Handle markers ending with +
                        if part == 'CD45+':
                            # Skip CD45+ as it's a general leukocyte marker
                            continue
                        elif any(cell_marker in part for cell_marker in ['CD4', 'CD8', 'CD3']):
                            # Include specific cell markers like CD4+, CD8+
                            clean_parts.append(part.rstrip('+'))
                        else:
                            # Include other markers, removing the +
                            clean_parts.append(part.rstrip('+'))
                
                # Reconstruct the cell type name
                if len(clean_parts) == 1:
                    return clean_parts[0]
                elif len(clean_parts) == 2:
                    # For cases like "T Cells/CD4" -> return "CD4"
                    if clean_parts[1] in ['CD4', 'CD8', 'CD3']:
                        return clean_parts[1]
                    else:
                        return f"{clean_parts[0]}/{clean_parts[1]}"
                elif len(clean_parts) > 2:
                    # For longer paths, prioritize the most specific cell type
                    # Check for specific cell markers
                    for part in reversed(clean_parts):
                        if part in ['CD4', 'CD8', 'CD3']:
                            return part
                    # If no specific markers, use the last meaningful part
                    return clean_parts[-1]
                elif len(clean_parts) == 0:
                    # If no clean parts found, look for broader cell types
                    for part in meaningful_parts:
                        if 'T Cells' in part:
                            return 'T Cells'
                        elif 'Non-T Cells' in part:
                            return 'Non-T Cells'
                        elif 'B Cells' in part:
                            return 'B Cells'
            
            # Original fallback logic for other formats
            if len(path_parts) > 2 and path_parts[0] == 'Singlets' and path_parts[1] == 'Live':
                # Skip Singlets/Live and take the meaningful parts
                meaningful_parts = path_parts[2:]
                if len(meaningful_parts) == 1:
                    return meaningful_parts[0]
                elif len(meaningful_parts) == 2:
                    return f"{meaningful_parts[0]}/{meaningful_parts[1]}"
                else:
                    return f"{meaningful_parts[-2]}/{meaningful_parts[-1]}"
            else:
                # For other formats, try to extract the most meaningful part
                # Skip common prefixes and look for actual cell type names
                for part in reversed(path_parts):
                    if part and not part.startswith('GFP') and part not in ['Scatter', 'Singlets', 'FSC', 'SSC']:
                        return part
                # Last resort - return the last part
                return path_parts[-1]
        return cell_part
    
    return column_name


def enhance_cell_type_name(cell_type: str, column_name: str) -> str:
    """
    Enhance cell type name with GFP+ information based on the column context.
    
    Args:
        cell_type: Basic cell type name (e.g., "CD4", "T Cells")
        column_name: Full column name for context
        
    Returns:
        Enhanced cell type name (e.g., "CD4+GFP+", "T cells GFP+")
    """
    # Check if this is a GFP-related column
    is_gfp_column = 'GFP' in column_name or 'gfp' in column_name.lower()
    
    if not is_gfp_column:
        return cell_type
    
    # Format cell type names to match the expected display
    if cell_type == "CD4":
        return "CD4+GFP+"
    elif cell_type == "CD8":
        return "CD8+GFP+"
    elif cell_type == "T Cells":
        return "T cells GFP+"
    elif cell_type == "Non-T Cells":
        return "Non T cells GFP+"
    else:
        # Generic enhancement for other cell types
        return f"{cell_type} GFP+"


def create_enhanced_title(df: DataFrame, column_name: str, time_col: str = 'Time') -> str:
    """
    Create a simple title that shows just the metric name.
    
    Args:
        df: DataFrame containing the data
        column_name: Name of the column (cell type and metric)
        time_col: Name of the time column (unused, kept for compatibility)
        
    Returns:
        Simple title string with just the metric
    """
    # Extract metric from column name
    metric = extract_metric_name(column_name)
    
    # Return just the metric name
    return metric if metric else extract_cell_type_name(column_name)


def create_comprehensive_plot_title(df: DataFrame, metric_type: str = None, cell_types: List[str] = None, time_col: str = 'Time', filter_options=None) -> str:
    """
    Create a comprehensive plot title that includes metric name and filter information.
    
    Args:
        df: DataFrame containing the data (unused, kept for compatibility)
        metric_type: Type of metric being plotted (e.g., "Freq. of Parent")
        cell_types: List of cell types being plotted (unused, kept for compatibility)
        time_col: Name of the time column (unused, kept for compatibility)
        filter_options: Optional filter options containing selected tissues and times
        
    Returns:
        Title string with metric and filter information
    """
    # Start with the base metric name
    title = metric_type if metric_type else "Flow Cytometry Analysis"
    
    # Add filter information if available
    if filter_options:
        filter_parts = []
        
        # Add tissue filter information
        if hasattr(filter_options, 'selected_tissues') and filter_options.selected_tissues:
            if len(filter_options.selected_tissues) == 1:
                filter_parts.append(f"Tissue: {filter_options.selected_tissues[0]}")
            else:
                filter_parts.append(f"Tissues: {', '.join(filter_options.selected_tissues)}")
        
        # Add time filter information
        if hasattr(filter_options, 'selected_times') and filter_options.selected_times:
            if len(filter_options.selected_times) == 1:
                filter_parts.append(f"Time: {filter_options.selected_times[0]}")
            else:
                filter_parts.append(f"Times: {', '.join(map(str, filter_options.selected_times))}")
        
        # Append filter information to title
        if filter_parts:
            title += f" ({'; '.join(filter_parts)})"
    
    return title


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


def extract_metric_name(column_name: str) -> str:
    """
    Extract metric name from column name by taking everything after the '|' character.
    
    Args:
        column_name: Full column name
        
    Returns:
        Extracted metric name
    """
    if '|' in column_name:
        return column_name.split('|')[-1].strip()
    return column_name


def get_base_columns(df: DataFrame, time_col: str) -> List[str]:
    """
    Get base columns for plotting, including required and optional columns.
    
    Args:
        df: DataFrame to analyze
        time_col: Time column name
        
    Returns:
        List of base column names
    """
    base_columns = ['Group']  # Only use Group for x-axis
    
    if time_col not in base_columns and time_col in df.columns:
        base_columns.append(time_col)
    
    return base_columns


def detect_available_metric_types(df: DataFrame) -> List[str]:
    """
    Dynamically detect what metric types are available in the data.
    
    This function analyzes the actual column names to determine which
    metric types (like 'Freq. of Parent', 'Freq. of Live', etc.) are
    present in the data, rather than using hardcoded lists.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        List of available metric type names
    """
    available_metrics = []
    columns = [col.lower() for col in df.columns]
    
    # Check for frequency metrics
    if any('freq. of parent' in col for col in columns):
        available_metrics.append('Freq. of Parent')
    if any('freq. of live' in col for col in columns):
        available_metrics.append('Freq. of Live')
    if any('freq. of total' in col for col in columns):
        available_metrics.append('Freq. of Total')
    
    # Check for other metrics
    if any('median' in col and 'geometric' not in col for col in columns):
        available_metrics.append('Median')
    if any('mean' in col and 'geometric' not in col for col in columns):
        available_metrics.append('Mean')
    if any('geometric mean' in col for col in columns):
        available_metrics.append('Geometric Mean')
    if any('count' in col for col in columns):
        available_metrics.append('Count')
    if any('cv' in col for col in columns):
        available_metrics.append('CV')
    if any('mad' in col for col in columns):
        available_metrics.append('MAD')
    if any('mode' in col for col in columns):
        available_metrics.append('Mode')
    
    return available_metrics


def get_matching_columns_for_metric(df: DataFrame, metric_type: str) -> List[str]:
    """
    Get all columns that match a specific metric type.
    
    Args:
        df: DataFrame to search
        metric_type: Metric type to search for (e.g., 'Freq. of Parent')
        
    Returns:
        List of column names that match the metric type
    """
    matching_cols = []
    
    if metric_type == "Freq. of Parent":
        matching_cols = [col for col in df.columns if 'freq. of parent' in col.lower()]
    elif metric_type == "Freq. of Live":
        matching_cols = [col for col in df.columns if 'freq. of live' in col.lower()]
    elif metric_type == "Freq. of Total":
        matching_cols = [col for col in df.columns if 'freq. of total' in col.lower()]
    elif metric_type == "Mean":
        matching_cols = [col for col in df.columns if 'mean' in col.lower() and 'geometric mean' not in col.lower()]
    elif metric_type == "Median":
        matching_cols = [col for col in df.columns if 'median' in col.lower()]
    elif metric_type == "Geometric Mean":
        matching_cols = [col for col in df.columns if 'geometric mean' in col.lower()]
    elif metric_type == "Count":
        matching_cols = [col for col in df.columns if 'count' in col.lower()]
    elif metric_type == "CV":
        matching_cols = [col for col in df.columns if 'cv' in col.lower()]
    elif metric_type == "MAD":
        matching_cols = [col for col in df.columns if 'mad' in col.lower()]
    elif metric_type == "Mode":
        matching_cols = [col for col in df.columns if 'mode' in col.lower()]
    else:
        # Fallback to generic matching
        matching_cols = [col for col in df.columns if metric_type.lower() in col.lower()]
    
    return matching_cols 