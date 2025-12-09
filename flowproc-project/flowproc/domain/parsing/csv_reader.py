"""CSV file reading with robust error handling."""
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import logging

from ...core.exceptions import ParsingError as ParseError

logger = logging.getLogger(__name__)


class CSVReader:
    """Handles CSV file reading with various encodings and formats."""
    
    SUPPORTED_ENCODINGS = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    def __init__(self, skip_rows: Optional[List[int]] = None, 
                 remove_empty_rows: bool = True):
        """
        Initialize CSV reader.
        
        Args:
            skip_rows: Row indices to skip
            remove_empty_rows: Whether to remove empty rows
        """
        self.skip_rows = skip_rows or []
        self.remove_empty_rows = remove_empty_rows
        
    def read(self, file_path: Path) -> pd.DataFrame:
        """
        Read CSV file with automatic encoding detection.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with raw data
            
        Raises:
            ParseError: If file cannot be read
        """
        if not file_path.exists():
            raise ParseError(f"File not found: {file_path}")
            
        # Try different encodings
        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    skipinitialspace=True,
                    skip_blank_lines=True,
                    engine='python',
                    index_col=False  # Don't use first unnamed column as index
                )
                
                # If first column is unnamed, give it a name
                if df.columns[0] == 'Unnamed: 0' or df.columns[0] == '':
                    df = df.rename(columns={df.columns[0]: 'Sample'})
                
                logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                
                # Clean up the data
                df = self._clean_dataframe(df)
                return df
                
            except (UnicodeDecodeError, pd.errors.ParserError) as e:
                logger.debug(f"Failed to read with {encoding}: {e}")
                continue
                
        raise ParseError(f"Could not read {file_path} with any supported encoding")
        
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean up raw DataFrame."""
        # Remove completely empty rows and columns
        if self.remove_empty_rows:
            df = df.dropna(how='all', axis=0)  # Remove empty rows
            df = df.dropna(how='all', axis=1)  # Remove empty columns
            
        # Remove footer rows (Mean, SD, etc.)
        footer_patterns = ['mean', 'sd', 'average', 'stddev', 'total']
        first_col = df.iloc[:, 0].astype(str).str.lower()
        
        footer_mask = first_col.str.contains('|'.join(footer_patterns), na=False)
        if footer_mask.any():
            df = df[~footer_mask]
            logger.debug(f"Removed {footer_mask.sum()} footer rows")
            
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
        
        # Check object columns for text markers before attempting numeric conversion
        object_cols = df.select_dtypes(include=['object']).columns
        for col in object_cols:
            # Skip metadata columns - they should remain as text
            if col.lower() in ['sampleid', 'sample', 'tissue', 'well', 'group', 'animal', 'replicate', 'timepoint', 'time']:
                continue
                
            # Check if column has text markers that should be preserved
            if self._has_text_markers(df[col]):
                logger.debug(f"Preserving text markers in column '{col}'")
                continue
            
            # Try to convert to numeric if no text markers found
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                logger.warning(f"Failed to convert column {col} to numeric: {e}")
        
        # Convert already numeric columns to float, handling any trailing commas
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            try:
                df[col] = pd.to_numeric(df[col].astype(str).str.rstrip(','), errors='coerce')
            except Exception as e:
                logger.warning(f"Failed to convert column {col} to numeric: {e}")
        
        # Extract group from sample names if Group column doesn't exist
        if 'Sample' in df.columns and 'Group' not in df.columns:
            from .group_animal_parser import extract_group_animal
            df['Group'] = df['Sample'].apply(lambda x: f"Group {extract_group_animal(x).group}" if extract_group_animal(x) else "Unknown")
            
        return df
    
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