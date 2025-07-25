"""
Visualization workflow for flow cytometry data.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

from ...domain.visualization.service import VisualizationService
from ...infrastructure.monitoring.metrics import metrics_collector
from ...core.exceptions import FlowProcError

logger = logging.getLogger(__name__)


class VisualizationWorkflow:
    """Coordinates visualization operations for flow cytometry data."""
    
    def __init__(self):
        """Initialize the visualization workflow."""
        self.visualization_service = VisualizationService()
    
    def create_dashboard(self, data: Union[pd.DataFrame, List[pd.DataFrame]], 
                        config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comprehensive dashboard from data.
        
        Args:
            data: DataFrame or list of DataFrames
            config: Visualization configuration
            
        Returns:
            Dictionary with dashboard results
        """
        operation_id = metrics_collector.start_operation(
            "create_dashboard",
            metadata={'data_type': type(data).__name__}
        )
        
        try:
            results = {
                'success': True,
                'dashboard_path': None,
                'plots_created': 0,
                'errors': []
            }
            
            # Convert single DataFrame to list
            if isinstance(data, pd.DataFrame):
                dataframes = [data]
            else:
                dataframes = data
            
            # Create dashboard
            dashboard_config = config.get('dashboard', {})
            dashboard_fig = self.visualization_service.create_dashboard(
                dataframes, 
                dashboard_config.get('plots', [])
            )
            
            # Save dashboard
            output_dir = Path(config.get('output_dir', '.'))
            dashboard_path = output_dir / dashboard_config.get('filename', 'dashboard.html')
            
            self.visualization_service.save_plot(
                dashboard_fig, 
                str(dashboard_path), 
                format='html'
            )
            
            results['dashboard_path'] = str(dashboard_path)
            results['plots_created'] = len(dashboard_config.get('plots', []))
            
            logger.info(f"Dashboard created successfully: {dashboard_path}")
            metrics_collector.end_operation(operation_id, success=True)
            return results
            
        except Exception as e:
            logger.error(f"Dashboard creation failed: {e}")
            metrics_collector.end_operation(operation_id, success=False, error_message=str(e))
            results['success'] = False
            results['errors'].append(str(e))
            return results
    
    def create_individual_plots(self, data: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create individual plots from data.
        
        Args:
            data: Input DataFrame
            config: Visualization configuration
            
        Returns:
            Dictionary with plot results
        """
        operation_id = metrics_collector.start_operation(
            "create_individual_plots",
            metadata={'data_shape': data.shape}
        )
        
        try:
            results = {
                'success': True,
                'plots_created': 0,
                'plot_paths': [],
                'errors': []
            }
            
            plots_config = config.get('plots', [])
            output_dir = Path(config.get('output_dir', '.'))
            
            for i, plot_config in enumerate(plots_config):
                try:
                    # Create plot
                    fig = self.visualization_service.create_plot(
                        data,
                        plot_config.get('type', 'scatter'),
                        plot_config
                    )
                    
                    # Save plot
                    plot_filename = plot_config.get('filename', f'plot_{i+1}.html')
                    plot_path = output_dir / plot_filename
                    
                    self.visualization_service.save_plot(
                        fig, 
                        str(plot_path), 
                        format=plot_config.get('format', 'html')
                    )
                    
                    results['plot_paths'].append(str(plot_path))
                    results['plots_created'] += 1
                    
                    logger.debug(f"Created plot {i+1}: {plot_path}")
                    
                except Exception as e:
                    error_msg = f"Failed to create plot {i+1}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Individual plots created: {results['plots_created']} successful")
            metrics_collector.end_operation(operation_id, success=True)
            return results
            
        except Exception as e:
            logger.error(f"Individual plots creation failed: {e}")
            metrics_collector.end_operation(operation_id, success=False, error_message=str(e))
            results['success'] = False
            results['errors'].append(str(e))
            return results
    
    def create_comparison_plots(self, data_dict: Dict[str, pd.DataFrame], 
                              config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comparison plots between different datasets.
        
        Args:
            data_dict: Dictionary mapping dataset names to DataFrames
            config: Visualization configuration
            
        Returns:
            Dictionary with comparison plot results
        """
        operation_id = metrics_collector.start_operation(
            "create_comparison_plots",
            metadata={'dataset_count': len(data_dict)}
        )
        
        try:
            results = {
                'success': True,
                'comparison_plots_created': 0,
                'plot_paths': [],
                'errors': []
            }
            
            comparison_configs = config.get('comparisons', [])
            output_dir = Path(config.get('output_dir', '.'))
            
            for i, comp_config in enumerate(comparison_configs):
                try:
                    # Get datasets for comparison
                    dataset_names = comp_config.get('datasets', [])
                    datasets = {name: data_dict[name] for name in dataset_names if name in data_dict}
                    
                    if not datasets:
                        logger.warning(f"No valid datasets found for comparison {i+1}")
                        continue
                    
                    # Create comparison plot
                    fig = self._create_comparison_plot(datasets, comp_config)
                    
                    # Save plot
                    plot_filename = comp_config.get('filename', f'comparison_{i+1}.html')
                    plot_path = output_dir / plot_filename
                    
                    self.visualization_service.save_plot(
                        fig, 
                        str(plot_path), 
                        format=comp_config.get('format', 'html')
                    )
                    
                    results['plot_paths'].append(str(plot_path))
                    results['comparison_plots_created'] += 1
                    
                    logger.debug(f"Created comparison plot {i+1}: {plot_path}")
                    
                except Exception as e:
                    error_msg = f"Failed to create comparison plot {i+1}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Comparison plots created: {results['comparison_plots_created']} successful")
            metrics_collector.end_operation(operation_id, success=True)
            return results
            
        except Exception as e:
            logger.error(f"Comparison plots creation failed: {e}")
            metrics_collector.end_operation(operation_id, success=False, error_message=str(e))
            results['success'] = False
            results['errors'].append(str(e))
            return results
    
    def _create_comparison_plot(self, datasets: Dict[str, pd.DataFrame], 
                              config: Dict[str, Any]) -> go.Figure:
        """Create a comparison plot from multiple datasets."""
        plot_type = config.get('type', 'scatter')
        x_col = config.get('x')
        y_col = config.get('y')
        color_col = config.get('color')
        
        # Create subplots
        from plotly.subplots import make_subplots
        
        n_datasets = len(datasets)
        rows = int(n_datasets ** 0.5)
        cols = (n_datasets + rows - 1) // rows
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=list(datasets.keys())
        )
        
        # Add traces for each dataset
        for i, (name, df) in enumerate(datasets.items()):
            row = i // cols + 1
            col = i % cols + 1
            
            if plot_type == 'scatter':
                trace = go.Scatter(
                    x=df[x_col] if x_col else df.iloc[:, 0],
                    y=df[y_col] if y_col else df.iloc[:, 1],
                    mode='markers',
                    name=name,
                    showlegend=False
                )
            elif plot_type == 'bar':
                trace = go.Bar(
                    x=df[x_col] if x_col else df.iloc[:, 0],
                    y=df[y_col] if y_col else df.iloc[:, 1],
                    name=name,
                    showlegend=False
                )
            else:
                # Default to scatter
                trace = go.Scatter(
                    x=df[x_col] if x_col else df.iloc[:, 0],
                    y=df[y_col] if y_col else df.iloc[:, 1],
                    mode='markers',
                    name=name,
                    showlegend=False
                )
            
            fig.add_trace(trace, row=row, col=col)
        
        # Apply theme
        theme = config.get('theme', 'default')
        self.visualization_service.themes.apply_theme(fig, theme)
        
        return fig
    
    def create_time_series_plots(self, data: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create time series plots from data.
        
        Args:
            data: Input DataFrame with time column
            config: Visualization configuration
            
        Returns:
            Dictionary with time series plot results
        """
        operation_id = metrics_collector.start_operation(
            "create_time_series_plots",
            metadata={'data_shape': data.shape}
        )
        
        try:
            results = {
                'success': True,
                'time_series_plots_created': 0,
                'plot_paths': [],
                'errors': []
            }
            
            time_configs = config.get('time_series', [])
            output_dir = Path(config.get('output_dir', '.'))
            
            for i, time_config in enumerate(time_configs):
                try:
                    # Create time series plot
                    fig = self._create_time_series_plot(data, time_config)
                    
                    # Save plot
                    plot_filename = time_config.get('filename', f'time_series_{i+1}.html')
                    plot_path = output_dir / plot_filename
                    
                    self.visualization_service.save_plot(
                        fig, 
                        str(plot_path), 
                        format=time_config.get('format', 'html')
                    )
                    
                    results['plot_paths'].append(str(plot_path))
                    results['time_series_plots_created'] += 1
                    
                    logger.debug(f"Created time series plot {i+1}: {plot_path}")
                    
                except Exception as e:
                    error_msg = f"Failed to create time series plot {i+1}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Time series plots created: {results['time_series_plots_created']} successful")
            metrics_collector.end_operation(operation_id, success=True)
            return results
            
        except Exception as e:
            logger.error(f"Time series plots creation failed: {e}")
            metrics_collector.end_operation(operation_id, success=False, error_message=str(e))
            results['success'] = False
            results['errors'].append(str(e))
            return results
    
    def _create_time_series_plot(self, data: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
        """Create a time series plot."""
        time_col = config.get('time_column', 'Time')
        value_col = config.get('value_column')
        group_col = config.get('group_column')
        
        if time_col not in data.columns:
            raise ValueError(f"Time column '{time_col}' not found in data")
        
        if value_col and value_col not in data.columns:
            raise ValueError(f"Value column '{value_col}' not found in data")
        
        # Create line plot
        fig = self.visualization_service.create_plot(
            data,
            'line',
            {
                'x': time_col,
                'y': value_col,
                'color': group_col,
                'title': config.get('title', 'Time Series Plot'),
                'theme': config.get('theme', 'default')
            }
        )
        
        return fig
    
    def validate_visualization_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate visualization configuration."""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate dashboard config
        if 'dashboard' in config:
            dashboard_config = config['dashboard']
            if 'plots' in dashboard_config:
                for i, plot_config in enumerate(dashboard_config['plots']):
                    plot_validation = self.visualization_service.validate_plot_config(plot_config)
                    if not plot_validation['valid']:
                        validation['errors'].extend([f"Dashboard plot {i+1}: {error}" for error in plot_validation['errors']])
                        validation['valid'] = False
                    validation['warnings'].extend([f"Dashboard plot {i+1}: {warning}" for warning in plot_validation['warnings']])
        
        # Validate individual plots config
        if 'plots' in config:
            for i, plot_config in enumerate(config['plots']):
                plot_validation = self.visualization_service.validate_plot_config(plot_config)
                if not plot_validation['valid']:
                    validation['errors'].extend([f"Plot {i+1}: {error}" for error in plot_validation['errors']])
                    validation['valid'] = False
                validation['warnings'].extend([f"Plot {i+1}: {warning}" for warning in plot_validation['warnings']])
        
        # Validate comparison config
        if 'comparisons' in config:
            for i, comp_config in enumerate(config['comparisons']):
                if 'datasets' not in comp_config:
                    validation['errors'].append(f"Comparison {i+1}: Missing 'datasets' configuration")
                    validation['valid'] = False
        
        # Validate time series config
        if 'time_series' in config:
            for i, time_config in enumerate(config['time_series']):
                if 'time_column' not in time_config:
                    validation['warnings'].append(f"Time series {i+1}: Missing 'time_column' configuration")
        
        return validation
    
    def get_visualization_capabilities(self) -> Dict[str, Any]:
        """Get information about visualization capabilities."""
        return {
            'available_plot_types': self.visualization_service.get_available_plot_types(),
            'available_themes': self.visualization_service.get_available_themes(),
            'supported_formats': ['html', 'png', 'pdf', 'svg'],
            'workflow_types': ['dashboard', 'individual_plots', 'comparison_plots', 'time_series_plots']
        } 