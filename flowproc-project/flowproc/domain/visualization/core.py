"""
Core visualization engine for creating interactive flow cytometry plots.

This module contains the main Visualizer class responsible for creating
Plotly figures from processed data, with support for both standard bar plots
and time-course line plots.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from .models import ProcessedData, PlotData, VisualizationResult
from .config import VisualizationConfig
from .themes import VisualizationThemes
from ...core.exceptions import VisualizationError
from ..parsing.tissue_parser import get_tissue_full_name

logger = logging.getLogger(__name__)

# Type aliases
DataFrame = pd.DataFrame
Figure = go.Figure


class Visualizer:
    """
    Creates interactive visualizations from processed data.
    
    This class is the core visualization engine, responsible for taking
    ProcessedData and creating publication-ready Plotly figures. It supports
    multiple visualization modes and provides extensive customization options.
    
    Key features:
    - Bar plots for standard analysis
    - Line plots for time-course analysis  
    - Automatic subplot creation for multiple tissues/subpopulations
    - Theme support with customizable styling
    - Error bars and individual data points
    - Responsive layout management
    """
    
    def __init__(self, config: VisualizationConfig):
        """
        Initialize the visualizer with configuration.
        
        Args:
            config: Visualization configuration
        """
        self.config = config
        self.themes = VisualizationThemes()
        
        # Validate configuration
        if not isinstance(config, VisualizationConfig):
            raise VisualizationError("Config must be a VisualizationConfig instance")
    
    def create_figure(self, processed_data: ProcessedData) -> Figure:
        """
        Create visualization figure from processed data.
        
        This is the main entry point for creating visualizations. It determines
        the appropriate visualization type and creates the corresponding figure.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            Plotly Figure object
            
        Raises:
            VisualizationError: If figure creation fails
        """
        try:
            if processed_data.is_empty:
                return self._create_empty_figure()
            
            # Apply subpopulation filter if specified
            if self.config.subpopulation_filter:
                processed_data = processed_data.filter_by_subpopulation(
                    self.config.subpopulation_filter
                )
                if processed_data.is_empty:
                    return self._create_empty_figure(
                        f"No data found for subpopulation '{self.config.subpopulation_filter}'"
                    )
            
            # Determine visualization type
            if self.config.time_course_mode and processed_data.has_time_data:
                return self._create_time_course_figure(processed_data)
            else:
                return self._create_bar_plot_figure(processed_data)
                
        except Exception as e:
            logger.error(f"Failed to create figure: {e}", exc_info=True)
            raise VisualizationError(f"Figure creation failed: {str(e)}") from e
    
    def create_visualization_result(self, processed_data: ProcessedData) -> VisualizationResult:
        """
        Create a complete visualization result with metadata.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            VisualizationResult with figure and metadata
        """
        import time
        start_time = time.time()
        
        try:
            # Create the figure
            figure = self.create_figure(processed_data)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create metadata
            metadata = {
                'data_shape': (len(processed_data.dataframes), len(processed_data.metrics)),
                'visualization_type': 'time_course' if self.config.time_course_mode else 'bar_plot',
                'theme': self.config.theme,
                'has_subplots': self._has_subplots(processed_data),
                'group_count': len(processed_data.groups),
                'tissue_count': len(processed_data.get_unique_tissues()),
                'metric_count': len(processed_data.metrics),
            }
            
            # Collect any warnings
            warnings = []
            if processed_data.replicate_count < 3:
                warnings.append(f"Low replicate count ({processed_data.replicate_count})")
            
            return VisualizationResult(
                figure=figure,
                metadata=metadata,
                warnings=warnings,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to create visualization result: {e}")
            raise VisualizationError(f"Visualization result creation failed: {str(e)}") from e
    
    def _create_empty_figure(self, message: str = "No data to visualize") -> Figure:
        """
        Create figure for empty or invalid data.
        
        Args:
            message: Message to display in the empty figure
            
        Returns:
            Plotly Figure with empty data message
        """
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20, color='gray')
        )
        
        # Apply theme and sizing
        self.themes.apply_theme(fig, self.config.theme)
        height = self.config.height if self.config.height is not None else 300
        fig.update_layout(
            width=self.config.width, 
            height=height,
            title="Visualization"
        )
        
        return fig
    
    def _create_time_course_figure(self, processed_data: ProcessedData) -> Figure:
        """
        Create time-course visualization with subplots.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            Plotly Figure with time-course visualization
        """
        logger.debug("Creating time-course visualization")
        
        # Determine subplot structure
        subplot_titles, rows, cols = self._calculate_subplot_layout(processed_data)
        
        # Create subplots
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=subplot_titles,
            shared_xaxes=True,
            shared_yaxes=False,
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Plot data for each subplot
        subplot_idx = 1
        for df in processed_data.dataframes:
            self._add_time_course_traces(fig, df, subplot_idx, processed_data.group_map)
            subplot_idx += 1
        
        # Apply styling and theme
        self._apply_time_course_styling(fig, processed_data, rows, cols)
        
        return fig
    
    def _create_bar_plot_figure(self, processed_data: ProcessedData) -> Figure:
        """
        Create standard bar plot visualization.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            Plotly Figure with bar plot visualization
        """
        logger.debug("Creating bar plot visualization")
        
        # Determine if we need subplots
        if self._has_subplots(processed_data):
            return self._create_bar_plot_subplots(processed_data)
        else:
            return self._create_single_bar_plot(processed_data)
    
    def _create_single_bar_plot(self, processed_data: ProcessedData) -> Figure:
        """
        Create a single bar plot from the data.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            Single bar plot figure
        """
        fig = go.Figure()
        
        if processed_data.dataframes:
            # If there are multiple dataframes (e.g., multiple tissues), combine them
            # to show all subpopulations in a single plot
            if len(processed_data.dataframes) > 1:
                # Combine all dataframes to show all subpopulations
                combined_df = pd.concat(processed_data.dataframes, ignore_index=True)
                self._add_bar_plot_traces(fig, combined_df, processed_data.group_map)
            else:
                # Use the single dataframe
                df = processed_data.dataframes[0]
                self._add_bar_plot_traces(fig, df, processed_data.group_map)
        
        # Apply styling
        self._apply_bar_plot_styling(fig, processed_data)
        
        return fig
    
    def _create_bar_plot_subplots(self, processed_data: ProcessedData) -> Figure:
        """
        Create bar plot with multiple subplots.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            Multi-subplot bar plot figure
        """
        # Calculate subplot layout
        subplot_titles, rows, cols = self._calculate_subplot_layout(processed_data)
        
        # Create subplots
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=subplot_titles,
            shared_xaxes=False,
            shared_yaxes=True,
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # Add data to each subplot
        for idx, df in enumerate(processed_data.dataframes):
            subplot_idx = idx + 1
            self._add_bar_plot_traces(fig, df, processed_data.group_map, subplot_idx, rows, cols)
        
        # Apply styling
        self._apply_bar_plot_styling(fig, processed_data, rows, cols)
        
        return fig
    
    def _add_time_course_traces(
        self, 
        fig: Figure, 
        df: DataFrame, 
        subplot_idx: int,
        group_map: Dict[int, str]
    ) -> None:
        """
        Add time-course traces to a subplot.
        
        Args:
            fig: Plotly figure to add traces to
            df: DataFrame with time-course data
            subplot_idx: Subplot index (1-based)
            group_map: Mapping from group numbers to labels
        """
        if df.empty or 'Time' not in df.columns:
            return
        
        # Calculate subplot position
        # Use the current Plotly API for subplot layout
        if hasattr(fig, 'get_subplots'):
            subplots = fig.get_subplots()
            rows = subplots.rows
            cols = subplots.cols
        else:
            # Fallback for older versions or single plots
            rows = 1
            cols = 1
        
        row = ((subplot_idx - 1) // cols) + 1
        col = ((subplot_idx - 1) % cols) + 1
        
        # Group data by group label
        grouped = df.groupby('Group_Label')
        
        for group_label, group_data in grouped:
            # Sort by time
            group_data = group_data.sort_values('Time')
            
            # Get color for this group
            color = self._get_group_color(group_label, list(group_map.values()))
            
            # Add line trace
            fig.add_trace(
                go.Scatter(
                    x=group_data['Time'],
                    y=group_data['Mean'],
                    error_y=dict(
                        type='data',
                        array=group_data['Std'] if self.config.error_bars else None,
                        visible=self.config.error_bars
                    ),
                    mode='lines+markers',
                    name=group_label,
                    line=dict(color=color, width=2),
                    marker=dict(color=color, size=6),
                    showlegend=(subplot_idx == 1),  # Only show legend for first subplot
                    legendgroup=group_label,  # Group legend items
                ),
                row=row, col=col
            )
            
            # Add individual points if requested
            if self.config.show_individual_points:
                # This would require individual data points, which might not be available
                # in the aggregated data. For now, we'll skip this feature.
                pass
    
    def _add_bar_plot_traces(
        self, 
        fig: Figure, 
        df: DataFrame,
        group_map: Dict[int, str],
        subplot_idx: Optional[int] = None,
        rows: int = 1,
        cols: int = 1
    ) -> None:
        """
        Add bar plot traces to a figure or subplot.
        
        Args:
            fig: Plotly figure to add traces to
            df: DataFrame with bar plot data
            group_map: Mapping from group numbers to labels
            subplot_idx: Subplot index (1-based, None for single plot)
        """
        if df.empty or 'Group_Label' not in df.columns:
            return
        
        # Determine subplot position
        row, col = 1, 1
        if subplot_idx is not None:
            # Calculate position for subplots using provided rows/cols
            row = ((subplot_idx - 1) // cols) + 1
            col = ((subplot_idx - 1) % cols) + 1
        
        # Get unique groups for x-axis
        group_labels = sorted(df['Group_Label'].unique())
        
        # Get unique subpopulations for different colored bars
        if 'Subpopulation' in df.columns:
            subpopulations = sorted(df['Subpopulation'].unique())
        elif 'Tissue' in df.columns:
            subpopulations = sorted(df['Tissue'].unique())
        else:
            # Fallback to using groups as subpopulations if no subpopulation column
            subpopulations = group_labels
            group_labels = [f"Group {i+1}" for i in range(len(group_labels))]
        
        # Create traces for each subpopulation
        for subpop in subpopulations:
            subpop_data = df[df.get('Subpopulation', df.get('Tissue', 'Group_Label')) == subpop]
            
            # Get color for this subpopulation
            color = self._get_group_color(subpop, subpopulations)
            
            # Prepare data for this subpopulation across all groups
            y_values = []
            for group_label in group_labels:
                group_subpop_data = subpop_data[subpop_data['Group_Label'] == group_label]
                if not group_subpop_data.empty:
                    y_values.append(group_subpop_data['Mean'].iloc[0])
                else:
                    y_values.append(0)  # No data for this group/subpop combination
            
            # Add bar trace
            trace_args = {
                'x': group_labels,
                'y': y_values,
                'name': subpop,
                'marker': dict(color=color),
                'showlegend': (subplot_idx is None or subplot_idx == 1),
                'legendgroup': subpop,
            }
            
            # Add error bars if requested
            if self.config.error_bars and 'Std' in subpop_data.columns:
                std_values = []
                for group_label in group_labels:
                    group_subpop_data = subpop_data[subpop_data['Group_Label'] == group_label]
                    if not group_subpop_data.empty and 'Std' in group_subpop_data.columns:
                        std_values.append(group_subpop_data['Std'].iloc[0])
                    else:
                        std_values.append(0)
                
                trace_args['error_y'] = dict(
                    type='data',
                    array=std_values,
                    visible=True
                )
            
            bar_trace = go.Bar(**trace_args)
            
            if subplot_idx is not None:
                fig.add_trace(bar_trace, row=row, col=col)
            else:
                fig.add_trace(bar_trace)
    
    def _calculate_subplot_layout(self, processed_data: ProcessedData) -> Tuple[List[str], int, int]:
        """
        Calculate the optimal subplot layout.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            Tuple of (subplot_titles, rows, cols)
        """
        num_subplots = len(processed_data.dataframes)
        
        if num_subplots <= 1:
            return [], 1, 1
        
        # Calculate optimal grid layout
        if num_subplots <= 2:
            rows, cols = 1, 2
        elif num_subplots <= 4:
            rows, cols = 2, 2
        elif num_subplots <= 6:
            rows, cols = 2, 3
        elif num_subplots <= 9:
            rows, cols = 3, 3
        else:
            rows = int(np.ceil(np.sqrt(num_subplots)))
            cols = int(np.ceil(num_subplots / rows))
        
        # Generate subplot titles
        subplot_titles = []
        for df in processed_data.dataframes:
            title = self._generate_subplot_title(df)
            subplot_titles.append(title)
        
        # Pad with empty titles if needed
        while len(subplot_titles) < rows * cols:
            subplot_titles.append("")
        
        return subplot_titles[:rows * cols], rows, cols
    
    def _generate_subplot_title(self, df: DataFrame) -> str:
        """
        Generate an appropriate title for a subplot.
        
        Args:
            df: DataFrame for the subplot
            
        Returns:
            Subplot title string
        """
        title_parts = []
        
        # Add metric if available
        if 'Metric' in df.columns:
            metric = df['Metric'].iloc[0] if not df.empty else "Unknown"
            title_parts.append(metric)
        
        # Add tissue if available and multiple tissues exist
        if 'Tissue' in df.columns:
            tissue = df['Tissue'].iloc[0] if not df.empty else "Unknown"
            # Convert tissue code to full name for display
            tissue_name = get_tissue_full_name(tissue) if tissue != "Unknown" else tissue
            title_parts.append(tissue_name)
        
        # Add subpopulation if available
        if 'Subpopulation' in df.columns:
            subpop = df['Subpopulation'].iloc[0] if not df.empty else "Unknown"
            title_parts.append(subpop)
        
        return " - ".join(title_parts) if title_parts else "Data"
    
    def _get_x_axis_labels(self, df: DataFrame) -> List[str]:
        """
        Generate appropriate x-axis labels from the data.
        
        Args:
            df: DataFrame to generate labels from
            
        Returns:
            List of x-axis label strings
        """
        if 'Subpopulation' in df.columns:
            return df['Subpopulation'].tolist()
        elif 'Tissue' in df.columns:
            # Convert tissue codes to full names for display
            return [get_tissue_full_name(tissue) for tissue in df['Tissue'].tolist()]
        elif 'Group_Label' in df.columns:
            return df['Group_Label'].tolist()
        else:
            return [f"Data {i+1}" for i in range(len(df))]
    
    def _get_group_color(self, group_label: str, all_groups: List[str]) -> str:
        """
        Get color for a specific group.
        
        Args:
            group_label: Label of the group
            all_groups: List of all group labels
            
        Returns:
            Color string (hex or named color)
        """
        # Use custom color palette if provided
        if self.config.color_palette:
            try:
                idx = all_groups.index(group_label)
                if idx < len(self.config.color_palette):
                    return self.config.color_palette[idx]
            except (ValueError, IndexError):
                pass
        
        # Use theme-based colors
        return self.themes.get_group_color(group_label, all_groups, self.config.theme)
    
    def _apply_time_course_styling(
        self, 
        fig: Figure, 
        processed_data: ProcessedData,
        rows: int,
        cols: int
    ) -> None:
        """
        Apply styling specific to time-course plots.
        
        Args:
            fig: Figure to style
            processed_data: Processed data container
            rows: Number of subplot rows
            cols: Number of subplot columns
        """
        # Apply theme
        self.themes.apply_theme(fig, self.config.theme)
        
        # Update layout
        height = self.config.height if self.config.height is not None else 300 * rows
        
        fig.update_layout(
            width=self.config.width,
            height=height,
            title=self._generate_main_title(processed_data, "Time Course Analysis"),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        # Update axes
        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text=self._get_y_axis_title(processed_data))
    
    def _apply_bar_plot_styling(
        self, 
        fig: Figure, 
        processed_data: ProcessedData,
        rows: int = 1,
        cols: int = 1
    ) -> None:
        """
        Apply styling specific to bar plots.
        
        Args:
            fig: Figure to style
            processed_data: Processed data container
            rows: Number of subplot rows
            cols: Number of subplot columns
        """
        # Apply theme
        self.themes.apply_theme(fig, self.config.theme)
        
        # Update layout
        height = self.config.height if self.config.height is not None else 300 * rows
        
        fig.update_layout(
            width=self.config.width,
            height=height,
            title=self._generate_main_title(processed_data, "Analysis"),
            showlegend=True,
            barmode='group',
            legend=dict(
                orientation="v",
                yanchor="top", 
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        # Update axes
        fig.update_yaxes(title_text=self._get_y_axis_title(processed_data))
    
    def _generate_main_title(self, processed_data: ProcessedData, analysis_type: str) -> str:
        """
        Generate the main title for the figure.
        
        Args:
            processed_data: Processed data container
            analysis_type: Type of analysis (e.g., "Time Course Analysis")
            
        Returns:
            Main title string
        """
        # Check if we have tissue information
        if processed_data.dataframes:
            df = processed_data.dataframes[0]
            if 'Tissue' in df.columns and not df.empty:
                # Check if there's only one unique tissue
                unique_tissues = df['Tissue'].unique()
                if len(unique_tissues) == 1:
                    tissue = unique_tissues[0]
                    if tissue and tissue != 'UNK':
                        # Return just the tissue name
                        from ..parsing.tissue_parser import get_tissue_full_name
                        return get_tissue_full_name(tissue)
        
        # If no tissue detected or multiple tissues, return the metric name
        if len(processed_data.metrics) == 1:
            return processed_data.metrics[0]
        elif len(processed_data.metrics) > 1:
            return f"{len(processed_data.metrics)} Metrics"
        else:
            return "Data Visualization"
    
    def _get_y_axis_title(self, processed_data: ProcessedData) -> str:
        """
        Generate appropriate y-axis title.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            Y-axis title string
        """
        if len(processed_data.metrics) == 1:
            return processed_data.metrics[0]
        else:
            return "Value"
    
    def _has_subplots(self, processed_data: ProcessedData) -> bool:
        """
        Check if the visualization needs subplots.
        
        Args:
            processed_data: Processed data container
            
        Returns:
            True if subplots are needed
        """
        return (
            len(processed_data.dataframes) > 1 or
            processed_data.has_multiple_tissues or
            len(processed_data.metrics) > 1
        )


class VisualizationFactory:
    """
    Factory for creating different types of visualizations.
    
    This factory provides convenient methods for creating visualizers
    optimized for different types of analysis and use cases.
    """
    
    @staticmethod
    def create_time_course_visualizer(
        metric: Optional[str] = None,
        width: int = 1200,
        height: int = 600,
        **kwargs
    ) -> Visualizer:
        """
        Create a visualizer optimized for time-course analysis.
        
        Args:
            metric: Specific metric to visualize
            width: Plot width
            height: Plot height
            **kwargs: Additional configuration parameters
            
        Returns:
            Visualizer configured for time-course analysis
        """
        config = VisualizationConfig.create_time_course(
            metric=metric,
            width=width,
            height=height,
            **kwargs
        )
        return Visualizer(config)
    
    @staticmethod
    def create_publication_visualizer(
        metric: Optional[str] = None,
        **kwargs
    ) -> Visualizer:
        """
        Create a visualizer for publication-ready figures.
        
        Args:
            metric: Specific metric to visualize
            **kwargs: Additional configuration parameters
            
        Returns:
            Visualizer configured for publication
        """
        config = VisualizationConfig.create_publication_ready(
            metric=metric,
            **kwargs
        )
        return Visualizer(config)
    
    @staticmethod
    def create_exploratory_visualizer(
        theme: str = "default",
        **kwargs
    ) -> Visualizer:
        """
        Create a visualizer for exploratory data analysis.
        
        Args:
            theme: Theme to use
            **kwargs: Additional configuration parameters
            
        Returns:
            Visualizer configured for exploration
        """
        config = VisualizationConfig(
            theme=theme,
            show_individual_points=True,
            interactive=True,
            **kwargs
        )
        return Visualizer(config)
