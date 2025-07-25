import re
import logging
import numpy as np
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum

from flowproc.logging_config import setup_logging
from flowproc.data_io import extract_group_animal, extract_tissue, validate_parsed_data
from flowproc.exceptions import ProcessingError

logger = logging.getLogger(__name__)

class Constants(Enum):
    UNKNOWN_WELL = "Unknown_well"
    UNKNOWN_TISSUE = "Unknown_tissue"

# Updated regex patterns to be more flexible
FCS_RE = r'^(SP|BM|WB|LN|TH|LI|LU|KD|SV|PL|AD|BR|HE)?_?(?:([A-F]\d{1,2}))?_?(-?\d+\.-?\d+)(?:\.fcs)?$'
GROUP_RE = re.compile(r"(-?\d+)\.(-?\d+)")
SIMPLE_ID_RE = re.compile(r'^(\d+\.\d+)(?:\.fcs)?$', re.IGNORECASE)

TISSUE_PATTERNS: Dict[str, Tuple[List[str], str]] = {
    'SP': ([r'\bSP\b', r'spleen'], "Spleen"),
    'WB': ([r'\bWB\b', r'whole\s*blood', r'peripheral\s*blood'], "Whole Blood"),
    'BM': ([r'\bBM\b', r'bone\s*marrow'], "Bone Marrow"),
    'LN': ([r'\bLN\b', r'lymph\s*node'], "Lymph Node"),
    'TH': ([r'thymus'], "Thymus"),
    'LI': ([r'liver', r'\bliv\b'], "Liver"),
    'LU': ([r'lung'], "Lung"),
    'KD': ([r'kidney'], "Kidney"),
    'SV': ([r'synovial'], "Synovial"),
    'PL': ([r'peritoneal'], "Peritoneal"),
    'AD': ([r'adipose'], "Adipose"),
    'BR': ([r'brain'], "Brain"),
    'HE': ([r'heart'], "Heart"),
    'T': ([r'^T\d+$'], "Tissue"),
}

LITERAL_TISSUE_MAP: Dict[str, str] = {
    'spleen': 'SP',
    'whole blood': 'WB',
    'peripheral blood': 'WB',
    'bone marrow': 'BM',
    'lymph node': 'LN',
    'thymus': 'TH',
    'liver': 'LI',
    'lung': 'LU',
    'kidney': 'KD',
    'synovial': 'SV',
    'peritoneal': 'PL',
    'adipose': 'AD',
    'brain': 'BR',
    'heart': 'HE',
}

@dataclass
class ParsedID:
    well: str
    group: int
    animal: int
    time: Optional[float]

@lru_cache(maxsize=1000)
def extract_tissue(sample_id: str) -> str:
    """Extract tissue shorthand from sample ID (cached for efficiency)."""
    if not isinstance(sample_id, str):
        return Constants.UNKNOWN_TISSUE.value
    
    # First check for explicit tissue patterns
    for prefix, (patterns, _) in TISSUE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, sample_id, re.IGNORECASE):
                return prefix
    
    # Check if ID matches FCS pattern
    match = re.match(FCS_RE, sample_id, re.IGNORECASE)
    if match and match.group(1):
        return match.group(1).upper()
    
    # Check for tissue prefix in filename
    parts = sample_id.split('_')
    if parts and parts[0].upper() in TISSUE_PATTERNS:
        return parts[0].upper()
    
    return Constants.UNKNOWN_TISSUE.value

def parse_time(sample_id: str) -> Optional[float]:
    """Extract and convert time from sample ID."""
    if not isinstance(sample_id, str):
        return None
    
    unit_patterns = r'(hours?|hrs?|h|minutes?|mins?|min|days?|d)'
    time_match = re.search(r'(\d+\.?\d*)\s*(' + unit_patterns + r')', sample_id, re.IGNORECASE)
    
    if time_match:
        try:
            value = float(time_match.group(1))
            unit = time_match.group(2).lower().rstrip('s')
            
            if unit in ['hour', 'hr', 'h']:
                return value
            elif unit in ['minute', 'min']:
                return value / 60.0
            elif unit in ['day', 'd']:
                return value * 24.0
        except ValueError:
            pass
    
    return None

