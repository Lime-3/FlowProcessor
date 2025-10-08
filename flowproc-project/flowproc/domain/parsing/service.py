"""
ParseService - Coordinates parsing operations using different strategies.
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from pathlib import Path
import logging

from ...core.exceptions import ParsingError
from ...core.protocols import ParserProtocol
from ...core.constants import DataType
from .strategies import ParsingStrategy
from .validators import DataValidator
from .csv_reader import CSVReader
from .column_detector import ColumnDetector
from .data_transformer import DataTransformer
from .data_type_detector import DataTypeDetector

logger = logging.getLogger(__name__)


class ParseService:
    """Service for coordinating parsing operations."""
    
    def __init__(self):
        self.csv_reader = CSVReader()
        self.column_detector = ColumnDetector()
        self.data_transformer = DataTransformer()
        self.validator = DataValidator()
        self.data_type_detector = DataTypeDetector()
        self.strategies: Dict[str, ParsingStrategy] = {}
        
    def register_strategy(self, name: str, strategy: ParsingStrategy) -> None:
        """Register a parsing strategy."""
        self.strategies[name] = strategy
        
    def parse_file(self, file_path: Path, strategy_name: str = "default") -> pd.DataFrame:
        """
        Parse a file using the specified strategy.
        
        Args:
            file_path: Path to file to parse
            strategy_name: Name of strategy to use (default, minimal, generic_lab, or auto)
            
        Returns:
            Parsed DataFrame
            
        Note:
            For backward compatibility, this method returns only the DataFrame.
            Use parse_file_with_type() to also get the detected data type.
        """
        df, _ = self.parse_file_with_type(file_path, strategy_name)
        return df
    
    def parse_file_with_type(self, file_path: Path, strategy_name: str = "default") -> Tuple[pd.DataFrame, DataType]:
        """
        Parse a file and return both DataFrame and detected data type.
        
        Args:
            file_path: Path to file to parse
            strategy_name: Name of strategy to use, or "auto" for automatic detection
            
        Returns:
            Tuple of (parsed DataFrame, detected DataType)
        """
        try:
            # Read the CSV file
            df = self.csv_reader.read(file_path)
            
            # Detect data type for auto-routing or logging
            data_type = self.data_type_detector.detect_data_type(df)
            logger.info(f"Detected data type: {data_type.value} for file: {file_path.name}")
            
            # Auto-select strategy based on data type if requested
            if strategy_name == "auto":
                if data_type == DataType.GENERIC_LAB:
                    strategy_name = "generic_lab"
                else:
                    strategy_name = "default"
                logger.info(f"Auto-selected strategy: {strategy_name}")
            
            # Detect columns
            columns = self.column_detector.detect_columns(df)
            
            # Get the parsing strategy
            strategy = self.strategies.get(strategy_name)
            if not strategy:
                raise ParsingError(f"Unknown parsing strategy: {strategy_name}")
            
            # Apply the strategy
            parsed_df = strategy.parse(df, columns)
            
            # Transform the data (pass data_type for conditional handling)
            transformed_df = self.data_transformer.transform(parsed_df, data_type=data_type)
            
            # Validate the result
            self.validator.validate(transformed_df)
            
            return transformed_df, data_type
            
        except Exception as e:
            raise ParsingError(f"Failed to parse file {file_path}: {str(e)}") from e
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available parsing strategies."""
        return list(self.strategies.keys())
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a file before parsing."""
        try:
            df = self.csv_reader.read(file_path)
            columns = self.column_detector.detect_columns(df)
            
            return {
                "valid": True,
                "columns": columns,
                "row_count": len(df),
                "column_count": len(df.columns)
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            } 