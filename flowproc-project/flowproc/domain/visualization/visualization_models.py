"""
Data models for the visualization domain.

This module contains all data structures and models used throughout
the visualization system, following Domain-Driven Design principles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Union
import pandas as pd
import plotly.graph_objects as go

# Type aliases for clarity
DataFrame = pd.DataFrame
Figure = go.Figure


@dataclass(frozen=True)
class ProcessedData:
    """
    Container for processed visualization data.
    
    This immutable data container holds all the processed data
    needed to create visualizations, ensuring data integrity
    throughout the visualization pipeline.
    
    Attributes:
        dataframes: List of processed DataFrames ready for plotting
        metrics: List of metrics included in the data
        groups: List of group numbers found in the data
        times: List of time points (None if no time data)
        tissues_detected: Whether multiple tissues were detected
        group_map: Mapping from group numbers to human-readable labels
        replicate_count: Number of replicates found in the data
    """
    dataframes: List[DataFrame]
    metrics: List[str]
    groups: List[int]
    times: List[Optional[float]]
    tissues_detected: bool
    group_map: Dict[int, str]
    replicate_count: int
    
    def __post_init__(self) -> None:
        """Validate the processed data after initialization."""
        if not isinstance(self.dataframes, list):
            raise ValueError("dataframes must be a list")
        
        if not isinstance(self.metrics, list):
            raise ValueError("metrics must be a list")
            
        if not isinstance(self.groups, list):
            raise ValueError("groups must be a list")
            
        if not isinstance(self.group_map, dict):
            raise ValueError("group_map must be a dictionary")
            
        if self.replicate_count < 0:
            raise ValueError("replicate_count cannot be negative")
    
    @property
    def has_time_data(self) -> bool:
        """Check if the data contains valid time information."""
        return (
            len(self.times) > 1 or 
            (len(self.times) == 1 and self.times[0] is not None)
        )
    
    @property
    def has_multiple_tissues(self) -> bool:
        """Check if the data contains multiple tissues."""
        return self.tissues_detected
    
    @property
    def is_empty(self) -> bool:
        """Check if the processed data is empty."""
        return len(self.dataframes) == 0 or all(df.empty for df in self.dataframes)
    
    def get_unique_tissues(self) -> List[str]:
        """Get list of unique tissues in the data."""
        tissues = set()
        for df in self.dataframes:
            if 'Tissue' in df.columns:
                tissues.update(df['Tissue'].unique())
        return sorted(list(tissues))
    
    def get_unique_subpopulations(self) -> List[str]:
        """Get list of unique subpopulations in the data."""
        subpops = set()
        for df in self.dataframes:
            if 'Subpopulation' in df.columns:
                subpops.update(df['Subpopulation'].unique())
        return sorted(list(subpops))
    
    def filter_by_tissue(self, tissue: str) -> ProcessedData:
        """
        Create a new ProcessedData filtered by tissue.
        
        Args:
            tissue: Tissue name to filter by
            
        Returns:
            New ProcessedData instance with filtered data
        """
        filtered_dfs = []
        for df in self.dataframes:
            if 'Tissue' in df.columns:
                filtered_df = df[df['Tissue'] == tissue].copy()
                if not filtered_df.empty:
                    filtered_dfs.append(filtered_df)
            else:
                # If no tissue column, include all data
                filtered_dfs.append(df.copy())
        
        return ProcessedData(
            dataframes=filtered_dfs,
            metrics=self.metrics.copy(),
            groups=self.groups.copy(),
            times=self.times.copy(),
            tissues_detected=False,  # Only one tissue after filtering
            group_map=self.group_map.copy(),
            replicate_count=self.replicate_count
        )
    
    def filter_by_subpopulation(self, subpopulation: str) -> ProcessedData:
        """
        Create a new ProcessedData filtered by subpopulation.
        
        Args:
            subpopulation: Subpopulation name to filter by
            
        Returns:
            New ProcessedData instance with filtered data
        """
        filtered_dfs = []
        for df in self.dataframes:
            if 'Subpopulation' in df.columns:
                filtered_df = df[df['Subpopulation'] == subpopulation].copy()
                if not filtered_df.empty:
                    filtered_dfs.append(filtered_df)
            else:
                # If no subpopulation column, include all data
                filtered_dfs.append(df.copy())
        
        return ProcessedData(
            dataframes=filtered_dfs,
            metrics=self.metrics.copy(),
            groups=self.groups.copy(),
            times=self.times.copy(),
            tissues_detected=self.tissues_detected,
            group_map=self.group_map.copy(),
            replicate_count=self.replicate_count
        )


@dataclass(frozen=True)
class PlotData:
    """
    Container for data specific to a single plot.
    
    This model represents the data needed to create a single
    plot within a larger visualization.
    """
    x_values: List[Any]
    y_values: List[float]
    error_values: Optional[List[float]] = None
    group_labels: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    
    def __post_init__(self) -> None:
        """Validate plot data consistency."""
        if len(self.x_values) != len(self.y_values):
            raise ValueError("x_values and y_values must have the same length")
        
        if self.error_values and len(self.error_values) != len(self.y_values):
            raise ValueError("error_values must have the same length as y_values")
        
        if self.group_labels and len(self.group_labels) != len(self.y_values):
            raise ValueError("group_labels must have the same length as y_values")
        
        if self.colors and len(self.colors) != len(self.y_values):
            raise ValueError("colors must have the same length as y_values")


@dataclass
class VisualizationRequest:
    """
    Request object for creating visualizations.
    
    This mutable model represents a request to create a visualization,
    containing all the necessary parameters and configuration.
    """
    data_source: Union[str, DataFrame]
    metric: Optional[str] = None
    output_path: Optional[str] = None
    width: int = 600
    height: int = 300
    theme: str = "default"
    time_course_mode: bool = False
    tissue_filter: Optional[str] = None
    subpopulation_filter: Optional[str] = None
    user_group_labels: Optional[List[str]] = None
    
    def validate(self) -> List[str]:
        """
        Validate the visualization request.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if self.width <= 0:
            errors.append("Width must be positive")
        
        if self.height <= 0:
            errors.append("Height must be positive")
        
        if not isinstance(self.theme, str) or not self.theme.strip():
            errors.append("Theme must be a non-empty string")
        
        if isinstance(self.data_source, str):
            from pathlib import Path
            if not Path(self.data_source).exists():
                errors.append(f"Data source file does not exist: {self.data_source}")
        
        return errors


@dataclass(frozen=True)
class VisualizationResult:
    """
    Result of a visualization operation.
    
    This immutable model contains the results of creating a visualization,
    including the figure, metadata, and any warnings or errors.
    """
    figure: Figure
    metadata: Dict[str, Any]
    warnings: List[str] = None
    processing_time_seconds: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Initialize warnings list if None."""
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
    
    @property
    def success(self) -> bool:
        """Check if the visualization was successful."""
        return self.figure is not None and len(self.figure.data) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def save_html(self, output_path: str, **kwargs) -> None:
        """
        Save the figure as HTML.
        
        Args:
            output_path: Path to save the HTML file
            **kwargs: Additional arguments to pass to figure.write_html()
        """
        if not self.success:
            raise ValueError("Cannot save unsuccessful visualization")
        
        default_config = {
            'include_plotlyjs': True,
            'full_html': True,
            'config': {
                'editable': True,
                'edits': {
                    'axisTitleText': True,
                    'titleText': True,
                    'legendText': True
                }
            }
        }
        
        # Merge user kwargs with defaults
        save_config = {**default_config, **kwargs}
        
        self.figure.write_html(output_path, **save_config)
