"""
Simple Visualizer - Minimal Interface for Flow Cytometry Visualization

This module provides a super simple interface for creating visualizations
without the complexity of the full system. Just 3 main functions for 90% of use cases.
"""

import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from typing import Optional, List, Union, Dict, Any

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame
Figure = go.Figure


def _apply_standard_legend_config(fig: Figure, df: DataFrame, color_col: Optional[str] = None, **kwargs) -> Figure:
    """
    Apply standardized legend configuration to all plot types.
    
    This ensures consistent legend appearance and positioning across all graph types.
    """
    # Determine if we have a color column for legend
    if color_col and color_col in df.columns:
        legend_items = len(df[color_col].unique())
        legend_labels = df[color_col].unique().tolist()
    else:
        # Check if the figure has traces with names (for single metric plots)
        legend_items = len([trace for trace in fig.data if trace.name])
        legend_labels = [trace.name for trace in fig.data if trace.name]
    
    # Always apply legend config for consistency, even if no legend items
    # This ensures all plots have the same layout structure
    # Calculate legend width for proper 2-column layout
    legend_width = max(legend_items * 25 + 50, 100)  # Minimum 100px for legend area
    base_width = kwargs.get('width', 800)
    total_width = base_width + legend_width + 50  # 50px spacing between plot and legend
    
    # Apply 2-column layout with legend on the right
    fig.update_layout(
        width=total_width,  # Use calculated total width for 2-column layout
        legend=dict(
            x=0.85,  # Position legend in the right column (85% of total width)
            y=0.5,   # Center vertically
            yanchor="middle",
            xanchor="left",
            font_size=11,
            bordercolor='black',
            borderwidth=0.5,
            bgcolor='rgba(255,255,255,0.8)',
            orientation="v",  # Vertical orientation
            itemwidth=30,
            itemsizing="constant",
            tracegroupgap=6,
            entrywidth=30,
            entrywidthmode="pixels",
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        ),
        margin=dict(l=50, r=50, t=50, b=50),  # Equal margins for balanced layout
    )
    
    return fig


def _detect_flow_columns(df: DataFrame) -> Dict[str, str]:
    """Automatically detect flow cytometry column types."""
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


