"""
Generic lab data parsing strategy for non-flow cytometry data.

Handles clinical chemistry, CBC, and other lab data with Group/Replicate/Timepoint structure.
"""

from typing import Dict, Any
import pandas as pd
import logging
import re

from .time_service import TimeService

logger = logging.getLogger(__name__)


class GenericLabParsingStrategy:
    """
    Parsing strategy for generic lab data (clinical chemistry, CBC, etc.).
    
    Handles data with Group, Replicate, and Timepoint columns but no
    flow cytometry-specific patterns.
    """
    
    def __init__(self):
        """Initialize the generic lab parsing strategy."""
        self.time_parser = TimeService()
    
    def parse(self, df: pd.DataFrame, columns: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Parse generic lab data.
        
        Args:
            df: DataFrame to parse
            columns: Optional column metadata (unused but kept for interface compatibility)
            
        Returns:
            Parsed DataFrame with standardized columns
        """
        result_df = df.copy()
        
        # Normalize column names (case-insensitive matching)
        result_df = self._normalize_columns(result_df)
        
        # Create synthetic SampleID from Group and Replicate
        result_df = self._create_sample_id(result_df)
        
        # Parse timepoint data
        result_df = self._parse_timepoint(result_df)
        
        # Add Animal column for export compatibility
        result_df = self._add_animal_column(result_df)
        
        logger.info(f"Generic lab parsing complete. Shape: {result_df.shape}")
        return result_df
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to standard format.
        
        Recognizes case-insensitive variants:
        - Group/group
        - Replicate/replicate/Rep/rep
        - Timepoint/timepoint/Time/time
        """
        column_mapping = {}
        
        for col in df.columns:
            col_lower = col.lower().strip()
            
            if col_lower == 'group':
                column_mapping[col] = 'Group'
            elif col_lower in ['replicate', 'rep']:
                column_mapping[col] = 'Replicate'
            elif col_lower in ['timepoint', 'time']:
                column_mapping[col] = 'Timepoint'
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
            logger.debug(f"Normalized columns: {column_mapping}")
        
        return df
    
    def _create_sample_id(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create synthetic SampleID from Group, Replicate, and Timepoint.
        
        Format: G{group}_R{replicate}_T{timepoint}
        """
        if 'Group' in df.columns and 'Replicate' in df.columns and 'Timepoint' in df.columns:
            df['SampleID'] = df.apply(
                lambda row: f"G{row['Group']}_R{row['Replicate']}_T{row['Timepoint']}", 
                axis=1
            )
            logger.debug("Created synthetic SampleID column with timepoint")
        elif 'Group' in df.columns and 'Replicate' in df.columns:
            df['SampleID'] = df.apply(
                lambda row: f"G{row['Group']}_R{row['Replicate']}", 
                axis=1
            )
            logger.debug("Created synthetic SampleID column without timepoint")
        else:
            # Create a basic index-based SampleID if columns are missing
            df['SampleID'] = [f"Sample_{i+1}" for i in range(len(df))]
            logger.warning("Group or Replicate column missing, using index-based SampleID")
        
        return df
    
    def _parse_timepoint(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse timepoint data into standardized Time column.
        
        Handles various formats:
        - "24hr", "168hr"
        - "Day 1", "Day 2"
        - "1000hr"
        - Numeric values
        """
        if 'Timepoint' not in df.columns:
            logger.warning("No Timepoint column found")
            return df
        
        time_values = []
        
        for value in df['Timepoint']:
            if pd.isna(value):
                time_values.append(None)
                continue
            
            value_str = str(value).strip()
            
            # Try to parse the time value
            try:
                # Check for "hr" or "hours" suffix
                if 'hr' in value_str.lower() or 'hour' in value_str.lower():
                    # Extract numeric part
                    numeric_part = re.search(r'(\d+\.?\d*)', value_str)
                    if numeric_part:
                        time_values.append(float(numeric_part.group(1)))
                    else:
                        time_values.append(None)
                
                # Check for "day" or "Day" prefix
                elif 'day' in value_str.lower():
                    # Extract numeric part after "day"
                    numeric_part = re.search(r'day\s*(\d+)', value_str, re.IGNORECASE)
                    if numeric_part:
                        # Convert days to hours (assuming 24 hours per day)
                        time_values.append(float(numeric_part.group(1)) * 24)
                    else:
                        time_values.append(None)
                
                # Try direct numeric conversion
                else:
                    try:
                        time_values.append(float(value_str))
                    except ValueError:
                        time_values.append(None)
                        logger.warning(f"Could not parse timepoint value: {value_str}")
            
            except Exception as e:
                logger.warning(f"Error parsing timepoint {value_str}: {e}")
                time_values.append(None)
        
        df['Time'] = time_values
        logger.debug(f"Parsed {len([t for t in time_values if t is not None])} timepoint values")
        
        return df
    
    def _add_animal_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Animal column for compatibility with export pipeline.
        
        Uses Replicate value as Animal ID since lab data doesn't
        have separate animal identifiers.
        """
        if 'Replicate' in df.columns:
            df['Animal'] = df['Replicate']
            logger.debug("Added Animal column from Replicate")
        else:
            df['Animal'] = 1
            logger.warning("No Replicate column, using default Animal=1")
        
        # Also add Well and Tissue columns for validation compatibility
        if 'Well' not in df.columns:
            df['Well'] = 'UNK'
            logger.debug("Added default Well column")
        
        if 'Tissue' not in df.columns:
            df['Tissue'] = 'UNK'
            logger.debug("Added default Tissue column")
        
        return df
