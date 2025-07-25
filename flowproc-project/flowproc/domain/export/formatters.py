"""
Data formatting functionality for export operations.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataFormatter:
    """Handles data formatting for export operations."""
    
    def __init__(self):
        """Initialize the formatter."""
        self.default_formats = {
            'datetime': '%Y-%m-%d %H:%M:%S',
            'date': '%Y-%m-%d',
            'time': '%H:%M:%S',
            'float': '{:.3f}',
            'integer': '{:.0f}',
            'percentage': '{:.2%}',
            'scientific': '{:.2e}'
        }
    
    def format_dataframe(self, df: pd.DataFrame, options: Dict[str, Any]) -> pd.DataFrame:
        """
        Format a DataFrame according to specified options.
        
        Args:
            df: Input DataFrame
            options: Formatting options
            
        Returns:
            Formatted DataFrame
        """
        result_df = df.copy()
        
        # Apply column formatting
        if 'column_formats' in options:
            result_df = self._format_columns(result_df, options['column_formats'])
        
        # Apply row formatting
        if 'row_formats' in options:
            result_df = self._format_rows(result_df, options['row_formats'])
        
        # Apply global formatting
        if 'global_formats' in options:
            result_df = self._apply_global_formats(result_df, options['global_formats'])
        
        # Apply custom formatting
        if 'custom_formats' in options:
            result_df = self._apply_custom_formats(result_df, options['custom_formats'])
        
        return result_df
    
    def _format_columns(self, df: pd.DataFrame, column_formats: Dict[str, Any]) -> pd.DataFrame:
        """Format specific columns."""
        for col, format_spec in column_formats.items():
            if col in df.columns:
                df[col] = self._format_column(df[col], format_spec)
        
        return df
    
    def _format_column(self, series: pd.Series, format_spec: Any) -> pd.Series:
        """Format a single column."""
        if isinstance(format_spec, str):
            # Use predefined format
            if format_spec in self.default_formats:
                return series.apply(lambda x: self.default_formats[format_spec].format(x) 
                                  if pd.notna(x) else x)
            else:
                # Custom format string
                return series.apply(lambda x: format_spec.format(x) if pd.notna(x) else x)
        
        elif isinstance(format_spec, dict):
            # Format specification dictionary
            format_type = format_spec.get('type', 'string')
            
            if format_type == 'datetime':
                return self._format_datetime(series, format_spec)
            elif format_type == 'number':
                return self._format_number(series, format_spec)
            elif format_type == 'string':
                return self._format_string(series, format_spec)
            elif format_type == 'custom':
                return self._format_custom(series, format_spec)
        
        return series
    
    def _format_datetime(self, series: pd.Series, format_spec: Dict[str, Any]) -> pd.Series:
        """Format datetime column."""
        date_format = format_spec.get('format', self.default_formats['datetime'])
        
        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(series):
            series = pd.to_datetime(series, errors='coerce')
        
        # Format datetime
        return series.dt.strftime(date_format)
    
    def _format_number(self, series: pd.Series, format_spec: Dict[str, Any]) -> pd.Series:
        """Format numeric column."""
        if not pd.api.types.is_numeric_dtype(series):
            return series
        
        format_type = format_spec.get('format_type', 'float')
        precision = format_spec.get('precision', 3)
        thousands_separator = format_spec.get('thousands_separator', False)
        decimal_separator = format_spec.get('decimal_separator', '.')
        
        if format_type == 'float':
            format_str = f'{{:.{precision}f}}'
        elif format_type == 'integer':
            format_str = '{:.0f}'
        elif format_type == 'percentage':
            format_str = f'{{:.{precision}%}}'
        elif format_type == 'scientific':
            format_str = f'{{:.{precision}e}}'
        else:
            format_str = f'{{:.{precision}f}}'
        
        # Apply formatting
        formatted = series.apply(lambda x: format_str.format(x) if pd.notna(x) else x)
        
        # Apply separators if needed
        if thousands_separator:
            formatted = formatted.apply(lambda x: self._add_thousands_separator(x, decimal_separator) 
                                      if isinstance(x, str) else x)
        
        return formatted
    
    def _format_string(self, series: pd.Series, format_spec: Dict[str, Any]) -> pd.Series:
        """Format string column."""
        case = format_spec.get('case', 'none')
        max_length = format_spec.get('max_length')
        prefix = format_spec.get('prefix', '')
        suffix = format_spec.get('suffix', '')
        
        result = series.astype(str)
        
        # Apply case transformation
        if case == 'upper':
            result = result.str.upper()
        elif case == 'lower':
            result = result.str.lower()
        elif case == 'title':
            result = result.str.title()
        
        # Apply length limit
        if max_length:
            result = result.str[:max_length]
        
        # Apply prefix and suffix
        if prefix:
            result = prefix + result
        if suffix:
            result = result + suffix
        
        return result
    
    def _format_custom(self, series: pd.Series, format_spec: Dict[str, Any]) -> pd.Series:
        """Apply custom formatting function."""
        custom_func = format_spec.get('function')
        if callable(custom_func):
            return series.apply(custom_func)
        return series
    
    def _format_rows(self, df: pd.DataFrame, row_formats: Dict[str, Any]) -> pd.DataFrame:
        """Format specific rows."""
        # This is a placeholder for row-level formatting
        # Implementation would depend on specific requirements
        return df
    
    def _apply_global_formats(self, df: pd.DataFrame, global_formats: Dict[str, Any]) -> pd.DataFrame:
        """Apply global formatting rules."""
        # Format all numeric columns
        if global_formats.get('format_numeric', False):
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            precision = global_formats.get('numeric_precision', 3)
            
            for col in numeric_cols:
                df[col] = df[col].apply(lambda x: f'{x:.{precision}f}' if pd.notna(x) else x)
        
        # Format all datetime columns
        if global_formats.get('format_datetime', False):
            datetime_cols = df.select_dtypes(include=['datetime64']).columns
            date_format = global_formats.get('datetime_format', self.default_formats['datetime'])
            
            for col in datetime_cols:
                df[col] = df[col].dt.strftime(date_format)
        
        # Apply case formatting to string columns
        case_format = global_formats.get('string_case')
        if case_format:
            string_cols = df.select_dtypes(include=['object']).columns
            for col in string_cols:
                if case_format == 'upper':
                    df[col] = df[col].str.upper()
                elif case_format == 'lower':
                    df[col] = df[col].str.lower()
                elif case_format == 'title':
                    df[col] = df[col].str.title()
        
        return df
    
    def _apply_custom_formats(self, df: pd.DataFrame, custom_formats: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply custom formatting rules."""
        for format_rule in custom_formats:
            condition = format_rule.get('condition')
            action = format_rule.get('action')
            
            if callable(condition) and callable(action):
                mask = condition(df)
                df.loc[mask] = action(df.loc[mask])
        
        return df
    
    def _add_thousands_separator(self, value: str, decimal_separator: str) -> str:
        """Add thousands separator to a formatted number string."""
        if '.' in value:
            parts = value.split('.')
            integer_part = parts[0]
            decimal_part = parts[1]
        else:
            integer_part = value
            decimal_part = ''
        
        # Add thousands separator
        if len(integer_part) > 3:
            integer_part = ','.join([integer_part[i:i+3] for i in range(0, len(integer_part), 3)])
        
        # Reconstruct with decimal separator
        if decimal_part:
            return f"{integer_part}{decimal_separator}{decimal_part}"
        else:
            return integer_part
    
    def get_available_formats(self) -> Dict[str, List[str]]:
        """Get list of available formatting options."""
        return {
            'predefined_formats': list(self.default_formats.keys()),
            'format_types': ['datetime', 'number', 'string', 'custom'],
            'number_formats': ['float', 'integer', 'percentage', 'scientific'],
            'case_formats': ['none', 'upper', 'lower', 'title']
        }
    
    def create_format_template(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create a formatting template based on DataFrame structure."""
        template = {
            'column_formats': {},
            'global_formats': {
                'format_numeric': True,
                'numeric_precision': 3,
                'format_datetime': True,
                'datetime_format': self.default_formats['datetime']
            }
        }
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                template['column_formats'][col] = {
                    'type': 'number',
                    'format_type': 'float',
                    'precision': 3
                }
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                template['column_formats'][col] = {
                    'type': 'datetime',
                    'format': self.default_formats['datetime']
                }
            else:
                template['column_formats'][col] = {
                    'type': 'string',
                    'case': 'none'
                }
        
        return template 