def plot(data: Union[str, DataFrame], 
         x: Optional[str] = None, 
         y: Optional[str] = None,
         plot_type: str = "scatter",
         save_html: Optional[str] = None,
         **kwargs) -> Figure:
    """
    Simple plotting function - handles 90% of visualization needs.
    
    Args:
        data: CSV file path or DataFrame
        x: X-axis column name (auto-detected if None)
        y: Y-axis column name (auto-detected if None)
        plot_type: 'scatter', 'bar', 'box', 'line', 'histogram'
        save_html: Optional path to save HTML file
        **kwargs: Additional plotly parameters
    
    Returns:
        Plotly Figure object
    
    Examples:
        >>> # Basic scatter plot (auto-detects columns)
        >>> fig = plot("data.csv")
        >>> fig.show()
        
        >>> # Box plot with custom title
        >>> fig = plot(df, x="Tissue", y="Median CD4", plot_type="box", 
        ...           title="CD4 Expression by Tissue")
        
        >>> # Save to HTML
        >>> fig = plot("data.csv", save_html="output.html")
    """
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        # Use the proper parsing logic to detect Group column
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect columns for flow cytometry data
    if x is None or y is None:
        flow_cols = _detect_flow_columns(df)
        
        # Debug logging
        logger.debug(f"Detected flow columns: {flow_cols}")
        logger.debug(f"Available columns: {list(df.columns)}")
        
        if x is None:
            # Prioritize Group column as default x-axis for flow cytometry data
            if 'Group' in df.columns:
                x = 'Group'
            elif 'group' in df.columns:
                x = 'group'
            elif flow_cols['frequencies']:
                x = flow_cols['frequencies'][0]
            else:
                x = df.columns[0] if len(df.columns) > 0 else "Sample"
        
        if y is None:
            # Prioritize "Freq. of Parent" as default y-axis for flow cytometry data
            freq_parent_cols = [col for col in flow_cols['frequencies'] if 'freq. of parent' in col.lower()]
            if freq_parent_cols:
                y = freq_parent_cols[0]
            elif flow_cols['frequencies']:
                y = flow_cols['frequencies'][0]
            elif flow_cols['medians']:
                y = flow_cols['medians'][0]
            elif flow_cols['means']:
                y = flow_cols['means'][0]
            elif flow_cols['counts']:
                y = flow_cols['counts'][0]
            elif flow_cols['geometric_means']:
                y = flow_cols['geometric_means'][0]
            elif flow_cols['cvs']:
                y = flow_cols['cvs'][0]
            elif flow_cols['mads']:
                y = flow_cols['mads'][0]
            else:
                # Fallback to any column that's not metadata
                metadata_cols = ['SampleID', 'Group', 'Animal', 'Well', 'Time', 'Replicate', 'Tissue']
                non_metadata_cols = [col for col in df.columns if col not in metadata_cols]
                if non_metadata_cols:
                    y = non_metadata_cols[0]
                else:
                    y = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # For flow cytometry data, aggregate by Group and show Mean+/-SEM
    if x == 'Group' and 'Group' in df.columns:
        # Check if y is a metric type (like "Freq. of Parent") or a specific column
        metric_types = ['Freq. of Parent', 'Freq. of Total', 'Count', 'Median', 'Mean', 'Geometric Mean', 'Mode', 'CV', 'MAD']
        if y in metric_types:
            # Find all columns matching this metric type
            matching_cols = [col for col in df.columns if y.lower() in col.lower()]
            
            # Debug logging
            logger.debug(f"Looking for metric type '{y}', found matching columns: {matching_cols}")
            
            if len(matching_cols) > 1:
                # Create a combined plot with all matching columns
                fig = _create_cell_type_comparison_plot(df, matching_cols, plot_type, **kwargs)
            elif len(matching_cols) == 1:
                # Single column - use normal aggregation
                fig = _create_single_metric_plot(df, matching_cols[0], plot_type, **kwargs)
            else:
                # No matching columns found - try to find any frequency column as fallback
                logger.warning(f"No columns found matching metric type '{y}'. Available columns: {list(df.columns)}")
                freq_cols = [col for col in df.columns if 'freq' in col.lower()]
                if freq_cols:
                    logger.info(f"Using fallback frequency column: {freq_cols[0]}")
                    fig = _create_single_metric_plot(df, freq_cols[0], plot_type, **kwargs)
                else:
                    # Last resort - use first non-metadata column
                    metadata_cols = ['SampleID', 'Group', 'Animal', 'Well', 'Time', 'Replicate', 'Tissue']
                    non_metadata_cols = [col for col in df.columns if col not in metadata_cols]
                    if non_metadata_cols:
                        logger.info(f"Using fallback column: {non_metadata_cols[0]}")
                        fig = _create_single_metric_plot(df, non_metadata_cols[0], plot_type, **kwargs)
                    else:
                        raise ValueError(f"No suitable columns found for metric type '{y}'. Available: {list(df.columns)}")
        else:
            # Specific column - use normal aggregation
            # Validate column exists
            if y not in df.columns:
                raise ValueError(f"Column '{y}' not found. Available: {list(df.columns)}")
            fig = _create_single_metric_plot(df, y, plot_type, **kwargs)
        
        # Apply standardized legend configuration to Group plots as well
        color_col = kwargs.get('color')
        fig = _apply_standard_legend_config(fig, df, color_col, **kwargs)
    else:
        # For non-Group plots, use original data
        # Validate columns exist
        if x not in df.columns:
            raise ValueError(f"Column '{x}' not found. Available: {list(df.columns)}")
        if y not in df.columns:
            raise ValueError(f"Column '{y}' not found. Available: {list(df.columns)}")
        if plot_type == "scatter":
            fig = px.scatter(df, x=x, y=y, **kwargs)
        elif plot_type == "bar":
            fig = px.bar(df, x=x, y=y, **kwargs)
        elif plot_type == "box":
            fig = px.box(df, x=x, y=y, **kwargs)
        elif plot_type == "line":
            fig = px.line(df, x=x, y=y, **kwargs)
        elif plot_type == "histogram":
            fig = px.histogram(df, x=y, **kwargs)
        else:
            raise ValueError(f"Unknown plot type: {plot_type}")
        
        # Apply standardized legend configuration to ALL plot types
        color_col = kwargs.get('color')
        fig = _apply_standard_legend_config(fig, df, color_col, **kwargs)
    
    # Auto-generate title if not provided (only for non-Group plots)
    if 'title' not in kwargs and not (x == 'Group' and 'Group' in df.columns):
        fig.update_layout(title=f"{y} vs {x}")
    
    # Apply width and height if provided in kwargs
    if 'width' in kwargs or 'height' in kwargs:
        layout_updates = {}
        if 'width' in kwargs:
            layout_updates['width'] = kwargs['width']
        if 'height' in kwargs:
            layout_updates['height'] = kwargs['height']
        fig.update_layout(**layout_updates)
    else:
        # Apply default dimensions with landscape orientation for better screen fit
        fig.update_layout(width=800, height=500)
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved plot to {save_html}")
    
    return fig


