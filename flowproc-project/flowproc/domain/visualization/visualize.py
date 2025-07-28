"""
Flow cytometry data visualization module with high-performance vectorized aggregation.

This module provides functionality to create interactive visualizations from
flow cytometry CSV data using Plotly, with support for both standard bar plots
and time-course line plots.
"""
from __future__ import annotations

import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Union, Tuple, Protocol, TypeAlias
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from flowproc.logging_config import setup_logging
from flowproc.config import USER_GROUP_LABELS
from flowproc.domain.parsing import load_and_parse_df, extract_tissue
from flowproc.domain.processing.transform import map_replicates
from flowproc.domain.visualization.plotting import apply_plot_style, PLOT_STYLE
from flowproc.domain.visualization.themes import VisualizationThemes
from flowproc.domain.processing.vectorized_aggregator import VectorizedAggregator, AggregationConfig
from flowproc.core.constants import KEYWORDS, METRIC_KEYWORDS

logger = logging.getLogger(__name__)

# Type aliases for clarity
PathLike: TypeAlias = Union[str, Path]
DataFrame: TypeAlias = pd.DataFrame
Figure: TypeAlias = go.Figure


from ...core.exceptions import VisualizationError, DataError as DataProcessingError, ProcessingError


@dataclass(frozen=True)
class VisualizationConfig:
    """Configuration for visualization generation."""
    metric: Optional[str]
    width: int = 600  # Wide width for better timecourse aspect ratio
    height: Optional[int] = 300  # Short height for better timecourse visualization, None for dynamic
    theme: str = "default"  # Changed from "dark" to "default"
    time_course_mode: bool = False
    user_replicates: Optional[List[int]] = None
    auto_parse_groups: bool = True
    user_group_labels: Optional[List[str]] = None
    tissue_filter: Optional[str] = None
    subpopulation_filter: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.width <= 0:
            raise ValueError("Width must be a positive integer")
        if self.height is not None and self.height <= 0:
            raise ValueError("Height must be a positive integer or None for dynamic sizing")
        if self.metric and self.metric not in KEYWORDS:
            raise ValueError(f"Invalid metric '{self.metric}'. Valid options: {', '.join(KEYWORDS.keys())}")


@dataclass(frozen=True)
class ProcessedData:
    """Container for processed visualization data."""
    dataframes: List[DataFrame]
    metrics: List[str]
    groups: List[int]
    times: List[Optional[float]]
    tissues_detected: bool
    group_map: Dict[int, str]
    replicate_count: int


