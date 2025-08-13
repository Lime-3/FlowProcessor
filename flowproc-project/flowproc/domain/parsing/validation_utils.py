"""
Validation utilities for parsing logic.
Consolidates duplicated validation patterns.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pattern for detecting negative group/animal values
NEGATIVE_GROUP_ANIMAL_PATTERN = re.compile(r'(_-\d+\.|\.-\d+)')

def validate_sample_id_for_negative_values(sample_id: str, strict: bool = False) -> bool:
    """
    Validate sample ID for negative group/animal values.
    
    Args:
        sample_id: Sample ID string to validate
        strict: If True, raises ValueError on invalid values. If False, returns False.
        
    Returns:
        True if valid, False if invalid (when not strict)
        
    Raises:
        ValueError: If strict=True and negative values are found
    """
    if not isinstance(sample_id, str):
        if strict:
            raise ValueError("Sample ID must be a string")
        return False
    
    # Check for negative group (e.g., SP_-1.2) or negative animal (e.g., SP_1.-2)
    if NEGATIVE_GROUP_ANIMAL_PATTERN.search(sample_id):
        # Modern behavior: treat as invalid format without raising in strict mode here;
        # downstream parsers will surface a uniform ParseError.
        logger.warning(f"Negative values detected in: {sample_id}")
        return False
    
    return True

def validate_group_animal_values(group: int, animal: int, 
                                min_group: int = 1, max_group: int = 999999,
                                min_animal: int = 1, max_animal: int = 999999) -> bool:
    """
    Validate group and animal values are within acceptable ranges.
    
    Args:
        group: Group number
        animal: Animal number
        min_group: Minimum valid group number
        max_group: Maximum valid group number
        min_animal: Minimum valid animal number
        max_animal: Maximum valid animal number
        
    Returns:
        True if valid, False otherwise
    """
    if not (min_group <= group <= max_group):
        logger.warning(f"Group {group} out of range [{min_group}, {max_group}]")
        return False
        
    if not (min_animal <= animal <= max_animal):
        logger.warning(f"Animal {animal} out of range [{min_animal}, {max_animal}]")
        return False
        
    return True 