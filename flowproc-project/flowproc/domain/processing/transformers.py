"""
Data transformation functionality for flow cytometry data processing.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """Handles data transformations for flow cytometry data."""
    
    def __init__(self):
        """Initialize the transformer."""
        self.scalers = {}
        
    def transform(self, df: pd.DataFrame, options: Dict[str, Any]) -> pd.DataFrame:
        """
        Transform data according to specified options.
        
        Args:
            df: Input DataFrame
            options: Transformation options
            
        Returns:
            Transformed DataFrame
        """
        result_df = df.copy()
        
        # Apply normalization if specified
        if options.get('normalize', False):
            result_df = self._normalize_data(result_df, options.get('normalization_method', 'standard'))
        
        # Apply log transformation if specified
        if options.get('log_transform', False):
            result_df = self._log_transform(result_df, options.get('log_columns', []))
        
        # Apply scaling if specified
        if options.get('scale', False):
            result_df = self._scale_data(result_df, options.get('scale_method', 'standard'))
        
        # Apply filtering if specified
        if options.get('filter', False):
            result_df = self._filter_data(result_df, options.get('filter_criteria', {}))
        
        # Apply column selection if specified
        if options.get('select_columns', False):
            columns = options.get('columns', [])
            if columns:
                result_df = self._select_columns(result_df, columns)
        
        return result_df
    
    def _normalize_data(self, df: pd.DataFrame, method: str = 'standard') -> pd.DataFrame:
        """Normalize numeric data using specified method."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        elif method == 'robust':
            scaler = RobustScaler()
        else:
            logger.warning(f"Unknown normalization method: {method}")
            return df
        
        # Fit and transform numeric columns
        if len(numeric_cols) > 0:
            df_normalized = df.copy()
            df_normalized[numeric_cols] = scaler.fit_transform(df[numeric_cols])
            return df_normalized
        
        return df
    
    def _log_transform(self, df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """Apply log transformation to specified columns."""
        if columns is None:
            # Apply to all numeric columns
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        result_df = df.copy()
        
        for col in columns:
            if col in df.columns and df[col].dtype in ['float64', 'int64']:
                # Add small constant to avoid log(0)
                min_val = df[col].min()
                if min_val <= 0:
                    offset = abs(min_val) + 1e-10
                    result_df[col] = np.log(df[col] + offset)
                else:
                    result_df[col] = np.log(df[col])
        
        return result_df
    
    def _scale_data(self, df: pd.DataFrame, method: str = 'standard') -> pd.DataFrame:
        """Scale data using specified method."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        elif method == 'robust':
            scaler = RobustScaler()
        else:
            logger.warning(f"Unknown scaling method: {method}")
            return df
        
        # Store scaler for potential inverse transformation
        self.scalers[method] = scaler
        
        # Fit and transform numeric columns
        if len(numeric_cols) > 0:
            df_scaled = df.copy()
            df_scaled[numeric_cols] = scaler.fit_transform(df[numeric_cols])
            return df_scaled
        
        return df
    
    def _filter_data(self, df: pd.DataFrame, criteria: Dict[str, Any]) -> pd.DataFrame:
        """Filter data based on specified criteria."""
        result_df = df.copy()
        
        for col, condition in criteria.items():
            if col in df.columns:
                if isinstance(condition, dict):
                    # Range filtering
                    if 'min' in condition:
                        result_df = result_df[result_df[col] >= condition['min']]
                    if 'max' in condition:
                        result_df = result_df[result_df[col] <= condition['max']]
                elif isinstance(condition, list):
                    # Value filtering
                    result_df = result_df[result_df[col].isin(condition)]
                elif isinstance(condition, str):
                    # String filtering
                    result_df = result_df[result_df[col].str.contains(condition, na=False)]
        
        return result_df
    
    def _select_columns(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Select specific columns from the dataframe."""
        valid_columns = [col for col in columns if col in df.columns]
        if valid_columns:
            return df[valid_columns]
        else:
            logger.warning("No valid columns found for selection")
            return df
    
    def inverse_transform(self, df: pd.DataFrame, method: str = 'standard') -> pd.DataFrame:
        """Apply inverse transformation using stored scaler."""
        if method not in self.scalers:
            logger.warning(f"No scaler found for method: {method}")
            return df
        
        scaler = self.scalers[method]
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            df_inverse = df.copy()
            df_inverse[numeric_cols] = scaler.inverse_transform(df[numeric_cols])
            return df_inverse
        
        return df
    
    def get_transformation_info(self) -> Dict[str, Any]:
        """Get information about available transformations."""
        return {
            'available_scalers': list(self.scalers.keys()),
            'transformation_methods': {
                'normalization': ['standard', 'minmax', 'robust'],
                'scaling': ['standard', 'minmax', 'robust'],
                'log_transform': 'applied to numeric columns',
                'filtering': 'based on criteria dictionary',
                'column_selection': 'based on column list'
            }
        } 