class DataProcessor:
    """Handles data processing for visualization using vectorized operations."""
    
    def __init__(self, df: DataFrame, sid_col: str, config: VisualizationConfig):
        self.df = df
        self.sid_col = sid_col
        self.config = config
        self.aggregator = VectorizedAggregator(df, sid_col)
        
    def process(self) -> ProcessedData:
        """
        Process DataFrame for plotting using vectorized operations.
        
        Returns:
            ProcessedData container with aggregated results
            
        Raises:
            DataProcessingError: If processing fails
        """
        if self.df.empty:
            raise DataProcessingError("DataFrame is empty")
        
        # Map replicates
        df_mapped, replicate_count = self._map_replicates()
        if replicate_count == 0:
            raise DataProcessingError("No replicates found")
        
        # Apply tissue filtering if specified
        if self.config.tissue_filter and 'Tissue' in df_mapped.columns:
            original_count = len(df_mapped)
            df_mapped = df_mapped[df_mapped['Tissue'] == self.config.tissue_filter]
            filtered_count = len(df_mapped)
            logger.info(f"Applied tissue filter '{self.config.tissue_filter}': {original_count} -> {filtered_count} rows")
            
            if df_mapped.empty:
                raise DataProcessingError(f"No data found for tissue '{self.config.tissue_filter}'")
        
        # Apply subpopulation filtering if specified (for time-course mode)
        if self.config.subpopulation_filter and self.config.time_course_mode:
            # Note: Subpopulation filtering will be applied after aggregation
            # since subpopulations are created during the aggregation process
            logger.info(f"Subpopulation filter '{self.config.subpopulation_filter}' will be applied during visualization")
        
        # Update aggregator with mapped data
        self.aggregator.df = df_mapped
        
        # Get configuration
        groups, times, tissues_detected, group_map = self._extract_metadata(df_mapped)
        
        # Create aggregation config
        agg_config = AggregationConfig(
            groups=groups,
            times=times,
            tissues_detected=tissues_detected,
            group_map=group_map,
            sid_col=self.sid_col,
            time_course_mode=self.config.time_course_mode
        )
        
        # Determine metrics to process
        metrics = self._get_metrics_to_process()
        
        # Aggregate data using vectorized operations
        aggregated_lists = self._aggregate_metrics(metrics, agg_config)
        
        return ProcessedData(
            dataframes=aggregated_lists,
            metrics=metrics,
            groups=groups,
            times=times,
            tissues_detected=tissues_detected,
            group_map=group_map,
            replicate_count=replicate_count
        )
    
    def _map_replicates(self) -> Tuple[DataFrame, int]:
        """Map replicates using the transform module."""
        try:
            df_mapped, replicate_count = map_replicates(
                self.df, 
                auto_parse=self.config.auto_parse_groups,
                user_replicates=self.config.user_replicates,
                user_groups=None  # Let the function auto-detect groups
            )
            return df_mapped, replicate_count
        except Exception as e:
            raise DataProcessingError(f"Failed to map replicates: {str(e)}") from e
    
    def _extract_metadata(self, df: DataFrame) -> Tuple[List[int], List[Optional[float]], bool, Dict[int, str]]:
        """Extract metadata from processed DataFrame."""
        try:
            # Extract groups - convert to int for AggregationConfig
            groups = sorted([int(g) for g in df['Group'].unique().tolist()])
            
            # Extract times - convert to float for AggregationConfig
            times = []
            if 'Time' in df.columns:
                times = sorted([float(t) if pd.notna(t) else None for t in df['Time'].unique().tolist()])
            else:
                times = [None]
            
            # Check for tissues - if tissue filter is applied, only one tissue should remain
            tissues_detected = 'Tissue' in df.columns and df['Tissue'].nunique() > 1 and not self.config.tissue_filter
            
            # Create group map - use user_group_labels if provided, otherwise use default labels
            group_map = {}
            if 'Group' in df.columns:
                if self.config.user_group_labels and len(self.config.user_group_labels) >= len(groups):
                    # Use user-provided group labels
                    group_map = {groups[i]: self.config.user_group_labels[i] for i in range(len(groups))}
                else:
                    # Use default group labels
                    group_map = {int(g): f"Group {int(g)}" for g in df['Group'].unique()}
            
            return groups, times, tissues_detected, group_map
            
        except Exception as e:
            raise DataProcessingError(f"Failed to extract metadata: {str(e)}") from e
    
    def _get_metrics_to_process(self) -> List[str]:
        """Determine which metrics to process."""
        if self.config.metric:
            if self.config.metric not in KEYWORDS:
                raise DataProcessingError(f"Invalid metric: {self.config.metric}")
            return [self.config.metric]
        else:
            # Process all available metrics
            available_metrics = []
            for col in self.df.columns:
                if col in KEYWORDS:
                    available_metrics.append(col)
            return available_metrics
    
    def _aggregate_metrics(self, metrics: List[str], agg_config: AggregationConfig) -> List[DataFrame]:
        """Aggregate metrics using vectorized operations."""
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
                    agg_dfs = self.aggregator.aggregate_metric(metric, raw_cols, agg_config)
                    if agg_dfs:
                        aggregated_lists.extend(agg_dfs)
            
            return aggregated_lists
            
        except Exception as e:
            raise DataProcessingError(f"Failed to aggregate metrics: {str(e)}") from e


