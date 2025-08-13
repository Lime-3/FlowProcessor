"""
Unified Timecourse Visualization Module for Flow Cytometry Data

This module provides a single, consistent interface for creating timecourse plots
with smart auto-detection, performance optimization, and industry-standard defaults.
"""

import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple

from .column_utils import (
    detect_flow_columns, 
    analyze_data_size, 
    detect_available_metric_types, 
    get_matching_columns_for_metric,
    extract_metric_name,
    create_comprehensive_plot_title,
    create_timecourse_plot_title,
    create_population_shortname
)
from .legend_config import configure_legend
from .plot_utils import get_group_label_map
from .data_aggregation import aggregate_by_group_with_sem

logger = logging.getLogger(__name__)

# Type aliases for simplicity
DataFrame = pd.DataFrame


def create_timecourse_visualization(
    data: Union[str, DataFrame],
    time_column: Optional[str] = None,
    metric: Optional[str] = None,
    group_by: Optional[str] = None,
    facet_by: Optional[str] = None,
    plot_type: str = "line",
    aggregation: str = "mean_sem",
    max_cell_types: int = 10,
    sample_size: Optional[int] = None,
    filter_options: Optional[Dict] = None,
    population_filter: Optional[str] = None,  # New: filter for specific population
    save_html: Optional[str] = None,
    **kwargs
) -> go.Figure:
    """
    Unified timecourse visualization function - single entry point for all timecourse plots.
    
    Args:
        data: CSV file path or DataFrame
        time_column: Time column name (auto-detected if None)
        metric: Metric type (e.g., "Freq. of Parent") or specific column name
        group_by: Column to group data by (e.g., "Group", "Treatment")
        facet_by: What to facet by ("Group", "Cell Type", "Tissue", None for single plot)
        plot_type: Plot type ("line", "scatter", "area")
        aggregation: Data aggregation method ("mean_sem", "median_iqr", "raw")
        max_cell_types: Maximum number of cell types to include
        sample_size: Sample size for large datasets
        filter_options: Filtering options for data
        population_filter: Specific population to filter for (None for all populations)
        save_html: Optional path to save HTML file
        **kwargs: Additional plotly parameters
    
    Returns:
        Plotly Figure object
    
    Examples:
        >>> # Basic timecourse plot
        >>> fig = create_timecourse_visualization("data.csv")
        
        >>> # Faceted by cell type
        >>> fig = create_timecourse_visualization("data.csv", facet_by="Cell Type")
        
        >>> # Custom time and metric
        >>> fig = create_timecourse_visualization("data.csv", 
        ...                                    time_column="Day", 
        ...                                    metric="Freq. of Live")
        
        >>> # Single population timecourse
        >>> fig = create_timecourse_visualization("data.csv", 
        ...                                    population_filter="CD4+")
    """
    # Load and prepare data
    df, time_col, value_cols, group_col = _prepare_data(
        data, time_column, metric, group_by, max_cell_types, sample_size, population_filter
    )
    
    # Determine visualization strategy
    if facet_by:
        fig = _create_faceted_timecourse(
            df, time_col, value_cols, group_col, facet_by, plot_type, 
            aggregation, filter_options, **kwargs
        )
    else:
        fig = _create_single_timecourse(
            df, time_col, value_cols, group_col, plot_type, 
            aggregation, filter_options, **kwargs
        )
    
    # Save if requested
    if save_html:
        _save_visualization(fig, save_html)
    
    return fig


def _prepare_data(
    data: Union[str, DataFrame],
    time_column: Optional[str],
    metric: Optional[str],
    group_by: Optional[str],
    max_cell_types: int,
    sample_size: Optional[int],
    population_filter: Optional[str]
) -> Tuple[DataFrame, str, List[str], Optional[str]]:
    """Prepare and validate data for timecourse visualization."""
    # Load data if string path provided
    if isinstance(data, (str, Path)):
        from flowproc.domain.parsing import load_and_parse_df
        df, _ = load_and_parse_df(Path(data))
    else:
        df = data
    
    # Auto-detect time column
    time_col = _detect_time_column(df, time_column)
    
    # Auto-detect group column
    group_col = _detect_group_column(df, group_by)
    
    # Handle metric selection and get value columns
    value_cols = _detect_value_columns(df, metric, max_cell_types)
    
    # Apply sampling if needed
    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
        logger.info(f"Applied sampling: {sample_size} data points")
    
    # Apply population filter if provided
    if population_filter:
        # Filter value columns to only include those matching the selected population
        filtered_value_cols = []
        for col in value_cols:
            if population_filter in col:
                filtered_value_cols.append(col)
        
        if filtered_value_cols:
            value_cols = filtered_value_cols
            logger.info(f"Applied population filter '{population_filter}': {len(value_cols)} columns remaining")
        else:
            logger.warning(f"No columns found matching population '{population_filter}', using all available columns")
    
    return df, time_col, value_cols, group_col


