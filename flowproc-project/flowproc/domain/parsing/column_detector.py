"""Detect and identify column types in flow cytometry data."""
from typing import Optional, Dict, List, Set
import pandas as pd
import re
import logging

from ...core.exceptions import ParsingError
from ...core.constants import is_pure_metric_column

logger = logging.getLogger(__name__)


class ColumnDetector:
    """Detects column types and sample ID column."""
    
    # Patterns for sample ID detection
    ID_PATTERNS = [
        r'\d+\.\d+',  # Group.Animal pattern
        r'\.fcs$',     # FCS file extension
        r'^[A-Z]{2,3}_',  # Tissue prefix
        r'_[A-H]\d{1,2}_',  # Well pattern
    ]
    
    # Keywords for metric detection
    METRIC_KEYWORDS = {
        'count': 'count',
        'freq': 'frequency',
        'median': 'median',
        'mean': 'mean',
        'cv': 'cv',
        'sd': 'standard deviation',
        'geomean': 'geometric mean',
    }
    
    def __init__(self):
        """Initialize column detector."""
        self._cache: Dict[str, str] = {}
        
    def detect_sample_id_column(self, df: pd.DataFrame) -> str:
        """
        Detect which column contains sample IDs.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Name of sample ID column
            
        Raises:
            ParseError: If no sample ID column found
        """
        candidates = []
        
        # First try columns with 'sample' or 'id' in name
        for col in df.columns:
            col_lower = col.lower()
            if 'sample' in col_lower or 'id' in col_lower or col == 'Unnamed: 0':
                candidates.append((col, self._score_id_column(df[col])))
                
        # If no candidates, try all string columns
        if not candidates:
            for col in df.select_dtypes(include=['object']).columns:
                score = self._score_id_column(df[col])
                if score > 0:
                    candidates.append((col, score))
                    
        if not candidates:
            raise ParsingError("No sample ID column detected")
            
        # Return column with highest score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
        
    def _score_id_column(self, series: pd.Series) -> float:
        """Score a column for likelihood of being sample IDs."""
        if series.empty:
            return 0.0
            
        non_null = series.dropna().astype(str)
        if non_null.empty:
            return 0.0
            
        # Check pattern matches
        pattern_score = 0.0
        for pattern in self.ID_PATTERNS:
            matches = non_null.str.contains(pattern, regex=True, na=False).sum()
            pattern_score += matches / len(non_null)
            
        # Check uniqueness
        uniqueness_score = len(non_null.unique()) / len(non_null)
        
        # Combined score
        return pattern_score + uniqueness_score
        
    def detect_metric_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Detect and categorize metric columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary mapping metric types to column names
        """
        metric_map: Dict[str, List[str]] = {
            metric: [] for metric in self.METRIC_KEYWORDS
        }
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Skip metadata columns
            if col_lower in ['sampleid', 'group', 'animal', 'well', 'time', 'replicate']:
                continue
                
            # Check for metric keywords
            for keyword, metric_type in self.METRIC_KEYWORDS.items():
                if keyword in col_lower:
                    # Check if this is a pure metric column (not a subpopulation)
                    if is_pure_metric_column(col, keyword):
                        metric_map[keyword].append(col)
                    break
                    
        return {k: v for k, v in metric_map.items() if v}
        
    def detect_metadata_columns(self, df: pd.DataFrame) -> Set[str]:
        """
        Detect metadata columns (non-metric columns).
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Set of metadata column names
        """
        metadata = set()
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Check common metadata patterns
            if any(pattern in col_lower for pattern in 
                   ['sample', 'id', 'group', 'animal', 'well', 'time', 'replicate', 'tissue']):
                metadata.add(col)
                
        return metadata