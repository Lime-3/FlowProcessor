import re
import logging
import numpy as np
import pandas as pd
from typing import Optional, Tuple, List
from pathlib import Path

from .logging_config import setup_logging

logger = logging.getLogger(__name__)

FCS_RE = re.compile(r'^[A-Z0-9]+_\d+[._]\d+.*$', re.IGNORECASE)
GROUP_RE = re.compile(r'(?:G|Group)?(\d+)', re.IGNORECASE)
UNKNOWN_TISSUE = "Unknown"
UNKNOWN_WELL = "Unknown"

def parse_time(time_str: Optional[str]) -> Optional[float]:
    """Parse time string to float (hours), return None if invalid."""
    if not time_str or pd.isna(time_str):
        return None
    try:
        if ':' in time_str:
            h, m = map(int, time_str.split(':'))
            return h + m / 60.0
        return float(time_str)
    except (ValueError, AttributeError):
        logger.warning(f"Invalid time format: {time_str}")
        return None

def extract_group_animal(sample_id: str) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[float]]:
    """Extract well, group, animal, and time from sample ID."""
    try:
        parts = sample_id.strip().split('_')
        well = parts[0] if parts[0] else UNKNOWN_WELL
        group_match = GROUP_RE.search(sample_id)
        group = int(group_match.group(1)) if group_match else None
        animal = int(parts[-2]) if len(parts) >= 2 and parts[-2].isdigit() else None
        time = parse_time(parts[-1]) if len(parts) >= 3 else None
        return well, group, animal, time
    except Exception as e:
        logger.warning(f"Failed to parse sample ID '{sample_id}': {e}")
        return None, None, None, None

def extract_tissue(sample_id: str) -> str:
    """Extract tissue from sample ID."""
    try:
        return sample_id.split('_')[-1] if '_' in sample_id else UNKNOWN_TISSUE
    except Exception:
        return UNKNOWN_TISSUE

def validate_parsed_data(df: pd.DataFrame, sid_col: str) -> None:
    """Validate parsed DataFrame."""
    if df.empty:
        raise ValueError("Parsed DataFrame is empty")
    required_cols = ['Group', 'Animal']
    missing = [col for col in required_cols if col not in df.columns or df[col].isna().all()]
    if missing:
        raise ValueError(f"Missing or empty required columns: {missing}")

def load_and_parse_df(input_file: Path) -> Tuple[pd.DataFrame, str]:
