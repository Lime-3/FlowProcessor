from pathlib import Path
from typing import Optional, NamedTuple, Tuple
import pandas as pd
import logging
from .csv_reader import CSVReader
from .column_detector import ColumnDetector
from .data_transformer import DataTransformer

logger = logging.getLogger(__name__)


class ParsedID(NamedTuple):
    """Parsed ID data for test compatibility."""
    well: str
    group: int
    animal: int
    time: Optional[float] = None


def validate_parsed_data(df: pd.DataFrame, sid_col: str) -> None:
    """Validate parsed DataFrame."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected DataFrame, got {type(df)}")
    
    required_cols = ['Well', 'Group', 'Animal']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Check for invalid values
    if (df['Group'] < 0).any() or (df['Animal'] < 0).any():
        raise ValueError("Invalid group/animal values (negative)")
    
    # Check for non-numeric values
    if not pd.to_numeric(df['Group'], errors='coerce').notna().all():
        raise ValueError("Non-numeric Group values found")
    if not pd.to_numeric(df['Animal'], errors='coerce').notna().all():
        raise ValueError("Non-numeric Animal values found")
    
    # Check time values if present
    if 'Time' in df.columns and (df['Time'].dropna() < 0).any():
        raise ValueError("Negative time values found")
    
    # Check for duplicate sample IDs (but allow if they have different replicates)
    if df[sid_col].duplicated().any():
        duplicates = df[sid_col][df[sid_col].duplicated()].unique()
        # Check if duplicates have different replicates
        for dup_id in duplicates:
            dup_rows = df[df[sid_col] == dup_id]
            if 'Replicate' in df.columns:
                replicate_values = dup_rows['Replicate'].dropna().unique()
                if len(replicate_values) > 1:
                    # This is valid - same sample ID with different replicates
                    continue
            # If no replicate column or same replicate values, this is an error
            raise ValueError(f"Duplicate sample IDs found: {duplicates}")
    
    logger.debug("Validation passed")


def load_and_parse_df(file_path: Path) -> Tuple[pd.DataFrame, str]:
    """Load and parse a CSV file, returning the DataFrame and detected sample ID column."""
    logger.info(f"Loading file: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Input file '{file_path}' does not exist")
    
    try:
        reader = CSVReader()
        detector = ColumnDetector()
        transformer = DataTransformer()
        
        df = reader.read(file_path)
        
        if df.empty:
            logger.warning("Empty DataFrame after loading")
            return df, "SampleID"
        
        # Find sample ID column
        sid_col = detector.detect_sample_id_column(df)
        
        # Rename to standard name
        df = df.rename(columns={sid_col: 'SampleID'})
        sid_col = 'SampleID'
        
        # Transform the data
        df = transformer.transform(df)
        
        # Validate the parsed data
        validate_parsed_data(df, sid_col)
        
        return df, sid_col
        
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        raise


def is_likely_id_column(series: pd.Series) -> bool:
    """Return True if the series is likely a sample ID column."""
    detector = ColumnDetector()
    return detector._score_id_column(series) > 2.0 