def _create_single_metric_plot(df: DataFrame, y_col: str, plot_type: str, **kwargs) -> Figure:
    """Create a plot for a single metric with aggregation."""
    # Aggregate data by Group
    agg_df = df.groupby('Group')[y_col].agg(['mean', 'std', 'count']).reset_index()
    
    # Calculate SEM (Standard Error of the Mean)
    agg_df['sem'] = agg_df['std'] / np.sqrt(agg_df['count'])
    
    # Create plot based on type with error bars
    if plot_type == "scatter":
        fig = px.scatter(agg_df, x='Group', y='mean', error_y='sem', **kwargs)
    elif plot_type == "bar":
        fig = px.bar(agg_df, x='Group', y='mean', error_y='sem', **kwargs)
    elif plot_type == "box":
        # For box plots, use original data to show distribution
        fig = px.box(df, x='Group', y=y_col, **kwargs)
    elif plot_type == "line":
        fig = px.line(agg_df, x='Group', y='mean', error_y='sem', **kwargs)
    elif plot_type == "histogram":
        fig = px.histogram(df, x=y_col, **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration to ALL plot types
    color_col = kwargs.get('color')
    fig = _apply_standard_legend_config(fig, df, color_col, **kwargs)
        
    # Update y-axis title to show it's mean with error bars
    if 'title' not in kwargs:
        fig.update_layout(title=f"Mean {y_col} ± SEM by Group")
    
    return fig


def _create_cell_type_comparison_plot(df: DataFrame, freq_cols: List[str], plot_type: str, **kwargs) -> Figure:
    """Create a plot comparing all cell types with cell types in legend."""
    # Prepare data for plotting all cell types together
    plot_data = []
    
    for col in freq_cols:
        # Extract cell type name from column
        cell_type = _extract_cell_type_name(col)
        
        # Aggregate by Group for this cell type
        agg_df = df.groupby('Group')[col].agg(['mean', 'std', 'count']).reset_index()
        agg_df['sem'] = agg_df['std'] / np.sqrt(agg_df['count'])
        agg_df['Cell Type'] = cell_type
        
        plot_data.append(agg_df)
    
    # Combine all data
    combined_df = pd.concat(plot_data, ignore_index=True)
    
    # Create plot with cell types in legend
    if plot_type == "scatter":
        fig = px.scatter(combined_df, x='Group', y='mean', color='Cell Type', error_y='sem', **kwargs)
    elif plot_type == "bar":
        fig = px.bar(combined_df, x='Group', y='mean', color='Cell Type', error_y='sem', barmode='group', **kwargs)
    elif plot_type == "box":
        # For box plots, use original data
        melted_df = df.melt(id_vars=['Group'], value_vars=freq_cols, 
                           var_name='Cell Type', value_name='Frequency')
        melted_df['Cell Type'] = melted_df['Cell Type'].apply(_extract_cell_type_name)
        fig = px.box(melted_df, x='Group', y='Frequency', color='Cell Type', **kwargs)
    elif plot_type == "line":
        fig = px.line(combined_df, x='Group', y='mean', color='Cell Type', error_y='sem', **kwargs)
    elif plot_type == "histogram":
        # For histogram, use original data
        melted_df = df.melt(id_vars=['Group'], value_vars=freq_cols, 
                           var_name='Cell Type', value_name='Frequency')
        melted_df['Cell Type'] = melted_df['Cell Type'].apply(_extract_cell_type_name)
        fig = px.histogram(melted_df, x='Frequency', color='Cell Type', **kwargs)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration to ALL plot types
    # For cell type comparison plots, the color column is 'Cell Type'
    fig = _apply_standard_legend_config(fig, combined_df, 'Cell Type', **kwargs)
    
    # Update title
    if 'title' not in kwargs:
        fig.update_layout(title="Mean Frequency of Parent ± SEM by Group and Cell Type")
    
    return fig


def _create_time_course_single_plot(df: DataFrame, time_col: str, value_col: str, group_col: Optional[str], sample_size: Optional[int] = None, **kwargs) -> Figure:
    """Create a single time course plot."""
    # Prepare data for plotting
    plot_data = []
    
    # Determine if we need to sample data
    total_rows = len(df)
    if sample_size and total_rows > sample_size:
        logger.info(f"Sampling data: {total_rows} rows -> {sample_size}")
        df = df.sample(n=sample_size, random_state=42)
    
    # Create plot
    fig = px.line(df, x=time_col, y=value_col, color=group_col,
                  title=f"Time Course - {value_col}")
    
    # Apply standardized legend configuration
    fig = _apply_standard_legend_config(fig, df, group_col, **kwargs)
    
    # Apply width and height if provided
    if 'width' in kwargs or 'height' in kwargs:
        layout_updates = {}
        if 'width' in kwargs:
            layout_updates['width'] = kwargs['width']
        if 'height' in kwargs:
            layout_updates['height'] = kwargs['height']
        fig.update_layout(**layout_updates)
    else:
        # Apply default dimensions
        fig.update_layout(width=800, height=500)
    
    return fig





def _extract_cell_type_name(column_name: str) -> str:
    """Extract cell type name from column name."""
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


def _create_enhanced_title(df: DataFrame, column_name: str, time_col: str = 'Time') -> str:
    """
    Create an enhanced title that includes both cell type and timepoint information.
    
    Args:
        df: DataFrame containing the data
        column_name: Name of the column (cell type)
        time_col: Name of the time column
        
    Returns:
        Enhanced title string with cell type and timepoint info
    """
    cell_type = _extract_cell_type_name(column_name)
    
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


def _analyze_data_size(df: DataFrame, value_cols: List[str]) -> Dict[str, Any]:
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


def time_plot(data: Union[str, DataFrame],
              time_col: Optional[str] = None,
              value_col: Optional[str] = None, 
              group_col: Optional[str] = None,
              save_html: Optional[str] = None,
              max_cell_types: int = 10,  # Limit number of cell types to plot
              sample_size: Optional[int] = None,  # Sample data points if dataset is large
              **kwargs) -> Figure:
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
    flow_cols = _detect_flow_columns(df)
    
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
            analysis = _analyze_data_size(df, matching_cols)
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
                analysis = _analyze_data_size(df, matching_cols)
                if analysis['suggested_sample_size']:
                    sample_size = analysis['suggested_sample_size']
                    logger.info(f"Auto-applying sample size: {sample_size}")
        
        if len(matching_cols) > 1:
            # Create a faceted time plot with cell types in separate subplots
            logger.info(f"time_plot: Multiple cell types detected ({len(matching_cols)}), using faceted plot")
            fig = _create_cell_type_faceted_plot(df, time_col, matching_cols, **kwargs)
        elif len(matching_cols) == 1:
            # Single column - use normal time plot
            logger.info(f"time_plot: Single cell type detected, using _create_time_course_single_plot")
            fig = _create_time_course_single_plot(df, time_col, matching_cols[0], group_col, sample_size=sample_size, **kwargs)
        else:
            # No matching columns - use original value_col
            fig = _create_time_course_single_plot(df, time_col, value_col, group_col, sample_size=sample_size, **kwargs)
    else:
        # Specific column - use normal time plot
        # Validate column exists
        if value_col not in df.columns:
            raise ValueError(f"Column '{value_col}' not found. Available: {list(df.columns)}")
        
        # Auto-apply sampling for large datasets if not explicitly set
        if sample_size is None and len(df) > 5000:
            sample_size = 1000
            logger.info(f"Auto-applying sample size: {sample_size} for large dataset")
        
        fig = _create_time_course_single_plot(df, time_col, value_col, group_col, sample_size=sample_size, **kwargs)
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved time plot to {save_html}")
    
    return fig


def compare_groups(data: Union[str, DataFrame],
                  groups: Optional[List[str]] = None,
                  metric: Optional[str] = None,
                  plot_type: str = "box",
                  save_html: Optional[str] = None,
                  **kwargs) -> Figure:
    """
    Compare multiple groups for a specific metric.
    
    Args:
        data: CSV file path or DataFrame
        groups: List of group names to compare (auto-detected if None)
        metric: Metric column to compare (auto-detected if None)
        plot_type: 'box', 'bar', or 'scatter'
        save_html: Optional path to save HTML file
    
    Returns:
        Plotly Figure object
    
    Examples:
        >>> fig = compare_groups("data.csv")
        >>> fig.show()
    """
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        # Use the proper parsing logic to detect Group column
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect metric if not provided
    if metric is None:
        flow_cols = _detect_flow_columns(df)
        metric = flow_cols['frequencies'][0] if flow_cols['frequencies'] else df.columns[0]
    
    # For flow cytometry data, each row is typically a sample
    # Create sample groups if not provided
    if groups is None:
        df = df.copy()
        df['Sample_Group'] = [f'Sample_{i+1}' for i in range(len(df))]
        group_col = 'Sample_Group'
    else:
        # Filter to specified groups if provided
        df_filtered = df[df['Group'].isin(groups)]
        if df_filtered.empty:
            raise ValueError(f"No data found for groups: {groups}")
        df = df_filtered
        group_col = 'Group'
    
    # Create comparison plot
    if plot_type == "box":
        fig = px.box(df, x=group_col, y=metric)
    elif plot_type == "bar":
        fig = px.bar(df, x=group_col, y=metric)
    elif plot_type == "scatter":
        fig = px.scatter(df, x=group_col, y=metric)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")
    
    # Apply standardized legend configuration
    fig = _apply_standard_legend_config(fig, df, None, **kwargs)
    
    fig.update_layout(
        title=f"{metric} Comparison Across Groups",
        xaxis_title="Group",
        yaxis_title=metric
    )
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved comparison plot to {save_html}")
    
    return fig


# Convenience functions for common use cases
def scatter(data, x=None, y=None, **kwargs):
    """Quick scatter plot."""
    return plot(data, x=x, y=y, plot_type="scatter", **kwargs)

def bar(data, x=None, y=None, **kwargs):
    """Quick bar plot."""
    return plot(data, x=x, y=y, plot_type="bar", **kwargs)

def box(data, x=None, y=None, **kwargs):
    """Quick box plot."""
    return plot(data, x=x, y=y, plot_type="box", **kwargs)

def histogram(data, x=None, **kwargs):
    """Quick histogram."""
    return plot(data, x=x, y=x, plot_type="histogram", **kwargs) 


def time_plot_faceted(data: Union[str, DataFrame],
                     time_col: Optional[str] = None,
                     value_col: Optional[str] = None,
                     facet_by: str = "Group",  # "Group", "Cell Type", or "Tissue"
                     save_html: Optional[str] = None,
                     **kwargs) -> Figure:
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
    flow_cols = _detect_flow_columns(df)
    
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
            fig = _create_cell_type_faceted_plot(df, time_col, matching_cols, **kwargs)
        else:
            # Facet by group/tissue, show all cell types in each subplot
            fig = _create_group_faceted_plot(df, time_col, matching_cols, facet_by, **kwargs)
    else:
        # Single column - facet by group
        fig = _create_single_column_faceted_plot(df, time_col, value_col, facet_by, **kwargs)
    
    # Save if requested
    if save_html:
        # Use enhanced HTML generation with CDN loading
        from .plotly_renderer import PlotlyRenderer
        renderer = PlotlyRenderer()
        renderer.export_to_html_optimized(fig, save_html, 'minimal')
        logger.info(f"Saved faceted time plot to {save_html}")
    
    return fig




def _create_cell_type_faceted_plot(df: DataFrame, time_col: str, value_cols: List[str], **kwargs) -> Figure:
    """Create faceted plot with each subplot showing a different cell type in vertically stacked single columns."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Limit number of cell types
    if len(value_cols) > 8:
        value_cols = sorted(value_cols)[:8]
        logger.info(f"Limited to 8 cell types for faceted plot")
    
    # Create vertically stacked single column layout
    rows = len(value_cols)
    cols = 1
    
    # Create subplots with enhanced titles
    subplot_titles = [_create_enhanced_title(df, col, time_col) for col in value_cols]
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=0.15,  # Increased spacing for better readability
        horizontal_spacing=0.05
    )
    
    # Add traces for each cell type
    for i, col in enumerate(value_cols):
        row = i + 1  # Single column layout
        col_idx = 1
        
        # Get data for this cell type
        base_columns = ['Group']  # Always include Group
        optional_columns = ['Animal', 'Well', 'Tissue']
        for opt_col in optional_columns:
            if opt_col in df.columns and opt_col not in base_columns:
                base_columns.append(opt_col)
        
        if time_col not in base_columns:
            base_columns.append(time_col)
        
        plot_df = df[base_columns + [col]].copy()
        plot_df = plot_df.dropna(subset=[col])
        
        # Add line for each group
        for group in plot_df['Group'].unique():
            group_data = plot_df[plot_df['Group'] == group]
            if not group_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=group_data[time_col],
                        y=group_data[col],
                        mode='lines+markers',
                        name=f"Group {group}",
                        showlegend=False,  # Hide from global legend
                        legendgroup=f"subplot_{row}",
                        line=dict(width=2),
                        marker=dict(size=6)
                    ),
                    row=row, col=col_idx
                )
    
    # Update layout with increased right margin to accommodate legend
    width = kwargs.get('width', 1200)
    height = max(kwargs.get('height', 800), rows * 250)  # Ensure minimum height per subplot
    fig.update_layout(
        title=f"Time Course by Cell Type",
        width=width,
        height=height,
        showlegend=False,  # Disable global legend
        margin=dict(l=50, r=200, t=50, b=50)  # Standard right margin for legend
    )
    
    # Update axes labels
    for i in range(1, rows + 1):
        fig.update_xaxes(title_text=time_col, row=i, col=1)
        fig.update_yaxes(title_text="Frequency (%)", row=i, col=1)
    
    # Create individual legends for each subplot positioned to the right
    annotations = []
    for i in range(1, rows + 1):
        # Get unique groups for this subplot
        subplot_groups = []
        subplot_traces = []
        for trace in fig.data:
            if hasattr(trace, 'legendgroup') and trace.legendgroup == f"subplot_{i}":
                if trace.name not in subplot_groups:
                    subplot_groups.append(trace.name)
                    subplot_traces.append(trace)
        
        if subplot_groups:
            # Create legend text with colored symbols
            legend_items = []
            for j, (group, trace) in enumerate(zip(subplot_groups, subplot_traces)):
                color = trace.line.color if hasattr(trace.line, 'color') and trace.line.color else f"hsl({j * 360 // len(subplot_groups)}, 70%, 50%)"
                legend_items.append(f'<span style="color: {color};">●</span> {group}')
            legend_text = "<br>".join(legend_items)
            
            # Position legend to the right of each subplot using paper coordinates
            legend_x = 1.05  # Position to the right of the plot area
            # Calculate vertical position for each subplot
            subplot_height = 1.0 / rows
            subplot_center = 1.0 - (i - 0.5) * subplot_height
            legend_y = subplot_center
            
            annotations.append(
                dict(
                    text=legend_text,
                    xref="paper",  # Use paper coordinates for consistent positioning
                    yref="paper",
                    x=legend_x,
                    y=legend_y,
                    xanchor="left",
                    yanchor="middle",
                    showarrow=False,
                    bgcolor='rgba(255,255,255,0.95)',
                    bordercolor='rgba(0,0,0,0.3)',
                    borderwidth=1,
                    font=dict(size=11, color="black"),
                    align="left"
                )
            )
    
    # Preserve existing subplot titles and add legend annotations
    existing_annotations = fig.layout.annotations if hasattr(fig.layout, 'annotations') else []
    # Filter out any existing legend annotations (those with x=1.05)
    subplot_title_annotations = [ann for ann in existing_annotations if not (hasattr(ann, 'x') and ann.x == 1.05)]
    # Combine subplot titles with new legend annotations
    all_annotations = subplot_title_annotations + annotations
    fig.update_layout(annotations=all_annotations)
    
    return fig

def _create_group_faceted_plot(df: DataFrame, time_col: str, value_cols: List[str], facet_by: str, **kwargs) -> Figure:
    """Create faceted plot with each subplot showing a different group/tissue in vertically stacked single columns."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Get unique values for faceting
    if facet_by not in df.columns:
        raise ValueError(f"Column '{facet_by}' not found in data")
    
    facet_values = sorted(df[facet_by].unique())
    
    # Create vertically stacked single column layout
    rows = len(facet_values)
    cols = 1
    
    # Create subplots with enhanced titles
    subplot_titles = []
    for facet_val in facet_values:
        # Filter data for this facet to get time information
        facet_data = df[df[facet_by] == facet_val]
        if time_col in facet_data.columns:
            # Create enhanced title with time information
            time_values = facet_data[time_col].dropna().unique()
            if len(time_values) > 0:
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
                
                subplot_titles.append(f"{facet_val}{time_info}")
            else:
                subplot_titles.append(str(facet_val))
        else:
            subplot_titles.append(str(facet_val))
    
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=0.12,  # Increased from 0.08 to 0.12 for more spacing
        horizontal_spacing=0.05
    )
    
    # Limit cell types for clarity
    if len(value_cols) > 8:
        value_cols = sorted(value_cols)[:8]
        logger.info(f"Limited to 8 cell types for group faceted plot")
    
    # Add traces for each facet value
    for i, facet_val in enumerate(facet_values):
        row = i + 1  # Single column layout
        col_idx = 1
        
        # Filter data for this facet
        facet_data = df[df[facet_by] == facet_val]
        
        # Add line for each cell type
        for col in value_cols:
            # Build base columns dynamically based on what exists in the dataframe
            base_columns = ['Group']  # Always include Group
            optional_columns = ['Animal', 'Well', 'Tissue']
            for opt_col in optional_columns:
                if opt_col in df.columns and opt_col not in base_columns:
                    base_columns.append(opt_col)
            
            if time_col not in base_columns:
                base_columns.append(time_col)
            
            plot_df = facet_data[base_columns + [col]].copy()
            plot_df = plot_df.dropna(subset=[col])
            
            if not plot_df.empty:
                fig.add_trace(
                    go.Scatter(
                        x=plot_df[time_col],
                        y=plot_df[col],
                        mode='lines+markers',
                        name=f"{_extract_cell_type_name(col)}",  # Show cell type name in legend
                        showlegend=False,  # Hide from global legend
                        legendgroup=f"subplot_{row}",  # Group by subplot
                        line=dict(width=2),
                        marker=dict(size=6)
                    ),
                    row=row, col=col_idx
                )
    
    # Update layout
    width = kwargs.get('width', 1200)
    # Adjust height for vertically stacked layout
    base_height = kwargs.get('height', 800)
    height = max(base_height, rows * 200)  # Ensure minimum height per subplot
    
    fig.update_layout(
        title=f"Time Course by {facet_by}",
        width=width,
        height=height,
        showlegend=False  # Disable global legend
    )
    
    # Update axes labels
    for i in range(1, rows + 1):
        fig.update_xaxes(title_text=time_col, row=i, col=1)
        fig.update_yaxes(title_text="Frequency (%)", row=i, col=1)
    
    # Create individual legends for each subplot positioned next to each plot
    annotations = []
    for i in range(1, rows + 1):
        # Get unique cell types for this subplot
        subplot_cell_types = []
        subplot_traces = []
        for trace in fig.data:
            if hasattr(trace, 'legendgroup') and trace.legendgroup == f"subplot_{i}":
                if trace.name not in subplot_cell_types:
                    subplot_cell_types.append(trace.name)
                    subplot_traces.append(trace)
        
        if subplot_cell_types:
            # Create legend text for this subplot with colored symbols
            legend_items = []
            for j, (cell_type, trace) in enumerate(zip(subplot_cell_types, subplot_traces)):
                # Get the color from the trace
                color = trace.line.color if hasattr(trace.line, 'color') and trace.line.color else f"hsl({j * 360 // len(subplot_cell_types)}, 70%, 50%)"
                # Create colored circle symbol
                legend_items.append(f'<span style="color: {color};">●</span> {cell_type}')
            legend_text = "<br>".join(legend_items)
            
            # Calculate position for this subplot's legend
            # Position to the right of each subplot, horizontally centered
            legend_x = 1.05  # Position to the right of the plot area (moved from 0.85 to 1.05)
            legend_y = 1.0 - (i - 0.5) / rows  # Distribute evenly
            
            annotations.append(
                dict(
                    text=legend_text,
                    xref="paper",
                    yref="paper",
                    x=legend_x,
                    y=legend_y,
                    xanchor="left",
                    yanchor="middle",
                    showarrow=False,
                    bgcolor='rgba(255,255,255,0.95)',
                    bordercolor='rgba(0,0,0,0.3)',
                    borderwidth=1,
                    font=dict(size=11, color="black"),
                    align="left"
                )
            )
    
    # Preserve existing subplot titles and add legend annotations
    existing_annotations = fig.layout.annotations if hasattr(fig.layout, 'annotations') else []
    # Filter out any existing legend annotations (those with x=1.05)
    subplot_title_annotations = [ann for ann in existing_annotations if not (hasattr(ann, 'x') and ann.x == 1.05)]
    # Combine subplot titles with new legend annotations
    all_annotations = subplot_title_annotations + annotations
    fig.update_layout(annotations=all_annotations)
    
    return fig


