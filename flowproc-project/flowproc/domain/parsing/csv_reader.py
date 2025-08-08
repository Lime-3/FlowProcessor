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
        
        # Convert numeric columns to float, handling any trailing commas
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