"""
Parsing strategies - Different approaches to parsing flow cytometry data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd

from ...core.protocols import ParserProtocol
from .sample_id_parser import SampleIDParser
from .group_animal_parser import GroupAnimalParser
from .well_parser import WellParser
from .tissue_parser import TissueParser
from .time_parser import TimeParser


class ParsingStrategy(ABC):
    """Abstract base class for parsing strategies."""
    
    @abstractmethod
    def parse(self, df: pd.DataFrame, columns: Dict[str, Any]) -> pd.DataFrame:
        """Parse the dataframe using this strategy."""
        pass


class DefaultParsingStrategy(ParsingStrategy):
    """Default parsing strategy that uses all available parsers."""
    
    def __init__(self):
        self.sample_parser = SampleIDParser()
        self.group_parser = GroupAnimalParser()
        self.well_parser = WellParser()
        self.tissue_parser = TissueParser()
        self.time_parser = TimeParser()
    
    def parse(self, df: pd.DataFrame, columns: Dict[str, Any]) -> pd.DataFrame:
        """Parse using all available parsers."""
        result_df = df.copy()
        
        # Apply each parser in sequence
        parsers = [
            self.sample_parser,
            self.group_parser,
            self.well_parser,
            self.tissue_parser,
            self.time_parser
        ]
        
        for parser in parsers:
            if hasattr(parser, 'parse') and callable(getattr(parser, 'parse')):
                try:
                    result_df = parser.parse(result_df, columns)
                except Exception as e:
                    # Log the error but continue with other parsers
                    print(f"Warning: Parser {parser.__class__.__name__} failed: {e}")
        
        return result_df


class MinimalParsingStrategy(ParsingStrategy):
    """Minimal parsing strategy that only applies essential parsers."""
    
    def __init__(self):
        self.sample_parser = SampleIDParser()
        self.time_parser = TimeParser()
    
    def parse(self, df: pd.DataFrame, columns: Dict[str, Any]) -> pd.DataFrame:
        """Parse using only essential parsers."""
        result_df = df.copy()
        
        # Apply only essential parsers
        parsers = [self.sample_parser, self.time_parser]
        
        for parser in parsers:
            if hasattr(parser, 'parse') and callable(getattr(parser, 'parse')):
                try:
                    result_df = parser.parse(result_df, columns)
                except Exception as e:
                    print(f"Warning: Parser {parser.__class__.__name__} failed: {e}")
        
        return result_df


class CustomParsingStrategy(ParsingStrategy):
    """Custom parsing strategy that allows selective parser application."""
    
    def __init__(self, parser_classes: List[type] = None):
        self.parsers = []
        if parser_classes:
            for parser_class in parser_classes:
                if issubclass(parser_class, ParserProtocol):
                    self.parsers.append(parser_class())
    
    def parse(self, df: pd.DataFrame, columns: Dict[str, Any]) -> pd.DataFrame:
        """Parse using the specified parsers."""
        result_df = df.copy()
        
        for parser in self.parsers:
            if hasattr(parser, 'parse') and callable(getattr(parser, 'parse')):
                try:
                    result_df = parser.parse(result_df, columns)
                except Exception as e:
                    print(f"Warning: Parser {parser.__class__.__name__} failed: {e}")
        
        return result_df 