def _create_single_column_faceted_plot(df: DataFrame, time_col: str, value_col: str, facet_by: str, **kwargs) -> Figure:
    """Create faceted plot for a single column in vertically stacked single columns."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Get unique values for faceting
    if facet_by not in df.columns:
        raise ValueError(f"Column '{facet_by}' not found in data")
    
    facet_values = sorted(df[facet_by].unique())
    
    # Create vertically stacked single column layout
    rows = len(facet_values)
    cols = 1
    
    # Create subplots with enhanced titles
    subplot_titles = []
    for facet_val in facet_values:
        # Filter data for this facet to get time information
        facet_data = df[df[facet_by] == facet_val]
        if time_col in facet_data.columns:
            # Create enhanced title with time information
            time_values = facet_data[time_col].dropna().unique()
            if len(time_values) > 0:
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
                
                subplot_titles.append(f"{facet_val}{time_info}")
            else:
                subplot_titles.append(str(facet_val))
        else:
            subplot_titles.append(str(facet_val))
    
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=0.12,  # Increased from 0.08 to 0.12 for more spacing
        horizontal_spacing=0.05
    )
    
    # Add traces for each facet value
    for i, facet_val in enumerate(facet_values):
        row = i + 1  # Single column layout
        col_idx = 1
        
        # Filter data for this facet
        facet_data = df[df[facet_by] == facet_val]
        # Build base columns dynamically based on what exists in the dataframe
        base_columns = ['Group']  # Always include Group
        optional_columns = ['Animal', 'Well', 'Tissue']
        for opt_col in optional_columns:
            if opt_col in df.columns and opt_col not in base_columns:
                base_columns.append(opt_col)
        
        if time_col not in base_columns:
            base_columns.append(time_col)
        
        plot_df = facet_data[base_columns + [value_col]].copy()
        plot_df = plot_df.dropna(subset=[value_col])
        
        # Add line for each group
        for group in plot_df['Group'].unique():
            group_data = plot_df[plot_df['Group'] == group]
            if not group_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=group_data[time_col],
                        y=group_data[value_col],
                        mode='lines+markers',
                        name=f"Group {group}",  # Show "Group" prefix
                        showlegend=False,  # Hide from global legend
                        legendgroup=f"subplot_{row}",  # Group by subplot
                        line=dict(width=2),
                        marker=dict(size=6)
                    ),
                    row=row, col=col_idx
                )
    
    # Update layout
    width = kwargs.get('width', 1200)
    # Adjust height for vertically stacked layout
    base_height = kwargs.get('height', 800)
    height = max(base_height, rows * 200)  # Ensure minimum height per subplot
    
    fig.update_layout(
        title=f"{value_col} over Time by {facet_by}",
        width=width,
        height=height,
        showlegend=False  # Disable global legend
    )
    
    # Update axes labels
    for i in range(1, rows + 1):
        fig.update_xaxes(title_text=time_col, row=i, col=1)
        fig.update_yaxes(title_text=value_col, row=i, col=1)
    
    # Create individual legends for each subplot positioned next to each plot
    annotations = []
    for i in range(1, rows + 1):
        # Get unique groups for this subplot
        subplot_groups = []
        subplot_traces = []
        for trace in fig.data:
            if hasattr(trace, 'legendgroup') and trace.legendgroup == f"subplot_{i}":
                if trace.name not in subplot_groups:
                    subplot_groups.append(trace.name)
                    subplot_traces.append(trace)
        
        if subplot_groups:
            # Create legend text for this subplot with colored symbols
            legend_items = []
            for j, (group, trace) in enumerate(zip(subplot_groups, subplot_traces)):
                # Get the color from the trace
                color = trace.line.color if hasattr(trace.line, 'color') and trace.line.color else f"hsl({j * 360 // len(subplot_groups)}, 70%, 50%)"
                # Create colored circle symbol
                legend_items.append(f'<span style="color: {color};">●</span> {group}')
            legend_text = "<br>".join(legend_items)
            
            # Calculate position for this subplot's legend
            # Position to the right of each subplot, horizontally centered
            legend_x = 1.05  # Position to the right of the plot area (moved from 0.92 to 1.05)
            legend_y = 1.0 - (i - 0.5) / rows  # Distribute evenly
            
            annotations.append(
                dict(
                    text=legend_text,
                    xref="paper",
                    yref="paper",
                    x=legend_x,
                    y=legend_y,
                    xanchor="left",
                    yanchor="middle",
                    showarrow=False,
                    bgcolor='rgba(255,255,255,0.95)',
                    bordercolor='rgba(0,0,0,0.3)',
                    borderwidth=1,
                    font=dict(size=11, color="black"),
                    align="left"
                )
            )
    
    # Preserve existing subplot titles and add legend annotations
    existing_annotations = fig.layout.annotations if hasattr(fig.layout, 'annotations') else []
    # Filter out any existing legend annotations (those with x=1.05)
    subplot_title_annotations = [ann for ann in existing_annotations if not (hasattr(ann, 'x') and ann.x == 1.05)]
    # Combine subplot titles with new legend annotations
    all_annotations = subplot_title_annotations + annotations
    fig.update_layout(annotations=all_annotations)
    
    return fig


 