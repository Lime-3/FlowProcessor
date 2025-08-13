"""Parse group and animal identifiers."""
import re
from typing import Optional, Tuple, NamedTuple
import logging

logger = logging.getLogger(__name__)


class GroupAnimal(NamedTuple):
    """Parsed group and animal values."""
    group: int
    animal: int


class GroupAnimalParser:
    """Parses group and animal identifiers from sample IDs."""
    
    # Pattern for group.animal format
    GROUP_ANIMAL_PATTERN = re.compile(
        r'(\d+)\.(\d+)',
        re.IGNORECASE
    )
    
    # Alternative patterns
    ALT_PATTERNS = [
        # G1A2 format
        re.compile(r'G(\d+)A(\d+)', re.IGNORECASE),
        # Group1_Animal2 format
        re.compile(r'Group\s*(\d+).*Animal\s*(\d+)', re.IGNORECASE),
        # Separated by underscore
        re.compile(r'(\d+)_(\d+)'),
    ]
    
    def __init__(self, min_group: int = 1, max_group: int = 999999,
                 min_animal: int = 1, max_animal: int = 999999):
        """
        Initialize parser with validation ranges.
        
        Args:
            min_group: Minimum valid group number
            max_group: Maximum valid group number
            min_animal: Minimum valid animal number
            max_animal: Maximum valid animal number
        """
        self.min_group = min_group
        self.max_group = max_group
        self.min_animal = min_animal
        self.max_animal = max_animal
        
    def parse(self, text: str) -> Optional[GroupAnimal]:
        """
        Parse group and animal from text.
        
        Args:
            text: Text containing group/animal identifiers
            
        Returns:
            GroupAnimal tuple or None
        """
        if not text:
            return None
            
        # Try primary pattern first
        match = self.GROUP_ANIMAL_PATTERN.search(text)
        if match:
            result = self._extract_values(match)
            if result:
                return result
                
        # Try alternative patterns
        for pattern in self.ALT_PATTERNS:
            match = pattern.search(text)
            if match:
                result = self._extract_values(match)
                if result:
                    return result
                    
        return None
        
    def _extract_values(self, match: re.Match) -> Optional[GroupAnimal]:
        """Extract and validate group/animal values from match."""
        try:
            group = int(match.group(1))
            animal = int(match.group(2))
            
            # Validate ranges using consolidated validation
            from .validation_utils import validate_group_animal_values
            if not validate_group_animal_values(group, animal, 
                                               self.min_group, self.max_group,
                                               self.min_animal, self.max_animal):
                return None
                
            return GroupAnimal(group, animal)
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse group/animal: {e}")
            return None
            
    def format(self, group: int, animal: int, 
               format_type: str = 'dot') -> str:
        """
        Format group and animal values.
        
        Args:
            group: Group number
            animal: Animal number
            format_type: Format type ('dot', 'ga', 'underscore')
            
        Returns:
            Formatted string
        """
        if format_type == 'dot':
            return f"{group}.{animal}"
        elif format_type == 'ga':
            return f"G{group}A{animal}"
        elif format_type == 'underscore':
            return f"{group}_{animal}"
        else:
            return f"{group}.{animal}"
            
    def validate(self, group: int, animal: int) -> bool:
        """
        Validate group and animal values.
        
        Args:
            group: Group number
            animal: Animal number
            
        Returns:
            True if valid
        """
        from .validation_utils import validate_group_animal_values
        return validate_group_animal_values(group, animal, 
                                           self.min_group, self.max_group,
                                           self.min_animal, self.max_animal)

def extract_group_animal(text: str):
    """Convenience function to parse group and animal from text."""
    from .parsing_utils import ParsedID
    from .well_parser import WellParser
    from .time_service import TimeService
    from ...core.constants import Constants
    from .validation_utils import validate_sample_id_for_negative_values
    
    # Validate for negative values; do not raise here to allow uniform error handling upstream
    if not validate_sample_id_for_negative_values(text, strict=False):
        raise ValueError("Invalid group/animal")
    
    # Parse group/animal
    group_animal = GroupAnimalParser().parse(text)
    if not group_animal:
        return None
    
    # Parse additional components
    well_parser = WellParser()
    time_parser = TimeService()
    
    well = well_parser.parse(text) or Constants.UNKNOWN_WELL.value
    time_hours = time_parser.parse(text)
    
    return ParsedID(
        well=well,
        group=group_animal.group,
        animal=group_animal.animal,
        time=time_hours
    )