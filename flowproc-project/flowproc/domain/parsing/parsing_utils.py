from pathlib import Path
from typing import Optional, NamedTuple, Tuple
import pandas as pd
import logging
from .csv_reader import CSVReader
from .column_detector import ColumnDetector
from .data_transformer import DataTransformer
from .validation_service import validate_parsing_output

logger = logging.getLogger(__name__)


class ParsedID(NamedTuple):
    """Parsed ID data for test compatibility."""
    well: str
    group: int
    animal: int
    time: Optional[float] = None


def validate_parsed_data(df: pd.DataFrame, sid_col: str) -> None:
    """Validate parsed DataFrame using the consolidated validation service."""
    validate_parsing_output(df, sid_col)


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
        df = transformer.transform(df, file_path)
        
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