"""
Comprehensive validation service for parsed data.

This module consolidates validation logic from multiple locations into a single,
configurable validation service that can be used across the application.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def __bool__(self) -> bool:
        return self.is_valid


@dataclass
class ValidationConfig:
    """Configuration for validation operations."""
    # Required columns that must be present
    required_columns: List[str] = field(default_factory=lambda: ['Well', 'Group', 'Animal'])
    
    # Optional columns that should be validated if present
    optional_columns: List[str] = field(default_factory=lambda: ['Time', 'Replicate'])
    
    # Validation settings
    allow_empty_dataframe: bool = False
    allow_negative_values: bool = False
    allow_duplicate_samples: bool = False
    allow_non_numeric_groups: bool = False
    allow_non_numeric_animals: bool = False
    
    # Duplicate handling
    allow_duplicates_with_different_replicates: bool = True
    
    # Error handling
    raise_on_error: bool = True
    log_warnings: bool = True
    
    # Custom validation functions
    custom_validators: Dict[str, callable] = field(default_factory=dict)


def validate_dataframe_structure(df: pd.DataFrame, config: ValidationConfig) -> ValidationResult:
    """Validate basic DataFrame structure."""
    result = ValidationResult(is_valid=True)
    
    if not isinstance(df, pd.DataFrame):
        result.add_error(f"Expected DataFrame, got {type(df)}")
        return result
    
    if df.empty and not config.allow_empty_dataframe:
        result.add_error("Parsed DataFrame is empty")
        return result
    
    return result


def validate_required_columns(df: pd.DataFrame, config: ValidationConfig) -> ValidationResult:
    """Validate that required columns are present."""
    result = ValidationResult(is_valid=True)
    
    missing_cols = [col for col in config.required_columns if col not in df.columns]
    if missing_cols:
        result.add_error(f"Missing required columns: {missing_cols}")
    
    # Check for empty required columns
    empty_cols = []
    for col in config.required_columns:
        if col in df.columns and df[col].isna().all():
            empty_cols.append(col)
    
    if empty_cols:
        result.add_error(f"Required columns are empty: {empty_cols}")
    
    return result


def validate_numeric_values(df: pd.DataFrame, config: ValidationConfig) -> ValidationResult:
    """Validate numeric values in Group and Animal columns."""
    result = ValidationResult(is_valid=True)
    
    # Validate Group column
    if 'Group' in df.columns:
        if not config.allow_non_numeric_groups:
            if not pd.to_numeric(df['Group'], errors='coerce').notna().all():
                result.add_error("Non-numeric Group values found")
                return result  # Stop here if non-numeric values found
        
        if not config.allow_negative_values:
            # Convert to numeric first to avoid comparison errors
            numeric_group = pd.to_numeric(df['Group'], errors='coerce')
            if (numeric_group < 0).any():
                result.add_error("Invalid group values (negative)")
    
    # Validate Animal column
    if 'Animal' in df.columns:
        if not config.allow_non_numeric_animals:
            if not pd.to_numeric(df['Animal'], errors='coerce').notna().all():
                result.add_error("Non-numeric Animal values found")
                return result  # Stop here if non-numeric values found
        
        if not config.allow_negative_values:
            # Convert to numeric first to avoid comparison errors
            numeric_animal = pd.to_numeric(df['Animal'], errors='coerce')
            if (numeric_animal < 0).any():
                result.add_error("Invalid animal values (negative)")
    
    return result


def validate_time_values(df: pd.DataFrame, config: ValidationConfig) -> ValidationResult:
    """Validate time values if present."""
    result = ValidationResult(is_valid=True)
    
    if 'Time' in df.columns:
        time_data = df['Time'].dropna()
        if len(time_data) > 0:
            if not config.allow_negative_values:
                if (time_data < 0).any():
                    result.add_error("Negative time values found")
            
            # Check for non-numeric time values
            if not pd.to_numeric(time_data, errors='coerce').notna().all():
                result.add_error("Non-numeric time values found")
    
    return result


def validate_duplicate_samples(df: pd.DataFrame, sid_col: str, config: ValidationConfig) -> ValidationResult:
    """Validate for duplicate sample IDs."""
    result = ValidationResult(is_valid=True)
    
    if config.allow_duplicate_samples:
        return result
    
    if sid_col not in df.columns:
        result.add_warning(f"Sample ID column '{sid_col}' not found, skipping duplicate validation")
        return result
    
    if df[sid_col].duplicated().any():
        duplicates = df[sid_col][df[sid_col].duplicated()].unique()
        
        # Check if duplicates are allowed due to different replicates
        if config.allow_duplicates_with_different_replicates and 'Replicate' in df.columns:
            valid_duplicates = []
            for dup_id in duplicates:
                dup_rows = df[df[sid_col] == dup_id]
                replicate_values = dup_rows['Replicate'].dropna().unique()
                if len(replicate_values) <= 1:
                    valid_duplicates.append(dup_id)
            
            if valid_duplicates:
                result.add_error(f"Duplicate sample IDs found: {valid_duplicates}")
        else:
            result.add_error(f"Duplicate sample IDs found: {duplicates}")
    
    return result


def validate_parsed_data(
    df: pd.DataFrame, 
    sid_col: str = 'SampleID',
    config: Optional[ValidationConfig] = None
) -> Union[ValidationResult, None]:
    """
    Comprehensive validation of parsed DataFrame data.
    
    This function consolidates validation logic from multiple locations into a single,
    configurable validation service.
    
    Args:
        df: DataFrame to validate
        sid_col: Name of the sample ID column
        config: Validation configuration. If None, uses default configuration.
    
    Returns:
        ValidationResult if config.raise_on_error is False, None otherwise.
        Raises ValueError or TypeError if validation fails and config.raise_on_error is True.
    
    Raises:
        ValueError: If validation fails and raise_on_error is True
        TypeError: If input is not a DataFrame and raise_on_error is True
    """
    if config is None:
        config = ValidationConfig()
    
    # Run validation steps in order, stopping early on critical errors
    final_result = ValidationResult(is_valid=True)
    
    # Step 1: Validate DataFrame structure (critical - must pass first)
    structure_result = validate_dataframe_structure(df, config)
    final_result.errors.extend(structure_result.errors)
    final_result.warnings.extend(structure_result.warnings)
    if not structure_result.is_valid:
        final_result.is_valid = False
    else:
        # Step 2: Validate required columns
        columns_result = validate_required_columns(df, config)
        final_result.errors.extend(columns_result.errors)
        final_result.warnings.extend(columns_result.warnings)
        if not columns_result.is_valid:
            final_result.is_valid = False
        else:
            # Step 3: Validate numeric values
            numeric_result = validate_numeric_values(df, config)
            final_result.errors.extend(numeric_result.errors)
            final_result.warnings.extend(numeric_result.warnings)
            if not numeric_result.is_valid:
                final_result.is_valid = False
            else:
                # Step 4: Validate time values
                time_result = validate_time_values(df, config)
                final_result.errors.extend(time_result.errors)
                final_result.warnings.extend(time_result.warnings)
                if not time_result.is_valid:
                    final_result.is_valid = False
                else:
                    # Step 5: Validate duplicate samples
                    duplicate_result = validate_duplicate_samples(df, sid_col, config)
                    final_result.errors.extend(duplicate_result.errors)
                    final_result.warnings.extend(duplicate_result.warnings)
                    if not duplicate_result.is_valid:
                        final_result.is_valid = False
    
    # Log warnings if enabled
    if config.log_warnings and final_result.warnings:
        for warning in final_result.warnings:
            logger.warning(warning)
    
    # Handle errors based on configuration
    if not final_result.is_valid:
        if config.raise_on_error:
            error_msg = "; ".join(final_result.errors)
            raise ValueError(f"Validation failed: {error_msg}")
        else:
            return final_result
    
    # Log success
    logger.debug("Validation passed")
    
    # Return result if not raising on error
    if not config.raise_on_error:
        return final_result
    
    return None


# Convenience functions for specific validation scenarios

def validate_parsing_output(df: pd.DataFrame, sid_col: str = 'SampleID') -> None:
    """
    Validate parsed data with strict settings for parsing output.
    
    This is the equivalent of the original parsing_utils.py validation.
    """
    config = ValidationConfig(
        required_columns=['Well', 'Group', 'Animal'],
        allow_empty_dataframe=False,
        allow_negative_values=False,
        allow_duplicate_samples=False,
        allow_duplicates_with_different_replicates=True,
        raise_on_error=True
    )
    validate_parsed_data(df, sid_col, config)


def validate_persistence_input(df: pd.DataFrame, sid_col: str = 'SampleID') -> None:
    """
    Validate data with relaxed settings for persistence operations.
    
    This is the equivalent of the original data_io.py validation.
    """
    config = ValidationConfig(
        required_columns=['Group', 'Animal'],
        allow_empty_dataframe=False,
        allow_negative_values=True,  # More permissive for persistence
        allow_duplicate_samples=True,  # Allow duplicates in persistence
        raise_on_error=True
    )
    validate_parsed_data(df, sid_col, config)


def validate_with_result(df: pd.DataFrame, sid_col: str = 'SampleID', **config_kwargs) -> ValidationResult:
    """
    Validate data and return detailed result without raising exceptions.
    
    Args:
        df: DataFrame to validate
        sid_col: Name of the sample ID column
        **config_kwargs: Configuration overrides
    
    Returns:
        ValidationResult with detailed validation information
    """
    config = ValidationConfig(**config_kwargs)
    config.raise_on_error = False
    return validate_parsed_data(df, sid_col, config) 