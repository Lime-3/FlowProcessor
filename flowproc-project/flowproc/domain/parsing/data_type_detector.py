"""
Data type detection for distinguishing flow cytometry from generic lab data.

This module implements conservative detection logic with a strong bias toward
flow cytometry to ensure backward compatibility.
"""

from typing import Dict, Set
import pandas as pd
import re
import logging

from ...core.constants import DataType

logger = logging.getLogger(__name__)


class DataTypeDetector:
    """
    Detects whether data is flow cytometry or generic lab data.
    
    Uses conservative detection with strong flow cytometry bias to maintain
    backward compatibility with existing files.
    """
    
    # Flow cytometry indicators (any one triggers FLOW_CYTOMETRY)
    FLOW_INDICATORS = {
        'fcs_extension': r'\.fcs',
        'pipe_separator': r'\|',
        'freq_of_parent': r'freq\.?\s+of\s+parent',
        'freq_of_live': r'freq\.?\s+of\s+live',
        'freq_of_total': r'freq\.?\s+of\s+total',
        'median_comp': r'median\s+\(comp-',
        'mean_comp': r'mean\s+\(comp-',
        'group_animal': r'\d+\.\d+',  # Group.Animal pattern like 1.1, 2.3
    }
    
    TISSUE_PREFIXES = ['SP_', 'BM_', 'PB_', 'LN_', 'TH_', 'LI_', 'KI_', 'LU_', 'BR_', 'HE_']
    
    WELL_PATTERNS = [r'_[A-H]\d{1,2}_', r'_[A-H]\d{1,2}\b']  # _A1_, _B2_, etc.
    
    # Generic lab indicators (only checked if NO flow indicators)
    LAB_COLUMN_PATTERNS = {
        'group': r'^group$',
        'replicate': r'^(replicate|rep)$',
        'timepoint': r'^(timepoint|time)$',
    }
    
    def __init__(self):
        """Initialize the data type detector."""
        self._flow_pattern_cache: Dict[str, re.Pattern] = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        for key, pattern in self.FLOW_INDICATORS.items():
            self._flow_pattern_cache[key] = re.compile(pattern, re.IGNORECASE)
        
        for key, pattern in self.LAB_COLUMN_PATTERNS.items():
            self._flow_pattern_cache[f'lab_{key}'] = re.compile(pattern, re.IGNORECASE)
    
    def detect_data_type(self, df: pd.DataFrame) -> DataType:
        """
        Detect whether the DataFrame contains flow cytometry or generic lab data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            DataType.FLOW_CYTOMETRY or DataType.GENERIC_LAB
            
        Note:
            Defaults to FLOW_CYTOMETRY if uncertain to maintain backward compatibility.
        """
        if df.empty:
            logger.warning("Empty DataFrame, defaulting to FLOW_CYTOMETRY")
            return DataType.FLOW_CYTOMETRY
        
        # Check for flow cytometry indicators (high priority)
        if self._has_flow_indicators(df):
            logger.info("Flow cytometry indicators detected")
            return DataType.FLOW_CYTOMETRY
        
        # Check for generic lab indicators (only if no flow indicators)
        if self._has_lab_indicators(df):
            logger.info("Generic lab data indicators detected")
            return DataType.GENERIC_LAB
        
        # Default to flow cytometry for backward compatibility
        logger.info("Data type ambiguous, defaulting to FLOW_CYTOMETRY for compatibility")
        return DataType.FLOW_CYTOMETRY
    
    def _has_flow_indicators(self, df: pd.DataFrame) -> bool:
        """
        Check for flow cytometry indicators in the DataFrame.
        
        Returns True if any flow indicator is found.
        """
        # Check column names for flow patterns
        all_columns = ' '.join(df.columns.astype(str))
        
        # Check for .fcs extension
        if self._flow_pattern_cache['fcs_extension'].search(all_columns):
            logger.debug("Found .fcs extension in column names")
            return True
        
        # Check for pipe separator (cell population hierarchies)
        if self._flow_pattern_cache['pipe_separator'].search(all_columns):
            logger.debug("Found pipe separator in column names")
            return True
        
        # Check for flow-specific metric patterns
        for pattern_name in ['freq_of_parent', 'freq_of_live', 'freq_of_total', 
                             'median_comp', 'mean_comp']:
            if self._flow_pattern_cache[pattern_name].search(all_columns):
                logger.debug(f"Found {pattern_name} pattern in column names")
                return True
        
        # Check for SampleID column (even if unnamed or first column)
        if 'SampleID' in df.columns or df.columns[0].lower() in ['', 'unnamed: 0', 'sampleid']:
            # Check if first column contains .fcs or group.animal patterns
            first_col = df.iloc[:, 0].astype(str)
            sample_text = ' '.join(first_col.head(20))
            
            if self._flow_pattern_cache['fcs_extension'].search(sample_text):
                logger.debug("Found .fcs in first column values")
                return True
            
            if self._flow_pattern_cache['group_animal'].search(sample_text):
                logger.debug("Found Group.Animal pattern in first column")
                return True
        
        # Check for tissue prefixes in any column
        for prefix in self.TISSUE_PREFIXES:
            if any(prefix in str(col) for col in df.columns):
                logger.debug(f"Found tissue prefix {prefix}")
                return True
            
            # Also check values in first column
            first_col_str = ' '.join(df.iloc[:, 0].astype(str).head(20))
            if prefix in first_col_str:
                logger.debug(f"Found tissue prefix {prefix} in data")
                return True
        
        # Check for well patterns
        for pattern in self.WELL_PATTERNS:
            well_re = re.compile(pattern)
            if well_re.search(all_columns):
                logger.debug("Found well pattern in column names")
                return True
            
            first_col_str = ' '.join(df.iloc[:, 0].astype(str).head(20))
            if well_re.search(first_col_str):
                logger.debug("Found well pattern in data")
                return True
        
        return False
    
    def _has_lab_indicators(self, df: pd.DataFrame) -> bool:
        """
        Check for generic lab data indicators.
        
        Returns True only if all required lab columns are present and
        no flow indicators were found.
        """
        # Get column names (case-insensitive)
        columns_lower = [col.lower().strip() for col in df.columns]
        
        # Check for required lab columns: Group, Replicate/rep, Timepoint/timepoint
        has_group = any(self._flow_pattern_cache['lab_group'].match(col) for col in columns_lower)
        has_replicate = any(self._flow_pattern_cache['lab_replicate'].match(col) for col in columns_lower)
        has_timepoint = any(self._flow_pattern_cache['lab_timepoint'].match(col) for col in columns_lower)
        
        if not (has_group and has_replicate and has_timepoint):
            logger.debug(f"Missing lab columns: group={has_group}, replicate={has_replicate}, timepoint={has_timepoint}")
            return False
        
        # Additional check: columns should be simple (no pipe separators or complex names)
        has_complex_names = any('|' in str(col) or '/' in str(col) for col in df.columns)
        if has_complex_names:
            logger.debug("Found complex column names, not generic lab data")
            return False
        
        logger.debug("All lab data indicators present")
        return True
