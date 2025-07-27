# flowproc/validators.py
"""Data validation with clear error reporting."""
from typing import List, Set, Optional, Tuple
import pandas as pd
import numpy as np
import logging

from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class DataFrameValidator:
    """Validates flow cytometry DataFrames."""
    
    REQUIRED_COLUMNS = {'SampleID', 'Group', 'Animal'}
    NUMERIC_COLUMNS = {'Group', 'Animal', 'Replicate', 'Time'}
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with DataFrame to validate."""
        self.df = df
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validations.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()
        
        # Run validation checks
        self._check_required_columns()
        self._check_data_types()
        self._check_value_ranges()
        self._check_duplicates()
        self._check_group_consistency()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _check_required_columns(self) -> None:
        """Check for required columns."""
        missing = self.REQUIRED_COLUMNS - set(self.df.columns)
        if missing:
            self.errors.append(f"Missing required columns: {missing}")
            
    def _check_data_types(self) -> None:
        """Check column data types."""
        for col in self.NUMERIC_COLUMNS:
            if col not in self.df.columns:
                continue
                
            # Check if column can be converted to numeric
            non_numeric = self.df[col].apply(
                lambda x: not pd.isna(x) and not isinstance(x, (int, float, np.number))
            )
            
            if non_numeric.any():
                bad_values = self.df.loc[non_numeric, col].unique()[:5]
                self.errors.append(
                    f"Non-numeric values in {col}: {bad_values}"
                )
                
    def _check_value_ranges(self) -> None:
        """Check for invalid value ranges."""
        # Check for negative groups/animals
        for col in ['Group', 'Animal']:
            if col in self.df.columns:
                if (self.df[col] < 0).any():
                    self.errors.append(f"Negative values found in {col}")
                    
        # Check time values
        if 'Time' in self.df.columns:
            time_values = self.df['Time'].dropna()
            if (time_values < 0).any():
                self.errors.append("Negative time values found")
                
            # Warn about unusual time values
            if (time_values > 168).any():  # More than a week
                self.warnings.append(
                    "Time values exceed 168 hours (1 week)"
                )
                
    def _check_duplicates(self) -> None:
        """Check for duplicate sample IDs."""
        if 'SampleID' in self.df.columns:
            duplicates = self.df['SampleID'].duplicated()
            if duplicates.any():
                dup_ids = self.df.loc[duplicates, 'SampleID'].unique()[:5]
                self.errors.append(
                    f"Duplicate sample IDs found: {dup_ids}"
                )
                
    def _check_group_consistency(self) -> None:
        """Check for consistent group sizes."""
        if all(col in self.df.columns for col in ['Group', 'Animal']):
            group_sizes = self.df.groupby('Group')['Animal'].nunique()
            
            if len(group_sizes) > 1:
                min_size = group_sizes.min()
                max_size = group_sizes.max()
                
                if min_size != max_size:
                    self.warnings.append(
                        f"Inconsistent group sizes: {min_size}-{max_size} animals"
                    )
                    
                    # Show which groups are affected
                    for group, size in group_sizes.items():
                        if size != max_size:
                            self.warnings.append(
                                f"  Group {group}: {size} animals"
                            )


def validate_dataframe(df: pd.DataFrame, 
                      raise_on_error: bool = True) -> pd.DataFrame:
    """
    Validate a DataFrame and optionally raise on errors.
    
    Args:
        df: DataFrame to validate
        raise_on_error: Whether to raise ValidationError on errors
        
    Returns:
        The validated DataFrame
        
    Raises:
        ValidationError: If validation fails and raise_on_error is True
    """
    validator = DataFrameValidator(df)
    is_valid, errors, warnings = validator.validate()
    
    # Log warnings
    for warning in warnings:
        logger.warning(warning)
        
    # Handle errors
    if not is_valid:
        error_msg = "Validation failed:\n" + "\n".join(errors)
        
        if raise_on_error:
            raise ValidationError(error_msg, invalid_values=errors)
        else:
            logger.error(error_msg)
            
    return df