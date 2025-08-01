"""
Time course plot functions for flow cytometry visualization.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Union

from .column_utils import detect_flow_columns, analyze_data_size
from .plot_creators import create_time_course_single_plot
from .faceted_plots import create_cell_type_faceted_plot, create_group_faceted_plot, create_single_column_faceted_plot

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame


def time_plot(data: Union[str, DataFrame],
              time_col: Optional[str] = None,
              value_col: Optional[str] = None, 
              group_col: Optional[str] = None,
              save_html: Optional[str] = None,
              max_cell_types: int = 10,  # Limit number of cell types to plot
              sample_size: Optional[int] = None,  # Sample data points if dataset is large
              **kwargs):
    """
    Create time-course plots - optimized for temporal data.
    
    Args:
        data: CSV file path or DataFrame
        time_col: Time column name (auto-detected if None)
        value_col: Value column to plot (auto-detected if None) - can be a metric type like "Freq. of Parent"
        group_col: Group column for different lines (auto-detected if None)
        save_html: Optional path to save HTML file
        max_cell_types: Maximum number of cell types to include in multi-plot (default: 10)
        sample_size: If provided, sample this many data points per cell type for large datasets
    
    Returns:
        Plotly Figure object
    
    Examples:
        >>> fig = time_plot("timecourse.csv")
        >>> fig.show()
    """
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        # Use the proper parsing logic to detect Group column
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect columns
    flow_cols = detect_flow_columns(df)
    
    if time_col is None:
        # Look for time-related columns
        time_candidates = [col for col in df.columns if 'time' in col.lower() or 'day' in col.lower()]
        time_col = time_candidates[0] if time_candidates else df.columns[0]
    
    # Handle value_col selection - check if it's a metric type or specific column
    if value_col is None:
        # Default to "Freq. of Parent" for flow cytometry data
        freq_parent_cols = [col for col in flow_cols['frequencies'] if 'Freq. of Parent' in col]
        if freq_parent_cols:
            value_col = 'Freq. of Parent'  # Use as metric type
        else:
            value_col = flow_cols['frequencies'][0] if flow_cols['frequencies'] else df.columns[1]
    
    # Check if value_col is a metric type (like "Freq. of Parent") or a specific column
    metric_types = ['Freq. of Parent', 'Freq. of Total', 'Count', 'Median', 'Mean', 'Geometric Mean', 'Mode', 'CV', 'MAD']
    if value_col in metric_types:
        # Find all columns matching this metric type
        matching_cols = [col for col in df.columns if value_col.lower() in col.lower()]
        
        # Debug logging
        logger.debug(f"Looking for metric type '{value_col}', found matching columns: {matching_cols}")
        
        # Analyze data size and get recommendations
        if matching_cols:
            analysis = analyze_data_size(df, matching_cols)
            logger.info(f"Data analysis: {analysis['total_rows']} rows, {analysis['num_cell_types']} cell types, {analysis['complexity']} complexity")
            
            if analysis['recommendations']:
                for rec in analysis['recommendations']:
                    logger.info(f"Recommendation: {rec}")
        
        # Apply cell type limiting for performance
        if len(matching_cols) > max_cell_types:
            logger.info(f"Limiting cell types from {len(matching_cols)} to {max_cell_types} for performance")
            # Sort by column name and take the first max_cell_types
            matching_cols = sorted(matching_cols)[:max_cell_types]
        
        # Auto-apply sampling for large datasets if not explicitly set
        if sample_size is None and len(df) > 5000:
            # Use analysis recommendations or default
            if matching_cols and len(matching_cols) > 0:
                analysis = analyze_data_size(df, matching_cols)
                if analysis['suggested_sample_size']:
                    sample_size = analysis['suggested_sample_size']
                    logger.info(f"Auto-applying sample size: {sample_size}")
        
        if len(matching_cols) > 1:
            # Create a faceted time plot with cell types in separate subplots
            logger.info(f"time_plot: Multiple cell types detected ({len(matching_cols)}), using faceted plot")
            fig = create_cell_type_faceted_plot(df, time_col, matching_cols, **kwargs)
        elif len(matching_cols) == 1:
            # Single column - use normal time plot
            logger.info(f"time_plot: Single cell type detected, using _create_time_course_single_plot")
            fig = create_time_course_single_plot(df, time_col, matching_cols[0], group_col, sample_size=sample_size, **kwargs)
        else:
            # No matching columns - use original value_col
            fig = create_time_course_single_plot(df, time_col, value_col, group_col, sample_size=sample_size, **kwargs)
    else:
        # Specific column - use normal time plot
        # Validate column exists
        if value_col not in df.columns:
            raise ValueError(f"Column '{value_col}' not found. Available: {list(df.columns)}")
        
        # Auto-apply sampling for large datasets if not explicitly set
        if sample_size is None and len(df) > 5000:
            sample_size = 1000
            logger.info(f"Auto-applying sample size: {sample_size} for large dataset")
        
        fig = create_time_course_single_plot(df, time_col, value_col, group_col, sample_size=sample_size, **kwargs)
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved time plot to {save_html}")
    
    return fig


def time_plot_faceted(data: Union[str, DataFrame],
                     time_col: Optional[str] = None,
                     value_col: Optional[str] = None,
                     facet_by: str = "Group",  # "Group", "Cell Type", or "Tissue"
                     save_html: Optional[str] = None,
                     **kwargs):
    """
    Create faceted time-course plots - industry standard approach.
    
    Creates separate subplots for each group/cell type, making it easier to
    compare trends across different categories.
    
    Args:
        data: CSV file path or DataFrame
        time_col: Time column name (auto-detected if None)
        value_col: Value column to plot (auto-detected if None)
        facet_by: What to facet by ("Group", "Cell Type", "Tissue")
        save_html: Optional path to save HTML file
    
    Returns:
        Plotly Figure object with subplots
    """
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect columns
    flow_cols = detect_flow_columns(df)
    
    if time_col is None:
        time_candidates = [col for col in df.columns if 'time' in col.lower() or 'day' in col.lower()]
        time_col = time_candidates[0] if time_candidates else df.columns[0]
    
    if value_col is None:
        freq_parent_cols = [col for col in flow_cols['frequencies'] if 'Freq. of Parent' in col]
        if freq_parent_cols:
            value_col = 'Freq. of Parent'
        else:
            value_col = flow_cols['frequencies'][0] if flow_cols['frequencies'] else df.columns[1]
    
    # Handle metric types vs specific columns
    metric_types = ['Freq. of Parent', 'Freq. of Total', 'Count', 'Median', 'Mean', 'Geometric Mean', 'Mode', 'CV', 'MAD']
    
    if value_col in metric_types:
        # Find all columns matching this metric type
        matching_cols = [col for col in df.columns if value_col.lower() in col.lower()]
        
        if facet_by == "Cell Type":
            # Facet by cell type (each subplot is a different cell type)
            fig = create_cell_type_faceted_plot(df, time_col, matching_cols, **kwargs)
        else:
            # Facet by group/tissue, show all cell types in each subplot
            fig = create_group_faceted_plot(df, time_col, matching_cols, facet_by, **kwargs)
    else:
        # Single column - facet by group
        fig = create_single_column_faceted_plot(df, time_col, value_col, facet_by, **kwargs)
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved faceted time plot to {save_html}")
    
    return fig 