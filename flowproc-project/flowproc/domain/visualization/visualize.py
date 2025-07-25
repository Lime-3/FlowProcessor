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
    width: int = 800
    height: int = 600
    theme: str = "plotly_dark"
    time_course_mode: bool = False
    user_replicates: Optional[List[int]] = None
    auto_parse_groups: bool = True
    user_group_labels: Optional[List[str]] = None
    
    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Width and height must be positive integers")
        if self.metric and self.metric not in KEYWORDS:
            raise ValueError(f"Invalid metric '{self.metric}'. Valid options: {', '.join(KEYWORDS.keys())}")


@dataclass
class ProcessedData:
    """Container for processed visualization data."""
    dataframes: List[List[DataFrame]]
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
        """Map replicates with error handling."""
        try:
            user_groups = None
            if not self.config.auto_parse_groups:
                user_groups = sorted(self.df["Group"].dropna().unique().astype(int))
            
            return map_replicates(
                self.df,
                auto_parse=self.config.auto_parse_groups,
                user_replicates=self.config.user_replicates,
                user_groups=user_groups
            )
        except (ValueError, KeyError, TypeError) as e:
            raise DataProcessingError(f"Failed to map replicates: {str(e)}") from e
    
    def _extract_metadata(self, df: DataFrame) -> Tuple[List[int], List[Optional[float]], bool, Dict[int, str]]:
        """Extract metadata from processed DataFrame."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected DataFrame, got {type(df)}")
        groups = sorted(df["Group"].dropna().unique().astype(int))
        
        times: List[Optional[float]] = [None]
        if "Time" in df.columns and df["Time"].notna().any():
            times = sorted(t for t in df["Time"].unique() if pd.notna(t))
        
        tissues_detected = df[self.sid_col].apply(extract_tissue).nunique() > 1
        group_map = self._create_group_map(tuple(groups))  # Convert list to tuple for lru_cache
        
        return groups, times, tissues_detected, group_map
    
    @lru_cache(maxsize=1)
    def _create_group_map(self, groups: Tuple[int, ...]) -> Dict[int, str]:
        """Create mapping from group numbers to labels."""
        groups_list = list(groups)
        
        # Check user-provided labels
        if self.config.user_group_labels and len(self.config.user_group_labels) >= len(groups_list):
            return {groups_list[i]: self.config.user_group_labels[i] for i in range(len(groups_list))}
        
        # Check global labels
        if USER_GROUP_LABELS and len(USER_GROUP_LABELS) >= len(groups_list):
            return {groups_list[i]: USER_GROUP_LABELS[i] for i in range(len(groups_list))}
        
        # Default labels
        return {g: f"Group {g}" for g in groups_list}
    
    def _get_metrics_to_process(self) -> List[str]:
        """Determine which metrics to process."""
        if self.config.metric:
            metrics = [m for m in KEYWORDS.keys() if m.lower() == self.config.metric.lower()]
            if not metrics:
                raise DataProcessingError(
                    f"Invalid metric '{self.config.metric}'. Valid options: {', '.join(KEYWORDS.keys())}"
                )
            return metrics
        return list(KEYWORDS.keys())
    
    def _aggregate_metrics(self, metrics: List[str], agg_config: AggregationConfig) -> List[List[DataFrame]]:
        """Aggregate metrics using vectorized operations."""
        aggregated_lists: List[List[DataFrame]] = []
        
        for metric_name in metrics:
            # Map metric name to key substring using KEYWORDS dictionary
            key_substring = KEYWORDS.get(metric_name, metric_name.lower())
            # Check if we have a specific mapping in METRIC_KEYWORDS
            for metric_type, keywords in METRIC_KEYWORDS.items():
                if metric_name.lower() in [kw.lower() for kw in keywords]:
                    key_substring = keywords[0]  # Use the first keyword as the substring
                    break
            
            # Find matching columns efficiently
            raw_cols = self._find_metric_columns(key_substring)
            
            if not raw_cols:
                logger.info(f"No data for metric '{metric_name}'")
                continue
            
            # Use vectorized aggregation
            agg_dfs = self.aggregator.aggregate_metric(metric_name, raw_cols, agg_config)
            
            if agg_dfs:
                aggregated_lists.append(agg_dfs)
        
        return aggregated_lists
    
    def _find_metric_columns(self, key_substring: str) -> List[str]:
        """Find columns matching the metric keyword."""
        excluded_cols = {self.sid_col, "Well", "Group", "Animal", "Time", "Replicate", "Tissue"}
        
        return [
            col for col in self.aggregator.df.columns
            if key_substring in col.lower()
            and col not in excluded_cols
            and not self.aggregator.df[col].isna().all()
        ]


class Visualizer:
    """Creates interactive visualizations from processed data."""
    
    def __init__(self, config: VisualizationConfig):
        self.config = config
        
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
        apply_plot_style(fig, "", "", self.config.theme, self.config.width, self.config.height)
        return fig
    
    def _create_time_course_figure(self, processed_data: ProcessedData) -> Figure:
        """Create time-course visualization with subplots."""
        # Combine all dataframes
        all_data = self._combine_dataframes(processed_data)
        
        # Get unique dimensions
        unique_subpops = sorted(all_data['Subpopulation'].unique())
        unique_tissues = sorted(all_data['Tissue'].unique())
        num_rows = len(unique_subpops) * len(unique_tissues)
        
        # Create subplots
        fig = make_subplots(
            rows=num_rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=self._generate_subplot_titles(unique_tissues, unique_subpops)
        )
        
        # Add traces
        self._add_time_course_traces(fig, all_data, unique_tissues, unique_subpops)
        
        # Update layout
        updated_height = self.config.height * num_rows
        apply_plot_style(
            fig, 'Time', 'Metrics', 
            self.config.theme, self.config.width, updated_height
        )
        
        # Update x-axes
        for row in range(1, num_rows + 1):
            fig.update_xaxes(
                title_text='Time',
                title_standoff=0,
                showticklabels=True,
                autorange=True,
                row=row, col=1
            )
        
        return fig
    
    def _create_bar_plot_figure(self, processed_data: ProcessedData) -> Figure:
        """Create bar plot visualization."""
        # Combine all dataframes
        all_data = self._combine_dataframes(processed_data)
        
        # Create bar plot
        fig = px.bar(
            all_data,
            x='Group_Label',
            y='Mean',
            error_y='Std',
            color='Subpopulation',
            facet_col='Tissue' if processed_data.tissues_detected else None,
            title='Metrics Visualization',
            barmode='group',
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        
        # Apply styling
        apply_plot_style(
            fig, 'Group', 'Value',
            self.config.theme, self.config.width, self.config.height
        )
        
        # Update layout for better appearance
        fig.update_layout(
            legend=dict(y=-0.2),
            margin=dict(b=80)
        )
        fig.update_xaxes(title_standoff=10)
        fig.update_traces(
            marker_line_width=0.5,
            marker_line_color='black',
            error_y=dict(thickness=0.75, width=5),
            width=0.2
        )
        
        return fig
    
    def _combine_dataframes(self, processed_data: ProcessedData) -> DataFrame:
        """Combine all processed dataframes."""
        all_dfs: List[DataFrame] = []
        
        for agg_list in processed_data.dataframes:
            for df in agg_list:
                if not isinstance(df, pd.DataFrame):
                    raise TypeError(f"Expected DataFrame, got {type(df)}")
            all_dfs.extend(agg_list)
        
        if not all_dfs:
            return pd.DataFrame()
        
        return pd.concat(all_dfs, ignore_index=True)
    
    def _generate_subplot_titles(self, tissues: List[str], subpops: List[str]) -> List[str]:
        """Generate subplot titles for time-course visualization."""
        titles: List[str] = []
        
        for tissue in tissues:
            for subpop in subpops:
                if tissue != 'Unknown_tissue':
                    titles.append(f"{subpop} ({tissue})")
                else:
                    titles.append(subpop)
        
        return titles
    
    def _add_time_course_traces(
        self, 
        fig: Figure, 
        data: DataFrame, 
        tissues: List[str], 
        subpops: List[str]
    ) -> None:
        """Add traces to time-course figure."""
        # Create color mapping
        color_map = self._create_color_map(data['Group_Label'].unique())
        
        row_idx = 1
        for tissue in tissues:
            for subpop in subpops:
                # Filter data
                mask = (data['Subpopulation'] == subpop) & (data['Tissue'] == tissue)
                sub_df = data[mask]
                
                # Add trace for each group
                for group in sorted(sub_df['Group_Label'].unique()):
                    group_df = sub_df[sub_df['Group_Label'] == group].sort_values('Time')
                    
                    if not group_df.empty:
                        self._add_single_trace(
                            fig, group_df, group, tissue, 
                            color_map[group], row_idx, show_legend=(row_idx == 1)
                        )
                
                row_idx += 1
    
    def _create_color_map(self, groups) -> Dict[str, str]:
        """Create consistent color mapping for groups."""
        # Handle both pandas Series and numpy arrays
        if hasattr(groups, 'unique'):
            unique_groups = sorted(groups.unique())
        else:
            # Handle numpy array or other iterable
            unique_groups = sorted(pd.Series(groups).unique())
        
        color_sequence = px.colors.qualitative.Dark24
        
        return {
            group: color_sequence[i % len(color_sequence)]
            for i, group in enumerate(unique_groups)
        }
    
    def _add_single_trace(
        self,
        fig: Figure,
        data: DataFrame,
        group: str,
        tissue: str,
        color: str,
        row: int,
        show_legend: bool
    ) -> None:
        """Add a single trace to the figure."""
        name = f"{group}{f' ({tissue})' if tissue != 'Unknown_tissue' else ''}"
        
        fig.add_trace(
            go.Scatter(
                x=data['Time'],
                y=data['Mean'],
                error_y=dict(
                    type='data',
                    array=data['Std'],
                    visible=True
                ),
                mode='lines+markers',
                name=name,
                legendgroup=group,
                line=dict(color=color),
                showlegend=show_legend
            ),
            row=row, col=1
        )


def visualize_data(
    csv_path: PathLike,
    output_html: PathLike,
    metric: Optional[str] = None,
    width: int = 800,
    height: int = 600,
    theme: str = "plotly_dark",
    time_course_mode: bool = False,
    user_replicates: Optional[List[int]] = None,
    auto_parse_groups: bool = True,
    user_group_labels: Optional[List[str]] = None
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
        theme: Plotly theme name
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
            user_group_labels=user_group_labels
        )
        
        # Load and process data
        df, sid_col = load_and_parse_df(csv_path)
        
        # Check for time data if time course mode requested
        if config.time_course_mode:
            has_time = "Time" in df.columns and df["Time"].notna().any()
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
        fig.write_html(str(output_html), include_plotlyjs=True)
        
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
    parser.add_argument("--width", type=int, default=800, help="Plot width in pixels")
    parser.add_argument("--height", type=int, default=600, help="Plot height in pixels")
    parser.add_argument("--theme", default="plotly_dark", help="Plotly theme name")
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