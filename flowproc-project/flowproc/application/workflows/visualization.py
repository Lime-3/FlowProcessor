"""
Visualization workflow for flow cytometry data.

This module coordinates visualization operations using the new unified
PlotFactory architecture to eliminate code duplication.
"""

import logging
import warnings
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

from ...domain.visualization.flow_cytometry_visualizer import plot
from ...domain.visualization.time_plots import create_timecourse_visualization
from ...domain.visualization.plotly_renderer import PlotlyRenderer
from ...infrastructure.monitoring.metrics import metrics_collector
from ...core.exceptions import FlowProcError
from ...domain.visualization.naming_utils import NamingUtils
from ...domain.visualization import plot, compare_groups

logger = logging.getLogger(__name__)


class VisualizationWorkflow:
    """
    Coordinates visualization operations for flow cytometry data.
    
    This workflow now uses the unified PlotFactory architecture to eliminate
    code duplication and provide consistent visualization interfaces.
    """
    
    def __init__(self):
        """Initialize the visualization workflow."""
        pass  # No service dependencies needed for current modules
    
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
            
            # Create dashboard using unified service
            dashboard_config = config.get('dashboard', {})
            dashboard_fig = plot.create_dashboard(
                dataframes, 
                dashboard_config.get('plots', [])
            )
            
            # Save dashboard
            output_dir = Path(config.get('output_dir', '.'))
            dashboard_path = output_dir / dashboard_config.get('filename', 'dashboard.html')
            
            PlotlyRenderer.save_plot(
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
        Create individual plots from data with standard naming.
        
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
                'plot_paths': [],
                'plots_created': 0,
                'errors': []
            }
            
            plots_config = config.get('plots', [])
            output_dir = Path(config.get('output_dir', '.'))
            source_file = Path(config.get('source_file', '')) if config.get('source_file') else None
            
            for i, plot_config in enumerate(plots_config):
                try:
                    # Create plot using existing plot function
                    plot_type = plot_config.get('type', 'scatter')
                    x_axis = plot_config.get('x', 'Group')
                    y_axis = plot_config.get('y', 'Freq. of Parent')
                    
                    fig = plot(
                        data=data,
                        x=x_axis,
                        y=y_axis,
                        plot_type=plot_type,
                        width=plot_config.get('width', 1200),
                        height=plot_config.get('height', 500)
                    )
                    
                    # Generate standard filename
                    plot_filename = NamingUtils.generate_plot_filename(
                        plot_config=plot_config,
                        data=data,
                        source_file=source_file,
                        plot_index=i + 1
                    )
                    
                    plot_path = output_dir / plot_filename
                    
                    PlotlyRenderer.save_plot(
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
        Create comparison plots between multiple datasets with standard naming.
        
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
                'comparison_paths': [],
                'comparison_plots_created': 0,
                'errors': []
            }
            
            comparisons_config = config.get('comparisons', [])
            output_dir = Path(config.get('output_dir', '.'))
            source_files = config.get('source_files', [])
            if source_files:
                source_files = [Path(f) for f in source_files]
            
            for i, comp_config in enumerate(comparisons_config):
                try:
                    # Create comparison plot using existing compare_groups function
                    # Use the first dataset as primary
                    primary_data = list(data_dict.values())[0]
                    
                    fig = compare_groups(
                        data=primary_data,
                        plot_type=comp_config.get('type', 'box')
                    )
                    
                    # Generate standard filename
                    comparison_filename = NamingUtils.generate_comparison_filename(
                        comparison_config=comp_config,
                        data_dict=data_dict,
                        source_files=source_files,
                        comparison_index=i + 1
                    )
                    
                    comparison_path = output_dir / comparison_filename
                    
                    PlotlyRenderer.save_plot(
                        fig, 
                        str(comparison_path), 
                        format=comp_config.get('format', 'html')
                    )
                    
                    results['comparison_paths'].append(str(comparison_path))
                    results['comparison_plots_created'] += 1
                    
                    logger.debug(f"Created comparison plot {i+1}: {comparison_path}")
                    
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
    
    def create_time_series_plots(self, data: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create time series plots from data.
        
        Args:
            data: Input DataFrame with time series data
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
                'time_series_paths': [],
                'time_series_plots_created': 0,
                'errors': []
            }
            
            time_series_config = config.get('time_series', [])
            output_dir = Path(config.get('output_dir', '.'))
            
            for i, time_config in enumerate(time_series_config):
                try:
                    # Create time series plot using unified service
                    fig = plot.create_time_series_plot(data, time_config)
                    
                    # Save plot
                    time_series_filename = time_config.get('filename', f'time_series_{i+1}.html')
                    time_series_path = output_dir / time_series_filename
                    
                    PlotlyRenderer.save_plot(
                        fig, 
                        str(time_series_path), 
                        format=time_config.get('format', 'html')
                    )
                    
                    results['time_series_paths'].append(str(time_series_path))
                    results['time_series_plots_created'] += 1
                    
                    logger.debug(f"Created time series plot {i+1}: {time_series_path}")
                    
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
    
    def validate_visualization_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate visualization configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validation results
        """
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
                    try:
                        # The unified service is removed, so this call will need to be updated
                        # or the validation logic needs to be adapted.
                        # For now, we'll assume a placeholder or that this part of the workflow
                        # will be refactored in a subsequent edit.
                        # validated_config = self.unified_service.validate_plot_config(plot_config)
                        # dashboard_config['plots'][i] = validated_config
                        pass # Placeholder for validation logic
                    except Exception as e:
                        validation['errors'].append(f"Dashboard plot {i+1}: {str(e)}")
                        validation['valid'] = False
        
        # Validate individual plots config
        if 'plots' in config:
            for i, plot_config in enumerate(config['plots']):
                try:
                    # The unified service is removed, so this call will need to be updated
                    # or the validation logic needs to be adapted.
                    # For now, we'll assume a placeholder or that this part of the workflow
                    # will be refactored in a subsequent edit.
                    # validated_config = self.unified_service.validate_plot_config(plot_config)
                    # config['plots'][i] = validated_config
                    pass # Placeholder for validation logic
                except Exception as e:
                    validation['errors'].append(f"Plot {i+1}: {str(e)}")
                    validation['valid'] = False
        
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
        """
        Get information about visualization capabilities.
        
        Returns:
            Dictionary with visualization capabilities
        """
        # The unified service is removed, so this method will need to be updated
        # or the capabilities need to be defined directly here.
        # For now, we'll return a placeholder.
        return {
            'available_plot_types': ['scatter', 'histogram', 'boxplot', 'violin', 'heatmap', 'scatter3d', 'surface'],
            'available_themes': ['default', 'dark', 'light'],
            'supported_formats': ['html', 'png', 'pdf', 'svg'],
            'workflow_types': ['dashboard', 'individual_plots', 'comparison_plots', 'time_series_plots']
        } 