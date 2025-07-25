"""
Data processing workflow for flow cytometry data.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import pandas as pd

from ...domain.parsing.service import ParseService
from ...domain.processing.service import DataProcessingService
from ...domain.visualization.service import VisualizationService
from ...domain.export.service import ExportService
from ...infrastructure.monitoring.metrics import metrics_collector
from ...core.exceptions import FlowProcError

logger = logging.getLogger(__name__)


class DataProcessingWorkflow:
    """Coordinates the complete data processing workflow."""
    
    def __init__(self):
        """Initialize the workflow."""
        self.parse_service = ParseService()
        self.processing_service = DataProcessingService()
        self.visualization_service = VisualizationService()
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
        """Execute processing stage."""
        return self.processing_service.process_data(data, config)
    
    def _visualization_stage(self, data: pd.DataFrame, config: Dict[str, Any]) -> List[str]:
        """Execute visualization stage."""
        plots = []
        plot_configs = config.get('plots', [])
        
        for i, plot_config in enumerate(plot_configs):
            try:
                fig = self.visualization_service.create_plot(
                    data, 
                    plot_config.get('type', 'scatter'), 
                    plot_config
                )
                
                # Save plot
                output_path = config.get('output_dir', '.') / f"plot_{i+1}.html"
                self.visualization_service.save_plot(fig, str(output_path))
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
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate parsing config
        if 'parsing' in config:
            parsing_config = config['parsing']
            if 'strategy' in parsing_config:
                available_strategies = self.parse_service.get_available_strategies()
                if parsing_config['strategy'] not in available_strategies:
                    validation['errors'].append(f"Unknown parsing strategy: {parsing_config['strategy']}")
                    validation['valid'] = False
        
        # Validate processing config
        if 'processing' in config:
            processing_validation = self.processing_service.validate_processing_config(config['processing'])
            if not processing_validation['valid']:
                validation['errors'].extend(processing_validation['errors'])
                validation['valid'] = False
            validation['warnings'].extend(processing_validation['warnings'])
        
        # Validate visualization config
        if 'visualization' in config:
            viz_config = config['visualization']
            if 'plots' in viz_config:
                for i, plot_config in enumerate(viz_config['plots']):
                    plot_validation = self.visualization_service.validate_plot_config(plot_config)
                    if not plot_validation['valid']:
                        validation['errors'].extend([f"Plot {i+1}: {error}" for error in plot_validation['errors']])
                        validation['valid'] = False
                    validation['warnings'].extend([f"Plot {i+1}: {warning}" for warning in plot_validation['warnings']])
        
        # Validate export config
        if 'export' in config:
            export_config = config['export']
            if 'formats' in export_config:
                available_formats = self.export_service.get_export_formats()
                for format_type in export_config['formats']:
                    if format_type not in available_formats:
                        validation['errors'].append(f"Unsupported export format: {format_type}")
                        validation['valid'] = False
        
        return validation
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow capabilities."""
        return {
            'available_parsing_strategies': self.parse_service.get_available_strategies(),
            'available_plot_types': self.visualization_service.get_available_plot_types(),
            'available_themes': self.visualization_service.get_available_themes(),
            'available_export_formats': self.export_service.get_export_formats(),
            'processing_stats': self.processing_service.get_processing_stats(pd.DataFrame())
        } 