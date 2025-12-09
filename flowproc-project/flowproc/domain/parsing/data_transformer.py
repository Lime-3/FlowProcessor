"""Transform parsed data into structured DataFrame."""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging
from pathlib import Path

from .sample_id_parser import SampleIDParser, ParsedSampleID
from .column_detector import ColumnDetector
from ...core.exceptions import ParsingError as ParseError, ValidationError
from ...core.constants import DataType

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms raw CSV data into structured DataFrame."""
    
    def __init__(self,
                 sample_parser: Optional[SampleIDParser] = None,
                 column_detector: Optional[ColumnDetector] = None):
        """
        Initialize data transformer.
        
        Args:
            sample_parser: Sample ID parser instance
            column_detector: Column detector instance
        """
        self.sample_parser = sample_parser or SampleIDParser()
        self.column_detector = column_detector or ColumnDetector()
        
    def transform(self, df: pd.DataFrame, file_path: Optional[Path] = None, 
                  data_type: Optional[DataType] = None) -> pd.DataFrame:
        """
        Transform raw DataFrame into structured format.
        
        Args:
            df: Raw DataFrame from CSV
            file_path: Optional path to the CSV file for extracting time information
            data_type: Optional data type for conditional processing
            
        Returns:
            Transformed DataFrame with parsed columns
            
        Raises:
            ParseError: If transformation fails
        """
        if df.empty:
            raise ParseError("Cannot transform empty DataFrame")
        
        # Default to FLOW_CYTOMETRY for backward compatibility
        if data_type is None:
            data_type = DataType.FLOW_CYTOMETRY
            
        # For GENERIC_LAB data, skip flow-specific transformations
        if data_type == DataType.GENERIC_LAB:
            logger.info("Skipping flow-specific transforms for GENERIC_LAB data")
            # Generic lab data should already have SampleID, Group, Animal, Time from strategy
            # Just do basic cleanup and validation
            df = self._cleanup_dataframe_generic(df)
            self._validate_transformed_data_generic(df)
            return df
        
        # Flow cytometry processing (original logic)
        # Detect sample ID column
        sid_col = self.column_detector.detect_sample_id_column(df)
        logger.info(f"Detected sample ID column: {sid_col}")
        
        # Rename to standard name
        df = df.rename(columns={sid_col: 'SampleID'})
        
        # Parse sample IDs
        parsed_data = self._parse_sample_ids(df['SampleID'])
        
        # Add parsed columns
        df = self._add_parsed_columns(df, parsed_data)
        
        # Extract time information from filename if available
        if file_path:
            df = self._extract_time_from_filename(df, file_path)
        
        # Clean up
        df = self._cleanup_dataframe(df)
        
        # Validate
        self._validate_transformed_data(df)
        
        return df
        
    def _parse_sample_ids(self, sample_ids: pd.Series) -> List[Optional[ParsedSampleID]]:
        """Parse all sample IDs."""
        parsed_data = []
        
        # Check for negative values first
        from .validation_utils import validate_sample_id_for_negative_values
        
        for sid in sample_ids:
            if isinstance(sid, str):
                validate_sample_id_for_negative_values(sid, strict=True)
        
        for idx, sid in enumerate(sample_ids):
            try:
                parsed = self.sample_parser.parse(str(sid))
                parsed_data.append(parsed)
                
                if parsed is None:
                    logger.warning(f"Failed to parse sample ID at row {idx}: {sid}")
                    
            except ValueError as e:
                # Re-raise ValueError for invalid group/animal patterns
                if "Invalid group/animal" in str(e):
                    raise e
                logger.error(f"Error parsing sample ID at row {idx}: {e}")
                parsed_data.append(None)
            except Exception as e:
                logger.error(f"Error parsing sample ID at row {idx}: {e}")
                parsed_data.append(None)
                
        return parsed_data
        
    def _add_parsed_columns(self, df: pd.DataFrame, 
                           parsed_data: List[Optional[ParsedSampleID]]) -> pd.DataFrame:
        """Add parsed columns to DataFrame."""
        # Initialize columns with appropriate defaults
        df['Group'] = np.nan
        df['Animal'] = np.nan
        df['Tissue'] = 'UNK'
        df['Well'] = 'UNK'
        df['Time'] = np.nan
        
        # Fill in parsed data
        for idx, parsed in enumerate(parsed_data):
            if parsed is not None:
                df.at[idx, 'Group'] = parsed.group
                df.at[idx, 'Animal'] = parsed.animal
                df.at[idx, 'Tissue'] = parsed.tissue
                df.at[idx, 'Well'] = parsed.well
                
                if parsed.time_hours is not None:
                    df.at[idx, 'Time'] = parsed.time_hours
                    
        # Convert to appropriate types
        df['Group'] = pd.to_numeric(df['Group'], errors='coerce').astype('Int64')
        df['Animal'] = pd.to_numeric(df['Animal'], errors='coerce').astype('Int64')
        
        return df
        
    def _extract_time_from_filename(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        """Extract time information from filename and apply to all rows."""
        from .time_service import TimeService
        
        time_parser = TimeService()
        filename = file_path.name
        
        # Try to extract time from filename
        time_hours = time_parser.parse(filename)
        
        if time_hours is not None:
            logger.info(f"Extracted time {time_hours} hours from filename: {filename}")
            # Apply the time to all rows that don't already have time information
            mask = df['Time'].isna()
            df.loc[mask, 'Time'] = time_hours
        else:
            logger.debug(f"No time information found in filename: {filename}")
            
        return df
        
    def _cleanup_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean up transformed DataFrame."""
        # Check for duplicate sample IDs
        if df['SampleID'].duplicated().any():
            raise ValueError("Duplicate sample IDs found")
        
        # Remove rows where parsing completely failed
        df = df.dropna(subset=['Group', 'Animal'], how='all')
        
        if df.empty:
            raise ValueError("No valid sample ID column in the file")
            
        # Check for negative values
        if (df['Group'] < 0).any() or (df['Animal'] < 0).any():
            raise ValueError("Invalid group/animal numbers found")
            
        # Convert numeric columns (skip those with text markers)
        numeric_cols = df.select_dtypes(include=['object']).columns
        for col in numeric_cols:
            if col not in ['SampleID', 'Tissue', 'Well', 'Group', 'Animal', 'Replicate', 'Timepoint', 'Time']:
                # Check if column has text markers that should be preserved
                if self._has_text_markers(df[col]):
                    logger.debug(f"Preserving text markers in column '{col}' during cleanup")
                    continue
                
                # Try to convert to numeric if no text markers found
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    logger.warning(f"Failed to convert column {col} to numeric: {e}")
                
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
        
    def _validate_transformed_data(self, df: pd.DataFrame) -> None:
        """Validate transformed data."""
        # Check required columns
        required = ['SampleID', 'Group', 'Animal']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValidationError(f"Missing required columns: {missing}")
            
        # Check for all-null groups/animals
        if df['Group'].isna().all():
            raise ValidationError("All Group values are null")
            
        if df['Animal'].isna().all():
            raise ValidationError("All Animal values are null")
            
        # Warn about partial parsing failures
        null_groups = df['Group'].isna().sum()
        if null_groups > 0:
            logger.warning(
                f"{null_groups}/{len(df)} rows have null Group values"
            )
    
    def _cleanup_dataframe_generic(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean up DataFrame for generic lab data.
        
        Less strict than flow cytometry cleanup since lab data
        has simpler structure.
        """
        # Check for duplicate sample IDs
        if 'SampleID' in df.columns and df['SampleID'].duplicated().any():
            logger.warning("Duplicate sample IDs found in generic lab data")
        
        # Convert numeric columns (exclude metadata columns and those with text markers)
        metadata_cols = ['SampleID', 'Group', 'Animal', 'Replicate', 'Timepoint', 'Time', 'Tissue', 'Well']
        numeric_cols = [col for col in df.columns if col not in metadata_cols]
        
        for col in numeric_cols:
            if df[col].dtype == 'object':
                # Check if column has text markers that should be preserved
                if self._has_text_markers(df[col]):
                    logger.debug(f"Preserving text markers in column '{col}' during generic cleanup")
                    continue
                
                # Try to convert to numeric if no text markers found
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    logger.warning(f"Failed to convert column {col} to numeric: {e}")
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    
    def _validate_transformed_data_generic(self, df: pd.DataFrame) -> None:
        """
        Validate transformed generic lab data.
        
        Less strict requirements than flow cytometry data.
        """
        # Check required columns
        required = ['SampleID', 'Group']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValidationError(f"Missing required columns: {missing}")
        
        # Check for all-null groups
        if df['Group'].isna().all():
            raise ValidationError("All Group values are null")
        
        # Warn about partial parsing failures
        null_groups = df['Group'].isna().sum()
        if null_groups > 0:
            logger.warning(
                f"{null_groups}/{len(df)} rows have null Group values in generic lab data"
            )
    
    def _has_text_markers(self, series: pd.Series) -> bool:
        """
        Check if a column contains text markers that should be preserved.
        
        Args:
            series: pandas Series to check
            
        Returns:
            True if column contains text markers that should remain as text
        """
        if series.empty:
            return False
            
        # Convert to string and drop NaN values
        string_values = series.astype(str).dropna()
        if string_values.empty:
            return False
        
        # Check for common text markers
        text_markers = [
            r'\*',  # Asterisk prefix (like *4.51) - escaped for regex
            'OOR',  # Out of range markers
            r'<',  # Less than markers
            r'>',  # Greater than markers
            'ND',  # Not detected
            'LOD',  # Limit of detection
            'BLQ',  # Below limit of quantification
        ]
        
        # Check if any values contain these markers
        for marker in text_markers:
            if string_values.str.contains(marker, na=False, regex=True).any():
                logger.debug(f"Found text marker '{marker}' in column")
                return True
        
        # Check for values that start with asterisk (common pattern)
        if string_values.str.startswith('*').any():
            logger.debug("Found asterisk prefix in column")
            return True
            
        # Check for values that contain range markers
        range_patterns = [r'<', r'>', '≤', '≥']
        for pattern in range_patterns:
            if string_values.str.contains(pattern, na=False, regex=True).any():
                logger.debug(f"Found range marker '{pattern}' in column")
                return True
        
        return False