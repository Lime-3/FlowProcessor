"""
ParseService - Coordinates parsing operations using different strategies.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from pathlib import Path

from ...core.exceptions import ParsingError
from ...core.protocols import ParserProtocol
from .strategies import ParsingStrategy
from .validators import DataValidator
from .csv_reader import CSVReader
from .column_detector import ColumnDetector
from .data_transformer import DataTransformer


class ParseService:
    """Service for coordinating parsing operations."""
    
    def __init__(self):
        self.csv_reader = CSVReader()
        self.column_detector = ColumnDetector()
        self.data_transformer = DataTransformer()
        self.validator = DataValidator()
        self.strategies: Dict[str, ParsingStrategy] = {}
        
    def register_strategy(self, name: str, strategy: ParsingStrategy) -> None:
        """Register a parsing strategy."""
        self.strategies[name] = strategy
        
    def parse_file(self, file_path: Path, strategy_name: str = "default") -> pd.DataFrame:
        """Parse a file using the specified strategy."""
        try:
            # Read the CSV file
            df = self.csv_reader.read(file_path)
            
            # Detect columns
            columns = self.column_detector.detect_columns(df)
            
            # Get the parsing strategy
            strategy = self.strategies.get(strategy_name)
            if not strategy:
                raise ParsingError(f"Unknown parsing strategy: {strategy_name}")
            
            # Apply the strategy
            parsed_df = strategy.parse(df, columns)
            
            # Transform the data
            transformed_df = self.data_transformer.transform(parsed_df)
            
            # Validate the result
            self.validator.validate(transformed_df)
            
            return transformed_df
            
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