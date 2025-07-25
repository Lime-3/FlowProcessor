"""
Data validation for parsed flow cytometry data.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from ...core.exceptions import ValidationError


class DataValidator:
    """Validates parsed flow cytometry data."""
    
    def __init__(self):
        self.required_columns = [
            'Sample_ID', 'Time', 'Group', 'Animal', 'Tissue', 'Well'
        ]
        self.numeric_columns = ['Time']
        
    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate the parsed dataframe."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            # Check for required columns
            self._validate_required_columns(df, validation_results)
            
            # Check data types
            self._validate_data_types(df, validation_results)
            
            # Check for missing values
            self._validate_missing_values(df, validation_results)
            
            # Check for duplicates
            self._validate_duplicates(df, validation_results)
            
            # Generate statistics
            self._generate_stats(df, validation_results)
            
            # Determine overall validity
            validation_results['valid'] = len(validation_results['errors']) == 0
            
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Validation failed: {str(e)}")
        
        return validation_results
    
    def _validate_required_columns(self, df: pd.DataFrame, results: Dict[str, Any]) -> None:
        """Validate that required columns are present."""
        missing_columns = []
        for col in self.required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            results['errors'].append(f"Missing required columns: {missing_columns}")
    
    def _validate_data_types(self, df: pd.DataFrame, results: Dict[str, Any]) -> None:
        """Validate data types of columns."""
        for col in self.numeric_columns:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    results['warnings'].append(f"Column {col} should be numeric but is {df[col].dtype}")
    
    def _validate_missing_values(self, df: pd.DataFrame, results: Dict[str, Any]) -> None:
        """Check for missing values in important columns."""
        for col in self.required_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    results['warnings'].append(f"Column {col} has {missing_count} missing values")
    
    def _validate_duplicates(self, df: pd.DataFrame, results: Dict[str, Any]) -> None:
        """Check for duplicate rows."""
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            results['warnings'].append(f"Found {duplicate_count} duplicate rows")
    
    def _generate_stats(self, df: pd.DataFrame, results: Dict[str, Any]) -> None:
        """Generate basic statistics about the data."""
        results['stats'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'column_info': {}
        }
        
        for col in df.columns:
            results['stats']['column_info'][col] = {
                'dtype': str(df[col].dtype),
                'non_null_count': df[col].count(),
                'unique_count': df[col].nunique()
            }
    
    def validate_sample_ids(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate sample ID format and consistency."""
        if 'Sample_ID' not in df.columns:
            return {'valid': False, 'error': 'Sample_ID column not found'}
        
        sample_ids = df['Sample_ID'].dropna()
        validation = {
            'valid': True,
            'errors': [],
            'unique_samples': sample_ids.nunique(),
            'sample_patterns': {}
        }
        
        # Check for empty sample IDs
        empty_samples = sample_ids[sample_ids == ''].count()
        if empty_samples > 0:
            validation['errors'].append(f"Found {empty_samples} empty sample IDs")
            validation['valid'] = False
        
        # Check for common patterns
        patterns = sample_ids.value_counts().head(10)
        validation['sample_patterns'] = patterns.to_dict()
        
        return validation
    
    def validate_time_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate time column consistency."""
        if 'Time' not in df.columns:
            return {'valid': False, 'error': 'Time column not found'}
        
        time_col = df['Time'].dropna()
        validation = {
            'valid': True,
            'errors': [],
            'min_time': time_col.min() if len(time_col) > 0 else None,
            'max_time': time_col.max() if len(time_col) > 0 else None,
            'time_range': None
        }
        
        if len(time_col) > 0:
            validation['time_range'] = validation['max_time'] - validation['min_time']
            
            # Check for negative times
            negative_times = (time_col < 0).sum()
            if negative_times > 0:
                validation['errors'].append(f"Found {negative_times} negative time values")
                validation['valid'] = False
        
        return validation 