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

from ...domain.visualization.unified_service import UnifiedVisualizationService, get_unified_visualization_service
from ...infrastructure.monitoring.metrics import metrics_collector
from ...core.exceptions import FlowProcError

logger = logging.getLogger(__name__)


class VisualizationWorkflow:
    """
    Coordinates visualization operations for flow cytometry data.
    
    This workflow now uses the unified PlotFactory architecture to eliminate
    code duplication and provide consistent visualization interfaces.
    """
    
    def __init__(self):
        """Initialize the visualization workflow."""
        self.unified_service = get_unified_visualization_service()
    
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
            dashboard_fig = self.unified_service.create_dashboard(
                dataframes, 
                dashboard_config.get('plots', [])
            )
            
            # Save dashboard
            output_dir = Path(config.get('output_dir', '.'))
            dashboard_path = output_dir / dashboard_config.get('filename', 'dashboard.html')
            
            self.unified_service.save_plot(
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
                'plot_paths': [],
                'plots_created': 0,
                'errors': []
            }
            
            plots_config = config.get('plots', [])
            output_dir = Path(config.get('output_dir', '.'))
            
            for i, plot_config in enumerate(plots_config):
                try:
                    # Create plot using unified service
                    plot_type = plot_config.get('type', 'scatter')
                    fig = self.unified_service.create_plot(data, plot_type, plot_config)
                    
                    # Save plot
                    plot_filename = plot_config.get('filename', f'plot_{i+1}.html')
                    plot_path = output_dir / plot_filename
                    
                    self.unified_service.save_plot(
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
        Create comparison plots between multiple datasets.
        
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
            
            for i, comp_config in enumerate(comparisons_config):
                try:
                    # Create comparison plot using unified service
                    fig = self.unified_service.create_comparison_plot(data_dict, comp_config)
                    
                    # Save plot
                    comparison_filename = comp_config.get('filename', f'comparison_{i+1}.html')
                    comparison_path = output_dir / comparison_filename
                    
                    self.unified_service.save_plot(
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
                    fig = self.unified_service.create_time_series_plot(data, time_config)
                    
                    # Save plot
                    time_series_filename = time_config.get('filename', f'time_series_{i+1}.html')
                    time_series_path = output_dir / time_series_filename
                    
                    self.unified_service.save_plot(
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
                        validated_config = self.unified_service.validate_plot_config(plot_config)
                        dashboard_config['plots'][i] = validated_config
                    except Exception as e:
                        validation['errors'].append(f"Dashboard plot {i+1}: {str(e)}")
                        validation['valid'] = False
        
        # Validate individual plots config
        if 'plots' in config:
            for i, plot_config in enumerate(config['plots']):
                try:
                    validated_config = self.unified_service.validate_plot_config(plot_config)
                    config['plots'][i] = validated_config
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
        return {
            'available_plot_types': self.unified_service.get_available_plot_types(),
            'available_themes': self.unified_service.get_available_themes(),
            'supported_formats': ['html', 'png', 'pdf', 'svg'],
            'workflow_types': ['dashboard', 'individual_plots', 'comparison_plots', 'time_series_plots']
        } 