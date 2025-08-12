"""
Data processing workflow for flow cytometry data.

This workflow orchestrates the complete data processing pipeline using
the unified processing architecture to eliminate duplication.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import pandas as pd

from ...domain.parsing.service import ParseService
from ...domain.processing.core import UnifiedProcessingService, ProcessingConfig, ProcessingMode
from ...domain.export.service import ExportService
from ...infrastructure.monitoring.metrics import metrics_collector
from ...core.exceptions import FlowProcError

logger = logging.getLogger(__name__)


class DataProcessingWorkflow:
    """
    Coordinates the complete data processing workflow.
    
    This workflow uses the unified processing architecture to eliminate
    duplication and provide clear separation of concerns.
    """
    
    def __init__(self):
        """Initialize the workflow."""
        self.parse_service = ParseService()
        self.unified_processing_service = UnifiedProcessingService()
        self.export_service = ExportService()
        
        # Register default parsing strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """Register default parsing strategies."""
        from ...domain.parsing.strategies import DefaultParsingStrategy, MinimalParsingStrategy
        
        self.parse_service.register_strategy("default", DefaultParsingStrategy())
        self.parse_service.register_strategy("minimal", MinimalParsingStrategy())
    
    def process_file(self, input_file: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single file through the complete workflow.
        
        Args:
            input_file: Path to input file
            config: Processing configuration
            
        Returns:
            Dictionary with processing results
        """
        operation_id = metrics_collector.start_operation(
            "process_file", 
            metadata={'input_file': str(input_file)}
        )
        
        try:
            results = {
                'input_file': str(input_file),
                'success': True,
                'stages': {},
                'outputs': {}
            }
            
            # Stage 1: Parse data
            logger.info(f"Starting parsing stage for {input_file}")
            parsed_data = self._parse_stage(input_file, config.get('parsing', {}))
            results['stages']['parsing'] = {
                'success': True,
                'data_shape': parsed_data.shape,
                'columns': list(parsed_data.columns)
            }
            
            # Stage 2: Process data
            logger.info("Starting processing stage")
            processed_data = self._processing_stage(parsed_data, config.get('processing', {}))
            results['stages']['processing'] = {
                'success': True,
                'data_shape': processed_data.shape,
                'columns': list(processed_data.columns)
            }
            
            # Stage 3: Create visualizations (optional)
            if config.get('visualization', {}).get('create_plots', False):
                logger.info("Starting visualization stage")
                plots = self._visualization_stage(processed_data, config.get('visualization', {}))
                results['stages']['visualization'] = {
                    'success': True,
                    'plots_created': len(plots)
                }
                results['outputs']['plots'] = plots
            
            # Stage 4: Export data (optional)
            if config.get('export', {}).get('export_data', False):
                logger.info("Starting export stage")
                export_paths = self._export_stage(processed_data, config.get('export', {}))
                results['stages']['export'] = {
                    'success': True,
                    'export_paths': export_paths
                }
                results['outputs']['export_paths'] = export_paths
            
            logger.info("Data processing workflow completed successfully")
            metrics_collector.end_operation(operation_id, success=True)
            return results
            
        except Exception as e:
            logger.error(f"Data processing workflow failed: {e}")
            metrics_collector.end_operation(operation_id, success=False, error_message=str(e))
            results['success'] = False
            results['error'] = str(e)
            return results
    
    def _parse_stage(self, input_file: Path, config: Dict[str, Any]) -> pd.DataFrame:
        """Execute parsing stage."""
        strategy = config.get('strategy', 'default')
        return self.parse_service.parse_file(input_file, strategy)
    
    def _processing_stage(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Execute processing stage using unified architecture."""
        # Convert workflow config to unified config
        unified_config = ProcessingConfig(
            mode=ProcessingMode.WORKFLOW,
            group_by=config.get('group_by', []),
            aggregation_methods=config.get('aggregation_methods', ['mean']),
            transform_options=config.get('transform_options', {}),
            filter_options=config.get('filter_options', {}),
            visualization_options=config.get('visualization_options', {})
        )
        
        return self.unified_processing_service.process_data(data, unified_config)
    
    def _visualization_stage(self, data: pd.DataFrame, config: Dict[str, Any]) -> List[str]:
        """Execute visualization stage."""
        plots = []
        plot_configs = config.get('plots', [])
        
        for i, plot_config in enumerate(plot_configs):
            try:
                from ...domain.visualization.flow_cytometry_visualizer import plot
                from ...domain.visualization.plotly_renderer import PlotlyRenderer
                
                # Create plot using current module
                fig = plot(
                    data=data,
                    x=plot_config.get('x', 'Group'),
                    y=plot_config.get('y', 'Freq. of Parent'),
                    plot_type=plot_config.get('type', 'scatter'),
                    width=plot_config.get('width', 1200),
                    height=plot_config.get('height', 500)
                )
                
                # Save plot using current renderer
                output_path = Path(config.get('output_dir', '.')) / f"plot_{i+1}.html"
                renderer = PlotlyRenderer()
                renderer.export_to_html_optimized(fig, str(output_path), 'minimal')
                plots.append(str(output_path))
                
            except Exception as e:
                logger.error(f"Failed to create plot {i+1}: {e}")
        
        return plots
    
    def _export_stage(self, data: pd.DataFrame, config: Dict[str, Any]) -> List[str]:
        """Execute export stage."""
        export_paths = []
        export_configs = config.get('formats', ['excel'])
        output_dir = Path(config.get('output_dir', '.'))
        
        for format_type in export_configs:
            try:
                output_path = output_dir / f"processed_data.{format_type}"
                self.export_service.export_data(
                    data, 
                    str(output_path), 
                    format_type, 
                    config.get('export_options', {})
                )
                export_paths.append(str(output_path))
                
            except Exception as e:
                logger.error(f"Failed to export to {format_type}: {e}")
        
        return export_paths
    
    def process_batch(self, input_files: List[Path], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process multiple files in batch.
        
        Args:
            input_files: List of input file paths
            config: Processing configuration
            
        Returns:
            Dictionary with batch processing results
        """
        operation_id = metrics_collector.start_operation(
            "process_batch", 
            metadata={'file_count': len(input_files)}
        )
        
        try:
            results = {
                'total_files': len(input_files),
                'successful_files': 0,
                'failed_files': 0,
                'file_results': [],
                'success': True
            }
            
            for input_file in input_files:
                try:
                    file_result = self.process_file(input_file, config)
                    results['file_results'].append(file_result)
                    
                    if file_result['success']:
                        results['successful_files'] += 1
                    else:
                        results['failed_files'] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process {input_file}: {e}")
                    results['failed_files'] += 1
                    results['file_results'].append({
                        'input_file': str(input_file),
                        'success': False,
                        'error': str(e)
                    })
            
            logger.info(f"Batch processing completed: {results['successful_files']} successful, {results['failed_files']} failed")
            metrics_collector.end_operation(operation_id, success=True)
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            metrics_collector.end_operation(operation_id, success=False, error_message=str(e))
            return {
                'total_files': len(input_files),
                'successful_files': 0,
                'failed_files': len(input_files),
                'success': False,
                'error': str(e)
            }
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate processing configuration."""
        from ...core.validation import validate_config
        
        try:
            result = validate_config(config, 'workflow')
            
            # Additional workflow-specific validation
            if 'parsing' in config:
                parsing_config = config['parsing']
                if 'strategy' in parsing_config:
                    available_strategies = self.parse_service.get_available_strategies()
                    if parsing_config['strategy'] not in available_strategies:
                        result.add_issue('parsing.strategy', 
                                       f"Unknown parsing strategy: {parsing_config['strategy']}")
            
            if 'export' in config:
                export_config = config['export']
                if 'formats' in export_config:
                    available_formats = self.export_service.get_export_formats()
                    for format_type in export_config['formats']:
                        if format_type not in available_formats:
                            result.add_issue('export.formats', 
                                           f"Unsupported export format: {format_type}")
            
            return result.to_dict()
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Configuration validation failed: {str(e)}"],
                'warnings': []
            }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow capabilities."""
        return {
            'available_parsing_strategies': self.parse_service.get_available_strategies(),
            'available_plot_types': self.visualization_service.get_available_plot_types(),
            'available_themes': self.visualization_service.get_available_themes(),
            'available_export_formats': self.export_service.get_export_formats(),
            'processing_stats': self._get_processing_stats()
        }
    
    def _get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics using unified architecture."""
        # Create a minimal DataFrame for stats calculation
        df = pd.DataFrame({'sample': [1, 2, 3], 'value': [1.0, 2.0, 3.0]})
        
        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'numeric_columns': [],
            'categorical_columns': [],
            'datetime_columns': []
        }
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats['numeric_columns'].append(col)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                stats['datetime_columns'].append(col)
            else:
                stats['categorical_columns'].append(col)
        
        return stats