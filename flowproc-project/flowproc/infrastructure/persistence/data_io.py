import re
import logging
import numpy as np
import pandas as pd
from typing import Optional, Tuple, List
from pathlib import Path

from .logging_config import setup_logging
from .exceptions import ProcessingError
from ...domain.parsing.validation_service import validate_persistence_input
from ...domain.parsing.time_service import parse_time

logger = logging.getLogger(__name__)

FCS_RE = re.compile(r'^[A-Z0-9]+_\d+[._]\d+.*$', re.IGNORECASE)
GROUP_RE = re.compile(r'(?:G|Group)?(\d+)', re.IGNORECASE)
UNKNOWN_TISSUE = "Unknown"
UNKNOWN_WELL = "Unknown"

# Note: parse_time function is now imported from time_service
# The old implementation has been removed to eliminate duplication

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
    except (ValueError, AttributeError, IndexError) as e:
        logger.warning(f"Failed to parse sample ID '{sample_id}': {e}")
        return None, None, None, None

def extract_tissue(sample_id: str) -> str:
    """Extract tissue from sample ID."""
    if not sample_id or pd.isna(sample_id):
        return UNKNOWN_TISSUE
    try:
        return sample_id.split('_')[-1] if '_' in sample_id else UNKNOWN_TISSUE
    except (AttributeError, IndexError) as e:
        logger.warning(f"Failed to extract tissue from sample ID '{sample_id}': {e}")
        return UNKNOWN_TISSUE

def validate_parsed_data(df: pd.DataFrame, sid_col: str) -> None:
    """Validate parsed DataFrame using the consolidated validation service."""
    validate_persistence_input(df, sid_col)