def _detect_time_column(df: DataFrame, time_column: Optional[str]) -> str:
    """Auto-detect time column from common patterns."""
    if time_column and time_column in df.columns:
        return time_column
    
    # Look for time-related columns
    time_candidates = [
        col for col in df.columns 
        if any(keyword in col.lower() for keyword in ['time', 'day', 'hour', 'week', 'minute'])
    ]
    
    if time_candidates:
        time_col = time_candidates[0]
        logger.info(f"Auto-detected time column: {time_col}")
        return time_col
    
    # Fallback to first column
    logger.warning(f"No time column detected, using first column: {df.columns[0]}")
    return df.columns[0]


def _detect_group_column(df: DataFrame, group_by: Optional[str]) -> Optional[str]:
    """Auto-detect group column from common patterns."""
    if group_by and group_by in df.columns:
        return group_by
    
    # Look for group-related columns
    group_candidates = [
        col for col in df.columns 
        if any(keyword in col.lower() for keyword in ['group', 'treatment', 'condition', 'sample'])
    ]
    
    # Filter out SampleID columns that are not actual group columns
    filtered_candidates = []
    for col in group_candidates:
        col_lower = col.lower()
        # Skip columns that are clearly sample identifiers, not group columns
        if any(skip_keyword in col_lower for skip_keyword in ['sampleid', 'sample_id', 'id']):
            continue
        # Skip columns that contain file extensions or look like file paths
        if any(ext in col_lower for ext in ['.fcs', '.csv', '.txt']):
            continue
        filtered_candidates.append(col)
    
    if filtered_candidates:
        group_col = filtered_candidates[0]
        logger.info(f"Auto-detected group column: {group_col}")
        return group_col
    
    # If no suitable group column found, return None
    # This will result in a single trace plot without grouping
    logger.info("No suitable group column detected, will create single trace plot")
    return None


def _detect_value_columns(df: DataFrame, metric: Optional[str], max_cell_types: int) -> List[str]:
    """Detect value columns based on metric type or fallback to flow cytometry columns."""
    if metric:
        # Check if it's a metric type (like "Freq. of Parent")
        metric_types = detect_available_metric_types(df)
        if metric in metric_types:
            matching_cols = get_matching_columns_for_metric(df, metric)
            logger.info(f"Found {len(matching_cols)} columns for metric '{metric}'")
            
            # Apply cell type limiting
            if len(matching_cols) > max_cell_types:
                matching_cols = sorted(matching_cols)[:max_cell_types]
                logger.info(f"Limited to {max_cell_types} cell types for performance")
            
            return matching_cols
        elif metric in df.columns:
            return [metric]
        else:
            logger.warning(f"Metric '{metric}' not found, falling back to auto-detection")
    
    # Fallback to flow cytometry column detection
    flow_cols = detect_flow_columns(df)
    if flow_cols['frequencies']:
        # Prioritize "Freq. of Parent" and "Freq. of Live"
        freq_parent_cols = [col for col in flow_cols['frequencies'] 
                           if 'freq. of parent' in col.lower()]
        freq_live_cols = [col for col in flow_cols['frequencies'] 
                          if 'freq. of live' in col.lower()]
        
        if freq_parent_cols:
            return freq_parent_cols[:max_cell_types]
        elif freq_live_cols:
            return freq_live_cols[:max_cell_types]
        else:
            return flow_cols['frequencies'][:max_cell_types]
    
    # Last resort: use second column
    if len(df.columns) > 1:
        return [df.columns[1]]
    else:
        return [df.columns[0]]


