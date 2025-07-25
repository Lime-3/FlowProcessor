"""Transform parsed data into structured DataFrame."""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

from .sample_id_parser import SampleIDParser, ParsedSampleID
from .column_detector import ColumnDetector
from ...core.exceptions import ParsingError as ParseError, ValidationError

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
        
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw DataFrame into structured format.
        
        Args:
            df: Raw DataFrame from CSV
            
        Returns:
            Transformed DataFrame with parsed columns
            
        Raises:
            ParseError: If transformation fails
        """
        if df.empty:
            raise ParseError("Cannot transform empty DataFrame")
            
        # Detect sample ID column
        sid_col = self.column_detector.detect_sample_id_column(df)
        logger.info(f"Detected sample ID column: {sid_col}")
        
        # Rename to standard name
        df = df.rename(columns={sid_col: 'SampleID'})
        
        # Parse sample IDs
        parsed_data = self._parse_sample_ids(df['SampleID'])
        
        # Add parsed columns
        df = self._add_parsed_columns(df, parsed_data)
        
        # Clean up
        df = self._cleanup_dataframe(df)
        
        # Validate
        self._validate_transformed_data(df)
        
        return df
        
    def _parse_sample_ids(self, sample_ids: pd.Series) -> List[Optional[ParsedSampleID]]:
        """Parse all sample IDs."""
        parsed_data = []
        
        # Check for negative values first
        import re
        for sid in sample_ids:
            if isinstance(sid, str) and re.search(r'(_-\d+\.|\.-\d+)', sid):
                raise ValueError("Invalid group/animal")
        
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
        df['Group'] = pd.to_numeric(df['Group'], errors='coerce')
        df['Animal'] = pd.to_numeric(df['Animal'], errors='coerce')
        
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
            
        # Convert numeric columns
        numeric_cols = df.select_dtypes(include=['object']).columns
        for col in numeric_cols:
            if col not in ['SampleID', 'Tissue', 'Well']:
                # Try to convert to numeric
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
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