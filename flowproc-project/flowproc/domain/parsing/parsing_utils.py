from pathlib import Path
from typing import Optional, NamedTuple, Tuple
import pandas as pd
import logging
from .csv_reader import CSVReader
from .column_detector import ColumnDetector
from .data_transformer import DataTransformer
from .validation_service import validate_parsing_output
from .data_type_detector import DataTypeDetector
from .generic_lab_strategy import GenericLabParsingStrategy
from .strategies import DefaultParsingStrategy
from ...core.constants import DataType

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
    """
    Load and parse a CSV file, returning the DataFrame and detected sample ID column.
    
    Note:
        For backward compatibility, this returns only (df, sid_col).
        Use load_and_parse_df_with_type() to also get the detected data type.
    """
    df, sid_col, _ = load_and_parse_df_with_type(file_path)
    return df, sid_col


def load_and_parse_df_with_type(file_path: Path) -> Tuple[pd.DataFrame, str, DataType]:
    """
    Load and parse a CSV file, returning DataFrame, sample ID column, and detected data type.
    
    Returns:
        Tuple of (DataFrame, sample_id_column, DataType)
    """
    logger.info(f"Loading file: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Input file '{file_path}' does not exist")
    
    try:
        reader = CSVReader()
        detector = ColumnDetector()
        data_type_detector = DataTypeDetector()
        transformer = DataTransformer()
        
        df = reader.read(file_path)
        
        if df.empty:
            logger.warning("Empty DataFrame after loading")
            return df, "SampleID", DataType.FLOW_CYTOMETRY
        
        # Detect data type first
        data_type = data_type_detector.detect_data_type(df)
        logger.info(f"Detected data type: {data_type.value}")
        
        # Apply appropriate parsing strategy based on data type
        if data_type == DataType.GENERIC_LAB:
            # Use generic lab parsing strategy
            strategy = GenericLabParsingStrategy()
            df = strategy.parse(df)
            sid_col = 'SampleID'
        else:
            # Use default flow cytometry parsing
            # Find sample ID column
            sid_col = detector.detect_sample_id_column(df)
            
            # Rename to standard name
            df = df.rename(columns={sid_col: 'SampleID'})
            sid_col = 'SampleID'
        
        # Transform the data (pass data_type for conditional handling)
        df = transformer.transform(df, file_path, data_type=data_type)
        
        # Validate the parsed data
        validate_parsed_data(df, sid_col)
        
        return df, sid_col, data_type
        
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        raise


def is_likely_id_column(series: pd.Series) -> bool:
    """Return True if the series is likely a sample ID column."""
    detector = ColumnDetector()
    return detector._score_id_column(series) > 2.0 