class Visualizer:
    """Creates interactive visualizations from processed data."""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        self.themes = VisualizationThemes()
        
    def create_figure(self, processed_data: ProcessedData) -> Figure:
        """
        Create visualization figure from processed data.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            Plotly Figure object
        """
        if not processed_data.dataframes:
            return self._create_empty_figure()
        
        if self.config.time_course_mode and self._has_time_data(processed_data):
            return self._create_time_course_figure(processed_data)
        else:
            return self._create_bar_plot_figure(processed_data)
    
    def _has_time_data(self, processed_data: ProcessedData) -> bool:
        """Check if data has valid time information."""
        return (
            len(processed_data.times) > 1 or 
            (len(processed_data.times) == 1 and processed_data.times[0] is not None)
        )
    
    def _create_empty_figure(self) -> Figure:
        """Create figure for empty data."""
        fig = go.Figure()
        fig.add_annotation(
            text="No data to visualize",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        # Apply custom theme instead of using apply_plot_style
        self.themes.apply_theme(fig, self.config.theme)
        # Use default height if config height is None
        height_to_use = self.config.height if self.config.height is not None else 300
        fig.update_layout(width=self.config.width, height=height_to_use)
        return fig
    
    def _create_time_course_figure(self, processed_data: ProcessedData) -> Figure:
        """Create time-course visualization with subplots."""
        # Combine all dataframes
        all_data = self._combine_dataframes(processed_data)
        
        # Apply subpopulation filtering if specified
        if self.config.subpopulation_filter and 'Subpopulation' in all_data.columns:
            original_count = len(all_data)
            available_subpops = sorted(all_data['Subpopulation'].unique())
            logger.debug(f"Available subpopulations in data: {available_subpops}")
            logger.debug(f"Looking for subpopulation: '{self.config.subpopulation_filter}'")
            all_data = all_data[all_data['Subpopulation'] == self.config.subpopulation_filter]
            filtered_count = len(all_data)
            logger.info(f"Applied subpopulation filter '{self.config.subpopulation_filter}': {original_count} -> {filtered_count} rows")
            
            if all_data.empty:
                raise DataProcessingError(f"No data found for subpopulation '{self.config.subpopulation_filter}'")
        
        # Get unique dimensions from the filtered data
        unique_subpops = sorted(all_data['Subpopulation'].unique())
        # Filter out UNK tissues from the list
        unique_tissues = sorted([t for t in all_data['Tissue'].unique() if t != 'UNK'])
        
        # Ensure we have at least one row for subplots
        if not unique_tissues:
            # If no valid tissues, use subpopulations only
            num_rows = len(unique_subpops)
            unique_tissues = ['']  # Empty string for tissue display
        else:
            num_rows = len(unique_subpops) * len(unique_tissues)
        
        # Create subplots with dynamic spacing based on number of subplots
        # Plotly constraint: vertical_spacing <= 1 / (rows - 1)
        if num_rows > 1:
            max_allowed_spacing = 1 / (num_rows - 1)
            if num_rows <= 4:
                # For fewer graphs, use more generous spacing to prevent title overlap
                vertical_spacing = min(0.08, max_allowed_spacing * 0.8)  # Use 80% of max allowed, capped at 0.08
            else:
                # Use tighter spacing for better visual density while respecting constraints
                vertical_spacing = min(0.03, max_allowed_spacing * 0.4)  # Use 40% of max allowed, capped at 0.03
        else:
            vertical_spacing = 0.02
        
        fig = make_subplots(
            rows=num_rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=vertical_spacing,
            subplot_titles=self._generate_subplot_titles(unique_tissues, unique_subpops),
            # Ensure proper sizing for timecourse visualization
            specs=[[{"secondary_y": False}] for _ in range(num_rows)]
        )
        
        # Add traces
        self._add_time_course_traces(fig, all_data, unique_tissues, unique_subpops)
        
        # Update layout with optimized height calculation for better proportions
        # Use more reasonable heights for better visual balance
        min_height_per_subplot = 250  # Reduced from 400 for better proportions
        
        # Adjust title height and spacing based on number of subplots
        if num_rows <= 4:
            # For fewer graphs, use more space for titles to prevent overlap
            title_height = 80  # Increased from 60 for better title spacing
            spacing_height = 30 * num_rows  # Increased spacing for fewer graphs
        else:
            # For more graphs, use tighter spacing for better visual density
            title_height = 60  # Reduced from 80 for tighter layout
            spacing_height = 20 * num_rows  # Reduced from 50 to 20 for less spacing between subplots
        
        calculated_height = min_height_per_subplot * num_rows + title_height + spacing_height
        # Use calculated height if config height is None, otherwise use the maximum
        updated_height = calculated_height if self.config.height is None else max(calculated_height, self.config.height)
        title = self.config.metric if self.config.metric else 'Metrics Visualization'
        y_axis_title = self.config.metric if self.config.metric else 'Metrics'
        fig.update_layout(
            title=title,
            xaxis_title='Time',
            yaxis_title=y_axis_title,
            height=updated_height,
            width=self.config.width  # Set width here to ensure it's applied before theme
        )
        
        # Update x-axes and y-axes for all subplots with better spacing
        for row in range(1, num_rows + 1):
            fig.update_xaxes(
                title_text='Time',
                title_standoff=10,
                showticklabels=True,
                autorange=True,
                tickmode='auto',
                nticks=8,  # Limit number of ticks for cleaner appearance
                row=row, col=1
            )
            # Update y-axis title for each subplot with better label spacing
            fig.update_yaxes(
                title_text=self.config.metric if self.config.metric else 'Metrics',
                title_standoff=15,  # Increased from 10 to 15
                showticklabels=True,
                autorange=True,
                tickmode='auto',
                nticks=4,  # Reduced from 6 to 4 to prevent label overlap
                tickangle=0,  # Ensure labels are horizontal
                row=row, col=1
            )
        
        # Apply custom theme AFTER all axis updates to ensure theme is not overridden
        self.themes.apply_theme(fig, self.config.theme)
        
        # Ensure proper subplot sizing for timecourse visualization
        # This fixes the issue where width was not applying to plots when multiple graphs are displayed
        # The width is set both before and after theme application to ensure it's not overridden
        
        # Calculate dynamic margins based on number of subplots
        # When there are fewer subplots, we need more space for titles
        if num_rows <= 4:
            # For 4 or fewer graphs, use more generous margins to prevent title overlap
            dynamic_margin = dict(l=60, r=50, t=90, b=60)  # Increased top and bottom margins
        else:
            # For more graphs, use tighter spacing for better visual density
            dynamic_margin = dict(l=60, r=50, t=70, b=50)
        
        fig.update_layout(
            width=self.config.width,  # Re-apply width after theme to ensure it's not overridden
            # Dynamic margins based on number of subplots
            margin=dynamic_margin
        )
        
        return fig
    
    def _create_bar_plot_figure(self, processed_data: ProcessedData) -> Figure:
        """Create bar plot visualization."""
        # Combine all dataframes
        all_data = self._combine_dataframes(processed_data)
        
        # Check if we should use facet_col for tissue
        use_facet_col = False
        if processed_data.tissues_detected and 'Tissue' in all_data.columns:
            unique_tissues = all_data['Tissue'].nunique()
            use_facet_col = unique_tissues > 1
        
        # Create bar plot with manual positioning to control spacing
        title = self.config.metric if self.config.metric else 'Metrics Visualization'
        
        # Create figure manually to control bar positioning
        fig = go.Figure()
        
        # Extract integer labels from Group_Label for display
        def extract_group_number(label):
            """Extract the integer part from group labels like 'Group 1' -> '1'"""
            if pd.isna(label):
                return label
            label_str = str(label)
            # Try to extract number from "Group X" format
            import re
            if 'Group' in label_str:
                match = re.search(r'Group\s*(\d+)', label_str, re.IGNORECASE)
                if match:
                    return match.group(1)
            # If no "Group" prefix, try to extract any number
            numbers = re.findall(r'\d+', label_str)
            if numbers:
                return numbers[0]
            # Fallback to original label
            return label_str
        
        # Get unique groups and subpopulations
        all_groups = all_data['Group_Label'].unique()
        unique_subpops = sorted(all_data['Subpopulation'].unique()) if 'Subpopulation' in all_data.columns else ['Default']
        
        # Create a list of tuples (original_group, extracted_number) for sorting
        group_number_pairs = []
        for group in all_groups:
            group_number = extract_group_number(group)
            try:
                # Try to convert to int for numerical sorting
                sort_key = int(group_number)
            except (ValueError, TypeError):
                # If not a number, use a large number to put it at the end
                sort_key = 999999
            group_number_pairs.append((group, group_number, sort_key))
        
        # Sort by the numerical key
        group_number_pairs.sort(key=lambda x: x[2])
        
        # Extract the sorted groups and their display numbers
        unique_groups = [pair[0] for pair in group_number_pairs]
        unique_group_numbers = [pair[1] for pair in group_number_pairs]
        
        # Calculate bar positions
        group_positions = list(range(len(unique_groups)))
        bar_width = 0.15  # Fixed bar width
        subpop_spacing = 0.25  # 25% spacing between bars within groups
        
        # Add bars for each subpopulation
        for i, subpop in enumerate(unique_subpops):
            subpop_data = all_data[all_data['Subpopulation'] == subpop] if 'Subpopulation' in all_data.columns else all_data
            
            # Calculate x positions for this subpopulation
            x_positions = []
            for group in unique_groups:
                group_data = subpop_data[subpop_data['Group_Label'] == group]
                if not group_data.empty:
                    # Position bars within each group with spacing
                    group_idx = unique_groups.index(group)
                    # Offset each subpopulation within the group
                    x_pos = group_idx + (i - len(unique_subpops)/2) * (bar_width + subpop_spacing * bar_width)
                    x_positions.append(x_pos)
                else:
                    x_positions.append(None)
            
            # Filter out None values
            valid_data = [(x, y, std) for x, y, std in zip(x_positions, subpop_data['Mean'], subpop_data['Std']) if x is not None]
            if valid_data:
                x_vals, y_vals, std_vals = zip(*valid_data)
                
                fig.add_trace(go.Bar(
                    x=x_vals,
                    y=y_vals,
                    error_y=dict(type='data', array=std_vals, visible=True, thickness=0.5, width=0.75),  # Endcaps 50% wider than main line
                    name=subpop,
                    width=bar_width,
                    marker_line_width=0.5,
                    marker_line_color='black'
                ))
        
        # Set x-axis labels using integer group numbers
        fig.update_xaxes(
            ticktext=unique_group_numbers,
            tickvals=list(range(len(unique_groups))),
            title='Group'
        )
        
        # Set title and other properties
        fig.update_layout(
            title=title,
            yaxis_title=self.config.metric if self.config.metric else 'Value',  # Use metric name as y-axis title
            barmode='overlay'
        )
        
        # Calculate optimal layout based on label lengths (use integer labels for calculation)
        labels = unique_group_numbers
        legend_items = len(all_data['Subpopulation'].unique()) if 'Subpopulation' in all_data.columns else 0
        legend_labels = all_data['Subpopulation'].unique().tolist() if 'Subpopulation' in all_data.columns else []
        
        # Import the layout calculation function
        from .plotting import calculate_layout_for_long_labels
        # Use default height if config height is None
        height_for_calculation = self.config.height if self.config.height is not None else 300
        layout_adjustments = calculate_layout_for_long_labels(labels, legend_items, "Metrics Visualization", legend_labels, self.config.width, height_for_calculation)
        
        # Apply styling with dynamic width and height
        dynamic_width = layout_adjustments.get("width", self.config.width)
        dynamic_height = layout_adjustments.get("height", height_for_calculation)
        
        # Apply custom theme first
        self.themes.apply_theme(fig, self.config.theme)
        
        # Apply our custom styling after theme to override theme defaults
        fig.update_layout(
            xaxis_title='Group',
            yaxis_title=self.config.metric if self.config.metric else 'Value',  # Use metric name as y-axis title
            width=dynamic_width,
            height=dynamic_height
        )
        
        # Apply user-required styling (overrides theme)
        fig.update_xaxes(title_font=dict(size=12, color='black'))
        fig.update_yaxes(title_font=dict(size=12, color='black'))
        
        # Apply title styling (user requirement: 14pt bold, centered)
        current_title = fig.layout.title.text if hasattr(fig.layout, 'title') and fig.layout.title else ""
        fig.update_layout(
            title=dict(
                text=current_title,
                font=dict(size=14, color='black'),
                x=0.5,  # Center the title
                xanchor='center'
            )
        )
        
        # Apply dynamic layout adjustments
        if layout_adjustments:
            fig.update_layout(
                margin=layout_adjustments["margin"],
                legend=layout_adjustments["legend"]
            )
            fig.update_xaxes(
                title_standoff=layout_adjustments["xaxis_title_standoff"],
                tickangle=layout_adjustments["xaxis_tickangle"]
            )
        else:
            # Fallback to improved default settings with right-side legend
            fig.update_layout(
                legend=dict(
                    font_size=11,  # User requirement: label font should be 11pt
                    orientation="v",
                    yanchor="middle",
                    xanchor="left",
                    x=1.01,  # Slightly closer to graph
                    y=0.5,
                    borderwidth=0,
                    itemwidth=30,
                    itemsizing="constant",
                    tracegroupgap=6,  # Reduced spacing
                    entrywidth=30,
                    entrywidthmode="pixels",
                    itemclick="toggle",
                    itemdoubleclick="toggleothers"
                ),
                margin=dict(b=50, r=30),  # Slightly more right margin
            )
            fig.update_xaxes(title_standoff=15)
        
        # Update legend to match bar border styling
        fig.update_layout(
            legend=dict(
                bordercolor='black',
                borderwidth=0.5,  # Match the bar border width
                bgcolor='rgba(255,255,255,0.8)',  # Semi-transparent white background
            )
        )
        
        return fig
    
    def _combine_dataframes(self, processed_data: ProcessedData) -> DataFrame:
        """Combine all processed dataframes into one."""
        if not processed_data.dataframes:
            return pd.DataFrame()
        
        combined = pd.concat(processed_data.dataframes, ignore_index=True)
        return combined
    
    def _generate_subplot_titles(self, tissues: List[str], subpops: List[str]) -> List[str]:
        """Generate titles for subplots."""
        titles = []
        for tissue in tissues:
            for subpop in subpops:
                # Don't include UNK tissue or empty tissue strings in subplot titles
                tissue_display = tissue if tissue != 'UNK' and tissue != '' else ''
                if tissue_display and subpop:
                    titles.append(f"{tissue_display} - {subpop}")
                elif tissue_display:
                    titles.append(tissue_display)
                elif subpop:
                    titles.append(subpop)
                else:
                    titles.append("")
        return titles
    
    def _add_time_course_traces(self, fig: Figure, all_data: DataFrame, 
                               tissues: List[str], subpops: List[str]) -> None:
        """Add traces to time-course subplots."""
        # Get all unique groups across all data to create consistent color mapping
        all_unique_groups = sorted(all_data['Group_Label'].unique())
        
        # Create color mapping for consistent colors across all subplots
        color_sequence = px.colors.qualitative.Dark24
        group_color_map = {group: color_sequence[i % len(color_sequence)] for i, group in enumerate(all_unique_groups)}
        
        # Determine if we're in single-tissue mode (when tissues is [''] or only has one tissue)
        single_tissue_mode = len(tissues) == 1 and (tissues[0] == '' or len(tissues) == 1)
        
        for i, tissue in enumerate(tissues):
            for j, subpop in enumerate(subpops):
                if single_tissue_mode:
                    # When we have only subpopulations (no valid tissues), use simple row numbering
                    row = j + 1
                else:
                    # Original logic for multiple tissues
                    row = i * len(subpops) + j + 1
                
                # Filter data for this subplot
                if tissue == '':
                    # If tissue is empty string, include all tissues (including UNK)
                    mask = (all_data['Subpopulation'] == subpop)
                else:
                    mask = (all_data['Tissue'] == tissue) & (all_data['Subpopulation'] == subpop)
                subplot_data = all_data[mask]
                
                if not subplot_data.empty:
                    # Get unique groups for this subplot
                    unique_groups = sorted(subplot_data['Group_Label'].unique())
                    
                    # Create a trace for each group
                    for group in unique_groups:
                        group_data = subplot_data[subplot_data['Group_Label'] == group].sort_values('Time')
                        
                        if not group_data.empty:
                            # Add line trace for this group with consistent color
                            # Don't include UNK tissue in the name
                            tissue_display = tissue if tissue != 'UNK' else ''
                            name = f"{group} ({tissue_display} - {subpop})" if tissue_display else f"{group} ({subpop})"
                            fig.add_trace(
                                go.Scatter(
                                    x=group_data['Time'],
                                    y=group_data['Mean'],
                                    mode='lines+markers',
                                    name=name,
                                    error_y=dict(
                                        type='data',
                                        array=group_data['Std'],
                                        visible=True,
                                        thickness=0.3,
                                        width=0.5  # Reduced width to prevent overlap
                                    ),
                                    showlegend=(row == 1),  # Only show legend for first row
                                    legendgroup=group,
                                    line=dict(color=group_color_map[group])  # Assign consistent color
                                ),
                                row=row, col=1
                            )


def visualize_data(
    csv_path: PathLike,
    output_html: PathLike,
    metric: Optional[str] = None,
    width: int = 600,  # Wide width for better timecourse aspect ratio
    height: Optional[int] = 300,  # Short height for better timecourse visualization, None for dynamic
    theme: str = "default",  # Changed from "dark" to "default"
    time_course_mode: bool = False,
    user_replicates: Optional[List[int]] = None,
    auto_parse_groups: bool = True,
    user_group_labels: Optional[List[str]] = None,
    tissue_filter: Optional[str] = None,
    subpopulation_filter: Optional[str] = None
) -> Figure:
    """
    Generate interactive plots using vectorized data processing.
    
    This is the main entry point for visualization. It loads CSV data,
    processes it using vectorized operations, and generates interactive
    Plotly visualizations.
    
    Args:
        csv_path: Path to input CSV file
        output_html: Path for output HTML file
        metric: Specific metric to visualize (None for all)
        width: Plot width in pixels
        height: Plot height in pixels
        theme: Custom theme name (default, scientific, dark, minimal, colorful, publication)
        time_course_mode: Whether to use time-course visualization
        user_replicates: User-defined replicates
        auto_parse_groups: Whether to auto-parse groups
        user_group_labels: User-defined group labels
        
    Returns:
        Plotly Figure object
        
    Raises:
        VisualizationError: If visualization fails
        FileNotFoundError: If input file doesn't exist
        ValueError: If parameters are invalid
    """
    # Initialize logging
    setup_logging(filemode='a')
    logger.debug(f"Starting visualization for {csv_path}, metric={metric}")
    
    try:
        # Validate and convert paths
        csv_path = Path(csv_path)
        output_html = Path(output_html)
        
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file does not exist: {csv_path}")
        
        # Ensure output directory exists
        output_html.parent.mkdir(parents=True, exist_ok=True)
        
        # Create configuration
        config = VisualizationConfig(
            metric=metric,
            width=width,
            height=height,
            theme=theme,
            time_course_mode=time_course_mode,
            user_replicates=user_replicates,
            auto_parse_groups=auto_parse_groups,
            user_group_labels=user_group_labels,
            tissue_filter=tissue_filter,
            subpopulation_filter=subpopulation_filter
        )
        
        # Load and process data
        df, sid_col = load_and_parse_df(csv_path)
        
        # Check for time data if time course mode requested
        if config.time_course_mode:
            has_time = "Time" in df.columns and df["Time"].notna().any()
            logger.debug(f"Timecourse mode requested. Time column exists: {'Time' in df.columns}")
            logger.debug(f"Time column has non-null values: {has_time}")
            if "Time" in df.columns:
                time_values = df["Time"].dropna().unique()
                logger.debug(f"Unique time values found: {time_values}")
            if not has_time:
                logger.warning("No time data available, falling back to standard mode")
                config = VisualizationConfig(
                    **{**config.__dict__, 'time_course_mode': False}
                )
        
        # Process data
        processor = DataProcessor(df, sid_col, config)
        processed_data = processor.process()
        
        # Create visualization
        visualizer = Visualizer(config)
        fig = visualizer.create_figure(processed_data)
        
        # Save HTML with embedded Plotly for offline viewing
        # Use embedded Plotly.js instead of CDN for packaged apps
        fig.write_html(
            str(output_html), 
            include_plotlyjs=True,  # Changed from 'cdn' to True for offline compatibility
            full_html=True,
            config=dict(
                editable=True,
                edits=dict(
                    axisTitleText=True,  # Editable axis labels
                    titleText=True,      # Editable chart title
                    legendText=True      # Editable legend items
                )
            )
        )
        
        # Log success
        if output_html.exists():
            size = output_html.stat().st_size
            md5 = hashlib.md5(output_html.read_bytes()).hexdigest()
            logger.info(f"Saved '{output_html}' ({size} bytes, md5: {md5})")
        
        return fig
        
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Input error: {str(e)}")
        raise
    except DataProcessingError as e:
        logger.error(f"Data processing failed: {str(e)}")
        raise VisualizationError(f"Failed to process data: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise VisualizationError(f"Visualization failed: {str(e)}") from e


def main() -> None:
    """Command-line interface for visualization."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate interactive visualizations from flow cytometry CSV data"
    )
    parser.add_argument("--csv", required=True, help="Input CSV path")
    parser.add_argument("--output-html", required=True, help="Output HTML path")
    parser.add_argument("--metric", default=None, help="Specific metric to visualize")
    parser.add_argument("--width", type=int, default=600, help="Plot width in pixels")
    parser.add_argument("--height", type=int, default=300, help="Plot height in pixels")
    parser.add_argument("--theme", default="default", help="Custom theme name")
    parser.add_argument("--time-course", action="store_true", help="Enable time-course mode")
    
    args = parser.parse_args()
    
    try:
        visualize_data(
            csv_path=args.csv,
            output_html=args.output_html,
            metric=args.metric,
            width=args.width,
            height=args.height,
            theme=args.theme,
            time_course_mode=args.time_course
        )
        print(f"Visualization saved to: {args.output_html}")
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()