def _create_single_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> go.Figure:
    """Create a single timecourse plot (no faceting)."""
    # If we have multiple value columns but want a single population plot,
    # we should only use the first one to ensure single population display
    if len(value_cols) > 1:
        # Check if this is a single population request (from filter_options or kwargs)
        population_filter = kwargs.get('population_filter') or (filter_options.get('population_filter') if filter_options else None)
        
        if population_filter:
            # Single population requested - use only the first matching column
            logger.info(f"Single population timecourse requested for '{population_filter}', using first matching column: {value_cols[0]}")
            value_cols = [value_cols[0]]
        else:
            # Multiple populations without specific filter - create overlay plot
            logger.info(f"Multiple populations detected ({len(value_cols)}), creating overlay timecourse plot")
            return _create_overlay_timecourse(
                df, time_col, value_cols, group_col, plot_type, 
                aggregation, filter_options, **kwargs
            )
    
    # Single metric - create simple timecourse
    return _create_single_metric_timecourse(
        df, time_col, value_cols[0], group_col, plot_type, 
        aggregation, filter_options, **kwargs
    )


def _create_single_metric_timecourse(
    df: DataFrame,
    time_col: str,
    value_col: str,
    group_col: Optional[str],
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> go.Figure:
    """Create timecourse plot for a single metric."""
    # Extract internal-only option so it isn't passed to Plotly
    user_group_labels = kwargs.pop('user_group_labels', None)
    # Debug logging
    logger.info(f"Creating single metric timecourse for column: {value_col}")
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Time column: {time_col}, unique values: {df[time_col].dropna().unique()}")
    logger.info(f"Value column: {value_col}, range: {df[value_col].min():.3f} to {df[value_col].max():.3f}")
    if group_col:
        logger.info(f"Group column: {group_col}, unique values: {df[group_col].dropna().unique()}")
    
    # Apply aggregation if requested
    if aggregation == "mean_sem" and group_col:
        # For timecourse plots, we need to aggregate by both group and time
        plot_df = df.groupby([group_col, time_col])[value_col].agg(['mean', 'std', 'count']).reset_index()
        plot_df['sem'] = plot_df['std'] / np.sqrt(plot_df['count'])
        y_col = 'mean'
        error_y = 'sem'
        logger.info(f"Aggregated data shape: {plot_df.shape}")
        logger.info(f"Aggregated data columns: {list(plot_df.columns)}")
    else:
        plot_df = df
        y_col = value_col
        error_y = None
        logger.info(f"Using raw data, shape: {plot_df.shape}")
    
    # Create plot based on type with error bars
    if plot_type == "line":
        if group_col and group_col in plot_df.columns:
            if error_y and error_y in plot_df.columns:
                fig = px.line(plot_df, x=time_col, y=y_col, color=group_col, error_y=error_y, **kwargs)
                logger.info(f"Created line plot with grouping by {group_col} and SEM error bars")
            else:
                fig = px.line(plot_df, x=time_col, y=y_col, color=group_col, **kwargs)
                logger.info(f"Created line plot with grouping by {group_col} (no error bars)")
        else:
            if error_y and error_y in plot_df.columns:
                fig = px.line(plot_df, x=time_col, y=y_col, error_y=error_y, **kwargs)
                logger.info(f"Created line plot without grouping and SEM error bars")
            else:
                fig = px.line(plot_df, x=time_col, y=y_col, **kwargs)
                logger.info(f"Created line plot without grouping (no error bars)")
    elif plot_type == "scatter":
        if group_col and group_col in plot_df.columns:
            if error_y and error_y in plot_df.columns:
                fig = px.scatter(plot_df, x=time_col, y=y_col, color=group_col, error_y=error_y, **kwargs)
            else:
                fig = px.scatter(plot_df, x=time_col, y=y_col, color=group_col, **kwargs)
        else:
            if error_y and error_y in plot_df.columns:
                fig = px.scatter(plot_df, x=time_col, y=y_col, error_y=error_y, **kwargs)
            else:
                fig = px.scatter(plot_df, x=time_col, y=y_col, error_y=error_y, **kwargs)
    elif plot_type == "area":
        if group_col and group_col in plot_df.columns:
            if error_y and error_y in plot_df.columns:
                fig = px.area(plot_df, x=time_col, y=y_col, color=group_col, error_y=error_y, **kwargs)
            else:
                fig = px.area(plot_df, x=time_col, y=y_col, color=group_col, **kwargs)
        else:
            if error_y and error_y in plot_df.columns:
                fig = px.area(plot_df, x=time_col, y=y_col, error_y=error_y, **kwargs)
            else:
                fig = px.area(plot_df, x=time_col, y=y_col, error_y=error_y, **kwargs)
    else:
        raise ValueError(f"Unsupported plot type: {plot_type}")
    
    # Update trace names to use shortnames for better legend display
    for trace in fig.data:
        if trace.name and trace.name != value_col:
            # This is a group trace, keep the group name
            continue
        else:
            # This is the main trace, update to use shortname
            shortname = create_population_shortname(value_col)
            trace.name = shortname
            logger.info(f"Updated trace name from '{value_col}' to '{shortname}'")
    
    # Debug: Check what traces were created
    logger.info(f"Created figure with {len(fig.data)} traces")
    for i, trace in enumerate(fig.data):
        logger.info(f"Trace {i}: {trace.name}, x points: {len(trace.x)}, y points: {len(trace.y)}")
    
    # Apply legend configuration
    width = kwargs.get('width', 1200)
    height = kwargs.get('height', 500)
    
    # Determine appropriate legend title based on plot type
    if group_col:
        legend_title = "Groups"
    else:
        legend_title = "Populations"
    
    fig = configure_legend(
        fig, df, group_col, is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
    
    # Update title and labels
    if 'title' not in kwargs:
        metric_name = extract_metric_name(value_col)
        logger.debug(f"Time plot - Creating title with metric: {metric_name}")
        title = create_timecourse_plot_title(df, metric_name, [value_col], filter_options=filter_options)
        logger.debug(f"Time plot - Title created: {title}")
        fig.update_layout(
            title=title,
            margin=dict(t=80)  # Add more top margin for title spacing
        )
        
        # Debug: Verify the title was applied
        if hasattr(fig.layout, 'title') and hasattr(fig.layout.title, 'text'):
            logger.info(f"Title applied successfully to time plot: '{fig.layout.title.text}'")
        else:
            logger.warning("Title not found in time plot layout after update")
    
    fig.update_layout(
        width=width,
        height=height,
        xaxis_title="Time",
        yaxis_title=extract_metric_name(value_col)
    )
    
    return fig


def _create_overlay_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> go.Figure:
    """Create timecourse plot with multiple metrics overlaid."""
    # Extract internal-only option so it isn't passed to Plotly
    user_group_labels = kwargs.pop('user_group_labels', None)
    fig = go.Figure()
    
    # Apply aggregation if requested
    if aggregation == "mean_sem" and group_col:
        # For timecourse plots, we need to aggregate by both group and time for ALL value columns
        agg_data = []
        for value_col in value_cols:
            # Aggregate each value column separately
            col_agg = df.groupby([group_col, time_col])[value_col].agg(['mean', 'std', 'count']).reset_index()
            col_agg['sem'] = col_agg['std'] / np.sqrt(col_agg['count'])
            col_agg['value_col'] = value_col  # Track which column this data came from
            agg_data.append(col_agg)
        
        # Combine all aggregated data
        plot_df = pd.concat(agg_data, ignore_index=True)
        y_col = 'mean'
        error_y = 'sem'
    else:
        plot_df = df
        y_col = None
        error_y = None
    
    # Add traces for each metric
    for value_col in value_cols:
        if plot_type == "line":
            if group_col and group_col in plot_df.columns:
                # Get data for this specific value column
                if 'value_col' in plot_df.columns:
                    # Using aggregated data
                    col_data = plot_df[plot_df['value_col'] == value_col]
                else:
                    # Using raw data
                    col_data = plot_df
                
                for group in col_data[group_col].unique():
                    group_data = col_data[col_data[group_col] == group]
                    
                    # Add error bars if available
                    error_y_data = None
                    if error_y and error_y in group_data.columns:
                        error_y_data = dict(
                            type='data',
                            array=group_data[error_y],
                            visible=True
                        )
                    
                    # Use shortname for better legend display
                    shortname = create_population_shortname(value_col)
                    trace_name = f"{shortname} - {group}"
                    
                    fig.add_trace(go.Scatter(
                        x=group_data[time_col],
                        y=group_data[y_col] if y_col else group_data[value_col],
                        name=trace_name,
                        mode='lines+markers',
                        line=dict(width=2),
                        marker=dict(size=6),
                        error_y=error_y_data
                    ))
            else:
                # No group column, plot all data for this metric
                if 'value_col' in plot_df.columns:
                    # Using aggregated data
                    col_data = plot_df[plot_df['value_col'] == value_col]
                else:
                    # Using raw data
                    col_data = plot_df
                
                # Add error bars if available
                error_y_data = None
                if error_y and error_y in col_data.columns:
                    error_y_data = dict(
                        type='data',
                        array=col_data[error_y],
                        visible=True
                    )
                
                # Use shortname for better legend display
                shortname = create_population_shortname(value_col)
                
                fig.add_trace(go.Scatter(
                    x=col_data[time_col],
                    y=col_data[y_col] if y_col else col_data[value_col],
                    name=shortname,
                    mode='lines+markers',
                    line=dict(width=2),
                    marker=dict(size=6),
                    error_y=error_y_data
                ))
    
    # Apply legend configuration
    width = kwargs.get('width', 1200)
    height = kwargs.get('height', 500)
    
    # Determine appropriate legend title based on plot type
    if group_col:
        legend_title = "Groups"
    else:
        legend_title = "Metrics"
    
    fig = configure_legend(
        fig, df, group_col, is_subplot=False, width=width, height=height,
        legend_title=legend_title, show_mean_sem_label=True
    )
    
    # Update title and labels
    if 'title' not in kwargs:
        logger.debug(f"Overlay timecourse - Creating title for multiple metrics")
        title = create_timecourse_plot_title(df, "Multiple Metrics", value_cols, filter_options=filter_options)
        logger.debug(f"Overlay timecourse - Title created: {title}")
        fig.update_layout(
            title=title,
            margin=dict(t=80)  # Add more top margin for title spacing
        )
        
        # Debug: Verify the title was applied
        if hasattr(fig.layout, 'title') and hasattr(fig.layout.title, 'text'):
            logger.info(f"Title applied successfully to overlay timecourse: '{fig.layout.title.text}'")
        else:
            logger.warning("Title not found in overlay timecourse layout after update")
    
    fig.update_layout(
        width=width,
        height=height,
        xaxis_title="Time",
        yaxis_title="Value"
    )

    # If grouping is present, ensure tick labels use custom labels where available
    if group_col and group_col in df.columns:
        unique_groups = df[group_col].unique()
        try:
            numeric_groups = sorted([float(g) if isinstance(g, str) else g for g in unique_groups])
            tickvals = [int(g) if hasattr(g, 'is_integer') and g.is_integer() else g for g in numeric_groups]
        except Exception:
            tickvals = sorted(unique_groups)
        label_map = get_group_label_map(df, user_group_labels)
        ticktext = [label_map.get(g, g) for g in tickvals]
        # Only update if time axis is x and groups are used as color (legend)
        # For timecourse, groups are legend items; we don't set x-axis ticks to group names.
        # However, for completeness, when a grouped categorical axis exists in variants, we keep this logic.
    
    return fig


def _create_faceted_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    facet_by: str,
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> go.Figure:
    """Create faceted timecourse plot."""
    if facet_by == "Cell Type":
        return _create_cell_type_faceted_timecourse(
            df, time_col, value_cols, group_col, plot_type, 
            aggregation, filter_options, **kwargs
        )
    else:
        return _create_group_faceted_timecourse(
            df, time_col, value_cols, group_col, facet_by, plot_type, 
            aggregation, filter_options, **kwargs
        )


def _create_cell_type_faceted_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> go.Figure:
    """Create timecourse plot faceted by cell type."""
    from .faceted_plots import create_cell_type_faceted_plot
    
    # Create faceted plot using existing infrastructure with aggregation
    fig = create_cell_type_faceted_plot(
        df, time_col, value_cols, filter_options=filter_options, 
        aggregation=aggregation, group_col=group_col, **kwargs
    )
    
    # Update layout for timecourse specifics
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Value"
    )
    
    return fig


def _create_group_faceted_timecourse(
    df: DataFrame,
    time_col: str,
    value_cols: List[str],
    group_col: Optional[str],
    facet_by: str,
    plot_type: str,
    aggregation: str,
    filter_options: Optional[Dict],
    **kwargs
) -> go.Figure:
    """Create timecourse plot faceted by group/tissue."""
    from .faceted_plots import create_group_faceted_plot
    
    # Create faceted plot using existing infrastructure with aggregation
    fig = create_group_faceted_plot(
        df, time_col, value_cols, facet_by, filter_options=filter_options,
        aggregation=aggregation, group_col=group_col, **kwargs
    )
    
    # Update layout for timecourse specifics
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Value"
    )
    
    return fig


def _save_visualization(fig: go.Figure, save_path: str) -> None:
    """Save visualization to HTML file."""
    from .plotly_renderer import PlotlyRenderer
    
    renderer = PlotlyRenderer()
    renderer.export_to_html_optimized(fig, save_path, 'minimal')
    logger.info(f"Saved timecourse visualization to {save_path}")


# Export the main function
__all__ = [
    'create_timecourse_visualization'
] 