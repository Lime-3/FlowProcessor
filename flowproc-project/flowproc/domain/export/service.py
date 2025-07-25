"""
ExportService - Coordinates export operations for flow cytometry data.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
from pathlib import Path
import logging

from ...core.exceptions import ExportError
from .excel_writer import ExcelWriter
from .formatters import DataFormatter

logger = logging.getLogger(__name__)


class ExportService:
    """Service for coordinating export operations."""
    
    def __init__(self):
        self.excel_writer = ExcelWriter()
        self.formatter = DataFormatter()
        
    def export_data(self, data: Union[pd.DataFrame, List[pd.DataFrame]], 
                   filepath: str, format: str = 'excel', 
                   config: Optional[Dict[str, Any]] = None) -> None:
        """
        Export data to the specified format.
        
        Args:
            data: DataFrame or list of DataFrames to export
            filepath: Output file path
            format: Export format ('excel', 'csv', 'json', 'parquet')
            config: Export configuration
        """
        try:
            if format == 'excel':
                self._export_to_excel(data, filepath, config or {})
            elif format == 'csv':
                self._export_to_csv(data, filepath, config or {})
            elif format == 'json':
                self._export_to_json(data, filepath, config or {})
            elif format == 'parquet':
                self._export_to_parquet(data, filepath, config or {})
            else:
                raise ExportError(f"Unsupported export format: {format}")
                
        except Exception as e:
            raise ExportError(f"Failed to export data: {str(e)}") from e
    
    def _export_to_excel(self, data: Union[pd.DataFrame, List[pd.DataFrame]], 
                        filepath: str, config: Dict[str, Any]) -> None:
        """Export data to Excel format."""
        if isinstance(data, pd.DataFrame):
            data = [data]
        
        # Format data if specified
        if config.get('format_data', False):
            data = [self.formatter.format_dataframe(df, config.get('format_options', {})) 
                   for df in data]
        
        # Export to Excel
        self.excel_writer.write_excel(
            dataframes=data,
            filepath=filepath,
            sheet_names=config.get('sheet_names', [f'Sheet{i+1}' for i in range(len(data))]),
            include_index=config.get('include_index', False),
            auto_adjust_columns=config.get('auto_adjust_columns', True)
        )
    
    def _export_to_csv(self, data: Union[pd.DataFrame, List[pd.DataFrame]], 
                      filepath: str, config: Dict[str, Any]) -> None:
        """Export data to CSV format."""
        if isinstance(data, list):
            if len(data) == 1:
                data = data[0]
            else:
                # For multiple dataframes, create separate files
                base_path = Path(filepath)
                for i, df in enumerate(data):
                    suffix = f"_{i+1}" if i > 0 else ""
                    csv_path = base_path.parent / f"{base_path.stem}{suffix}.csv"
                    self._export_single_csv(df, str(csv_path), config)
                return
        
        self._export_single_csv(data, filepath, config)
    
    def _export_single_csv(self, df: pd.DataFrame, filepath: str, config: Dict[str, Any]) -> None:
        """Export a single DataFrame to CSV."""
        # Format data if specified
        if config.get('format_data', False):
            df = self.formatter.format_dataframe(df, config.get('format_options', {}))
        
        # Export to CSV
        df.to_csv(
            filepath,
            index=config.get('include_index', False),
            encoding=config.get('encoding', 'utf-8'),
            sep=config.get('separator', ','),
            decimal=config.get('decimal', '.')
        )
    
    def _export_to_json(self, data: Union[pd.DataFrame, List[pd.DataFrame]], 
                       filepath: str, config: Dict[str, Any]) -> None:
        """Export data to JSON format."""
        if isinstance(data, list):
            if len(data) == 1:
                data = data[0]
            else:
                # For multiple dataframes, create a dictionary
                data_dict = {f'dataframe_{i+1}': df.to_dict('records') 
                           for i, df in enumerate(data)}
                data = data_dict
        
        # Format data if specified
        if config.get('format_data', False) and isinstance(data, pd.DataFrame):
            data = self.formatter.format_dataframe(data, config.get('format_options', {}))
        
        # Export to JSON
        if isinstance(data, pd.DataFrame):
            data.to_json(
                filepath,
                orient=config.get('orient', 'records'),
                indent=config.get('indent', 2),
                date_format=config.get('date_format', 'iso')
            )
        else:
            import json
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=config.get('indent', 2))
    
    def _export_to_parquet(self, data: Union[pd.DataFrame, List[pd.DataFrame]], 
                          filepath: str, config: Dict[str, Any]) -> None:
        """Export data to Parquet format."""
        if isinstance(data, list):
            if len(data) == 1:
                data = data[0]
            else:
                # For multiple dataframes, create separate files
                base_path = Path(filepath)
                for i, df in enumerate(data):
                    suffix = f"_{i+1}" if i > 0 else ""
                    parquet_path = base_path.parent / f"{base_path.stem}{suffix}.parquet"
                    self._export_single_parquet(df, str(parquet_path), config)
                return
        
        self._export_single_parquet(data, filepath, config)
    
    def _export_single_parquet(self, df: pd.DataFrame, filepath: str, config: Dict[str, Any]) -> None:
        """Export a single DataFrame to Parquet."""
        # Format data if specified
        if config.get('format_data', False):
            df = self.formatter.format_dataframe(df, config.get('format_options', {}))
        
        # Export to Parquet
        df.to_parquet(
            filepath,
            index=config.get('include_index', False),
            compression=config.get('compression', 'snappy'),
            engine=config.get('engine', 'pyarrow')
        )
    
    def get_export_formats(self) -> List[str]:
        """Get list of available export formats."""
        return ['excel', 'csv', 'json', 'parquet']
    
    def validate_export_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate export configuration."""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for required fields based on format
        format = config.get('format', 'excel')
        
        if format == 'excel':
            if 'sheet_names' in config and not isinstance(config['sheet_names'], list):
                validation['errors'].append("sheet_names must be a list")
                validation['valid'] = False
        
        elif format == 'csv':
            if 'separator' in config and not isinstance(config['separator'], str):
                validation['errors'].append("separator must be a string")
                validation['valid'] = False
        
        elif format == 'json':
            if 'orient' in config and config['orient'] not in ['records', 'index', 'columns', 'split', 'table', 'values']:
                validation['warnings'].append(f"Unknown JSON orient: {config['orient']}")
        
        elif format == 'parquet':
            if 'compression' in config and config['compression'] not in ['snappy', 'gzip', 'brotli', 'lz4']:
                validation['warnings'].append(f"Unknown compression: {config['compression']}")
        
        return validation
    
    def get_export_info(self, data: Union[pd.DataFrame, List[pd.DataFrame]]) -> Dict[str, Any]:
        """Get information about the data to be exported."""
        if isinstance(data, pd.DataFrame):
            dataframes = [data]
        else:
            dataframes = data
        
        info = {
            'total_dataframes': len(dataframes),
            'dataframes_info': []
        }
        
        for i, df in enumerate(dataframes):
            df_info = {
                'index': i,
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': df.dtypes.to_dict(),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'null_counts': df.isnull().sum().to_dict()
            }
            info['dataframes_info'].append(df_info)
        
        return info 