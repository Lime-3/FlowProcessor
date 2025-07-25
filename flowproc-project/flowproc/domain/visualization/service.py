"""
VisualizationService - Coordinates visualization operations.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging

from ...core.exceptions import VisualizationError
from .plotly_renderer import PlotlyRenderer
from .themes import VisualizationThemes

logger = logging.getLogger(__name__)


class VisualizationService:
    """Service for coordinating visualization operations."""
    
    def __init__(self):
        self.renderer = PlotlyRenderer()
        self.themes = VisualizationThemes()
        
    def create_plot(self, df: pd.DataFrame, plot_type: str, 
                   config: Dict[str, Any]) -> go.Figure:
        """Create a plot using the specified type and configuration."""
        try:
            if plot_type == 'scatter':
                return self._create_scatter_plot(df, config)
            elif plot_type == 'bar':
                return self._create_bar_plot(df, config)
            elif plot_type == 'line':
                return self._create_line_plot(df, config)
            elif plot_type == 'box':
                return self._create_box_plot(df, config)
            elif plot_type == 'heatmap':
                return self._create_heatmap(df, config)
            elif plot_type == 'histogram':
                return self._create_histogram(df, config)
            else:
                raise VisualizationError(f"Unknown plot type: {plot_type}")
                
        except Exception as e:
            raise VisualizationError(f"Failed to create {plot_type} plot: {str(e)}") from e
    
    def _create_scatter_plot(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create a scatter plot."""
        x_col = config.get('x', df.columns[0])
        y_col = config.get('y', df.columns[1])
        color_col = config.get('color')
        size_col = config.get('size')
        
        fig = px.scatter(
            df, x=x_col, y=y_col, color=color_col, size=size_col,
            title=config.get('title', f'{y_col} vs {x_col}'),
            labels=config.get('labels', {})
        )
        
        # Apply theme
        theme = config.get('theme', 'default')
        self.themes.apply_theme(fig, theme)
        
        return fig
    
    def _create_bar_plot(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create a bar plot."""
        x_col = config.get('x', df.columns[0])
        y_col = config.get('y', df.columns[1])
        color_col = config.get('color')
        
        fig = px.bar(
            df, x=x_col, y=y_col, color=color_col,
            title=config.get('title', f'{y_col} by {x_col}'),
            labels=config.get('labels', {})
        )
        
        # Apply theme
        theme = config.get('theme', 'default')
        self.themes.apply_theme(fig, theme)
        
        return fig
    
    def _create_line_plot(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create a line plot."""
        x_col = config.get('x', df.columns[0])
        y_col = config.get('y', df.columns[1])
        color_col = config.get('color')
        
        fig = px.line(
            df, x=x_col, y=y_col, color=color_col,
            title=config.get('title', f'{y_col} over {x_col}'),
            labels=config.get('labels', {})
        )
        
        # Apply theme
        theme = config.get('theme', 'default')
        self.themes.apply_theme(fig, theme)
        
        return fig
    
    def _create_box_plot(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create a box plot."""
        x_col = config.get('x', df.columns[0])
        y_col = config.get('y', df.columns[1])
        color_col = config.get('color')
        
        fig = px.box(
            df, x=x_col, y=y_col, color=color_col,
            title=config.get('title', f'Distribution of {y_col} by {x_col}'),
            labels=config.get('labels', {})
        )
        
        # Apply theme
        theme = config.get('theme', 'default')
        self.themes.apply_theme(fig, theme)
        
        return fig
    
    def _create_heatmap(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create a heatmap."""
        # For heatmap, we need to pivot the data
        x_col = config.get('x', df.columns[0])
        y_col = config.get('y', df.columns[1])
        values_col = config.get('values', df.columns[2])
        
        pivot_df = df.pivot_table(
            values=values_col, 
            index=y_col, 
            columns=x_col, 
            aggfunc='mean'
        )
        
        fig = px.imshow(
            pivot_df,
            title=config.get('title', f'Heatmap of {values_col}'),
            labels=config.get('labels', {})
        )
        
        # Apply theme
        theme = config.get('theme', 'default')
        self.themes.apply_theme(fig, theme)
        
        return fig
    
    def _create_histogram(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create a histogram."""
        x_col = config.get('x', df.columns[0])
        color_col = config.get('color')
        
        fig = px.histogram(
            df, x=x_col, color=color_col,
            title=config.get('title', f'Distribution of {x_col}'),
            labels=config.get('labels', {})
        )
        
        # Apply theme
        theme = config.get('theme', 'default')
        self.themes.apply_theme(fig, theme)
        
        return fig
    
    def create_dashboard(self, dataframes: List[pd.DataFrame], 
                        plots_config: List[Dict[str, Any]]) -> go.Figure:
        """Create a dashboard with multiple plots."""
        try:
            n_plots = len(plots_config)
            rows = int(n_plots ** 0.5)
            cols = (n_plots + rows - 1) // rows
            
            fig = make_subplots(
                rows=rows, cols=cols,
                subplot_titles=[config.get('title', f'Plot {i+1}') for i, config in enumerate(plots_config)]
            )
            
            for i, (df, config) in enumerate(zip(dataframes, plots_config)):
                row = i // cols + 1
                col = i % cols + 1
                
                plot_type = config.get('type', 'scatter')
                plot_fig = self.create_plot(df, plot_type, config)
                
                # Add traces to subplot
                for trace in plot_fig.data:
                    fig.add_trace(trace, row=row, col=col)
            
            # Apply theme
            theme = plots_config[0].get('theme', 'default') if plots_config else 'default'
            self.themes.apply_theme(fig, theme)
            
            return fig
            
        except Exception as e:
            raise VisualizationError(f"Failed to create dashboard: {str(e)}") from e
    
    def save_plot(self, fig: go.Figure, filepath: str, format: str = 'html') -> None:
        """Save a plot to file."""
        try:
            if format == 'html':
                fig.write_html(filepath)
            elif format == 'png':
                fig.write_image(filepath)
            elif format == 'pdf':
                fig.write_image(filepath)
            elif format == 'svg':
                fig.write_image(filepath)
            else:
                raise VisualizationError(f"Unsupported format: {format}")
                
        except Exception as e:
            raise VisualizationError(f"Failed to save plot: {str(e)}") from e
    
    def get_available_plot_types(self) -> List[str]:
        """Get list of available plot types."""
        return ['scatter', 'bar', 'line', 'box', 'heatmap', 'histogram']
    
    def get_available_themes(self) -> List[str]:
        """Get list of available themes."""
        return self.themes.get_available_themes()
    
    def validate_plot_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plot configuration."""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        if 'type' not in config:
            validation['errors'].append("Plot type is required")
            validation['valid'] = False
        
        # Check plot type
        valid_types = self.get_available_plot_types()
        if 'type' in config and config['type'] not in valid_types:
            validation['errors'].append(f"Invalid plot type: {config['type']}")
            validation['valid'] = False
        
        # Check theme
        valid_themes = self.get_available_themes()
        if 'theme' in config and config['theme'] not in valid_themes:
            validation['warnings'].append(f"Unknown theme: {config['theme']}")
        
        return validation 