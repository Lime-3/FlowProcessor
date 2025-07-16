# flowproc/parsing.py
import re
import logging
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

UNKNOWN_WELL = "Unknown_well"
UNKNOWN_TISSUE = "Unknown_tissue"

FCS_RE = r'^(SP|BM|WB|LN|TH|LI|LU|KD|SV|PL|AD|BR|HE)_?(?:([A-F]\d{1,2}))?_?(\d+\.\d+)(?:\.fcs)?$'
GROUP_RE = re.compile(r"(\d+)\.(\d+)")

TISSUE_PATTERNS = {
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
}

def parse_time(sample_id: str) -> Optional[float]:
    """Extract and convert time from sample ID (e.g., '2 hour' → 2.0, '30 minute' → 0.5, '1 day' → 24.0). Updated for plurals."""
    try:
        time_match = re.match(r'^(\d+\.?\d*)\s*(hours?|hrs?|h|minutes?|mins?|min|days?|d)', sample_id, re.IGNORECASE)
        if time_match:
            value = float(time_match.group(1))
            unit = time_match.group(2).lower().rstrip('s')
            if unit in ['hour', 'hr', 'h']:
                return value
            elif unit in ['minute', 'min']:
                return value / 60.0
            elif unit in ['day', 'd']:
                return value * 24.0
            logger.warning(f"Unknown time unit '{unit}' in sample ID: '{sample_id}'")
            return None
        logger.warning(f"No time found in sample ID: '{sample_id}'")
        return None
    except Exception as e:
        logger.error(f"Error parsing time from '{sample_id}': {e}")
        return None

def extract_group_animal(sample_id: str) -> Optional[Tuple[str, int, int, Optional[float]]]:
    """Extract well location (if present), group, animal, and time from sample ID."""
    sample_id = sample_id.strip()
    logger.debug(f"Attempting to parse sample ID: '{sample_id}'")
    
    time = parse_time(sample_id)
    if time is not None:
        time_match = re.match(r'^(\d+\.?\d*)\s*(hours?|hrs?|h|minutes?|mins?|min|days?|d)', sample_id, re.IGNORECASE)
        sample_id = sample_id[time_match.end():].lstrip('_')
        logger.debug(f"Removed time part, new sample_id: '{sample_id}'")
    
    tissue_map = {v[1].lower(): k for k, v in TISSUE_PATTERNS.items()}
    for full_name, prefix in tissue_map.items():
        if re.match(r'^' + re.escape(full_name) + r'_?', sample_id, re.IGNORECASE):
            sample_id = re.sub(r'^' + re.escape(full_name) + r'_?', prefix + '_', sample_id, flags=re.IGNORECASE)
            logger.debug(f"Converted '{full_name}' to '{prefix}' in sample ID: '{sample_id}'")
    
    match = re.match(FCS_RE, sample_id, re.IGNORECASE)
    if match:
        well = match.group(2) if match.group(2) else UNKNOWN_WELL
        animal_str = match.group(3)
        logger.debug(f"Matched FCS_RE: well={well}, animal_str={animal_str}")
        m = GROUP_RE.match(animal_str)
        if m:
            group = int(m.group(1))
            animal = int(m.group(2))
            logger.debug(f"Parsed SampleID '{sample_id}': Well={well}, Group={group}, Animal={animal}, Time={time}")
            return well, group, animal, time
        else:
            logger.warning(f"Failed to parse group/animal from '{animal_str}' in '{sample_id}'")
    else:
        m = GROUP_RE.search(sample_id)
        if m:
            group = int(m.group(1))
            animal = int(m.group(2))
            logger.debug(f"SampleID '{sample_id}' does not match FCS_RE, but parsed Group={group}, Animal={animal}, Time={time}")
            return UNKNOWN_WELL, group, animal, time
        logger.warning(f"SampleID '{sample_id}' does not match expected format")
    return None

def extract_tissue(sample_id: str) -> str:
    """Extract tissue shorthand from sample ID. Improved with broader matching."""
    if not isinstance(sample_id, str):
        logger.warning(f"Sample ID '{sample_id}' is not a string")
        return UNKNOWN_TISSUE
    
    logger.debug(f"Extracting tissue from sample ID: '{sample_id}'")
    
    for prefix, (patterns, full_name) in TISSUE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, sample_id, re.IGNORECASE):
                logger.debug(f"Matched tissue pattern '{pat}' for '{prefix}' in '{sample_id}'")
                return prefix
    
    match = re.match(FCS_RE, sample_id, re.IGNORECASE)
    if match:
        tissue = match.group(1).upper()
        logger.debug(f"Matched tissue '{tissue}' in '{sample_id}'")
        return tissue
    
    logger.warning(f"No tissue matched for '{sample_id}'")
    return UNKNOWN_TISSUE

def get_tissue_full_name(tissue: str) -> str:
    """Get the full name of the tissue."""
    return TISSUE_PATTERNS.get(tissue.upper(), (None, tissue))[1] if tissue else tissue

def load_and_parse_df(input_file: Path) -> Tuple[pd.DataFrame, str]:
    """Load CSV and parse sample IDs into columns."""
    logger.info(f"Loading file: {input_file}")
    if not input_file.exists():
        raise FileNotFoundError(f"Input file '{input_file}' does not exist.")

    df = pd.read_csv(input_file, index_col=0)
    logger.debug(f"Columns in '{input_file.name}': {list(df.columns)}")
    df = df.reset_index()
    sid_col = next((c for c in df.columns if 'sample' in c.lower() or 'id' in c.lower()), df.columns[0])
    logger.info(f"Sample ID column identified as '{sid_col}'")

    df = df.rename(columns={sid_col: 'SampleID'})
    sid_col = 'SampleID'
    try:
        valid_samples = df[sid_col].apply(lambda x: bool(re.match(FCS_RE, str(x).strip(), re.IGNORECASE)) or bool(GROUP_RE.search(str(x).strip())))
        if valid_samples.sum() == 0:
            raise ValueError("No valid sample IDs found in the CSV. Please check input format.")
        logger.debug(f"Valid samples: {valid_samples.sum()} out of {len(valid_samples)}")
    except Exception as e:
        logger.error(f"Error during sample ID validation: {e}")
        raise RuntimeError(f"Failed to validate sample IDs: {e}")
    
    df = df[valid_samples].copy()
    logger.debug(f"After filtering valid samples: {len(df)} rows")

    try:
        parsed = df[sid_col].apply(extract_group_animal)
        df['Well'] = parsed.apply(lambda p: p[0] if p else None)
        df['Group'] = parsed.apply(lambda p: p[1] if p else None)
        df['Animal'] = parsed.apply(lambda p: p[2] if p else None)
        df['Time'] = parsed.apply(lambda p: p[3] if p else None)
        for idx, row in df.iterrows():
            logger.debug(f"Parsed sample '{row[sid_col]}': Well={row['Well']}, Group={row['Group']}, Animal={row['Animal']}, Time={row['Time']}")
    except Exception as e:
        logger.error(f"Error during sample ID parsing: {e}")
        raise RuntimeError(f"Failed to parse sample IDs: {e}")

    df = df.dropna(subset=['Group', 'Animal'])  # Time and Well can be None
    logger.debug(f"After dropping rows with missing Group/Animal: {len(df)} rows")
    if df.empty:
        raise ValueError("All sample IDs failed to parse or missing key fields.")

    return df, sid_col