def extract_group_animal(sample_id: str) -> Optional[ParsedID]:
    """Extract well, group, animal, and time from sample ID."""
    if not isinstance(sample_id, str):
        return None
    
    original_id = sample_id
    sample_id = sample_id.strip()
    
    # Extract time if present
    time = parse_time(sample_id)
    if time is not None:
        # Remove time portion from ID
        time_match = re.search(r'(\d+\.?\d*)\s*(hours?|hrs?|h|minutes?|mins?|min|days?|d)', sample_id, re.IGNORECASE)
        if time_match:
            sample_id = sample_id[time_match.end():].lstrip('_')
    
    # Replace literal tissue names with abbreviations
    for full_name, prefix in LITERAL_TISSUE_MAP.items():
        if re.match(r'^' + re.escape(full_name) + r'_?', sample_id, re.IGNORECASE):
            sample_id = re.sub(r'^' + re.escape(full_name) + r'_?', prefix + '_', sample_id, flags=re.IGNORECASE)
            break
    
    # Try multiple patterns to extract group/animal
    patterns = [
        # Standard FCS pattern
        (FCS_RE, lambda m: ParsedID(
            well=m.group(2) if m.group(2) else Constants.UNKNOWN_WELL.value,
            group=int(m.group(3).split('.')[0]),
            animal=int(m.group(3).split('.')[1]),
            time=time
        )),
        # Simple ID pattern (just numbers)
        (SIMPLE_ID_RE, lambda m: ParsedID(
            well=Constants.UNKNOWN_WELL.value,
            group=int(m.group(1).split('.')[0]),
            animal=int(m.group(1).split('.')[1]),
            time=time
        )),
        # Generic pattern with group.animal anywhere
        (r'(\d+)\.(\d+)', lambda m: ParsedID(
            well=Constants.UNKNOWN_WELL.value,
            group=int(m.group(1)),
            animal=int(m.group(2)),
            time=time
        ))
    ]
    
    for pattern, parser in patterns:
        match = re.search(pattern, sample_id)
        if match:
            try:
                parsed = parser(match)
                if parsed.group >= 0 and parsed.animal >= 0:
                    return parsed
            except (ValueError, IndexError, AttributeError):
                continue
    
    logger.warning(f"ID '{original_id}' format mismatch")
    return None

def get_tissue_full_name(tissue: str) -> str:
    """Map tissue shorthand to full name."""
    if not tissue:
        return tissue
    return TISSUE_PATTERNS.get(tissue.upper(), (None, tissue))[1]

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

def is_likely_id_column(series: pd.Series) -> bool:
    """Check if series looks like sample IDs."""
    non_nan = series.dropna().astype(str).str.strip()
    if len(non_nan) == 0:
        return False
    
    # Check for various ID patterns
    patterns = [
        lambda x: bool(GROUP_RE.search(x)),  # Contains group.animal pattern
        lambda x: x.endswith('.fcs'),         # FCS file
        lambda x: bool(re.match(r'^\d+\.\d+$', x)),  # Simple numeric ID
        lambda x: any(tissue in x.upper() for tissue in TISSUE_PATTERNS.keys()),  # Contains tissue
    ]
    
    match_count = sum(any(pattern(x) for pattern in patterns) for x in non_nan)
    match_frac = match_count / len(non_nan)
    
    # Also check uniqueness
    uniqueness = len(non_nan.unique()) / len(non_nan) if len(non_nan) > 0 else 0
    
    return match_frac > 0.5 or uniqueness > 0.8

def load_and_parse_df(input_file: Path) -> Tuple[pd.DataFrame, str]:
    """Load and parse a CSV file."""
    logger.info(f"Loading file: {input_file}")
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file '{input_file}' does not exist")
    
    try:
        # Load CSV with flexible parsing
        df = pd.read_csv(input_file, skipinitialspace=True, engine='python')
        
        # Remove footer rows if present
        df = df[~df.iloc[:, 0].astype(str).str.contains('Mean|SD|Average|StdDev', na=False, case=False)]
        
        logger.debug(f"Columns in '{input_file.name}': {list(df.columns)}")
        
        if df.empty:
            logger.warning("Empty DataFrame after loading")
            return df, "SampleID"
        
        # Find sample ID column
        candidates = []
        for c in df.columns:
            c_lower = c.lower()
            if 'sample' in c_lower or 'id' in c_lower or c == 'Unnamed: 0':
                candidates.append(c)
        
        # Find the best candidate
        sid_col = None
        for c in candidates:
            if is_likely_id_column(df[c]):
                sid_col = c
                break
        
        # If no good candidate found, use first column
        if sid_col is None:
            sid_col = df.columns[0]
        
        logger.info(f"Sample ID column identified as '{sid_col}'")
        
        # Rename to standard name
        df = df.rename(columns={sid_col: 'SampleID'})
        sid_col = 'SampleID'
        
        # Parse sample IDs
        parsed = df[sid_col].apply(extract_group_animal)
        valid = parsed.notna()
        
        # Filter to valid rows
        df = df[valid].copy()
        
        if df.empty:
            logger.warning("No valid sample IDs found")
            return df, sid_col
        
        # Extract parsed components
        df['Well'] = parsed[valid].apply(lambda p: p.well)
        df['Group'] = parsed[valid].apply(lambda p: p.group)
        df['Animal'] = parsed[valid].apply(lambda p: p.animal)
        df['Time'] = parsed[valid].apply(lambda p: p.time)
        
        # Clean up time column
        df['Time'] = df['Time'].replace(np.nan, None)
        
        # Extract tissue
        df['Tissue'] = df['SampleID'].apply(extract_tissue)
        
        # Drop rows with missing critical data
        df = df.dropna(subset=['Group', 'Animal'])
        
        if df.empty:
            logger.warning("All sample IDs failed to parse")
            return df, sid_col
        
        # Validate the parsed data
        validate_parsed_data(df, sid_col)
        
        return df, sid_col
        
    except (FileNotFoundError, pd.errors.EmptyDataError) as e:
        logger.error(f"Failed to load {input_file}: {e}")
        raise ProcessingError(f"Invalid input file: {e}")
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error: {e}")
        raise ProcessingError(f"Failed to parse CSV: {e}")
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise ProcessingError(f"Failed to parse: {e}")