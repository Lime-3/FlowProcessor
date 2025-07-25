"""High-level sample ID parser that combines component parsers."""
from typing import Optional, NamedTuple, Dict
import logging

from .time_parser import TimeParser
from .tissue_parser import TissueParser
from .well_parser import WellParser
from .group_animal_parser import GroupAnimalParser
from ...core.exceptions import ParsingError as ParseError

logger = logging.getLogger(__name__)


class ParsedSampleID(NamedTuple):
    """Complete parsed sample ID."""
    group: int
    animal: int
    tissue: str = 'UNK'
    well: str = 'UNK'
    time_hours: Optional[float] = None
    replicate: Optional[int] = None


class SampleIDParser:
    """Combines component parsers to parse complete sample IDs."""
    
    def __init__(self, 
                 time_parser: Optional[TimeParser] = None,
                 tissue_parser: Optional[TissueParser] = None,
                 well_parser: Optional[WellParser] = None,
                 group_animal_parser: Optional[GroupAnimalParser] = None,
                 strict: bool = False):
        """
        Initialize sample ID parser.
        
        Args:
            time_parser: Time parser instance
            tissue_parser: Tissue parser instance
            well_parser: Well parser instance
            group_animal_parser: Group/animal parser instance
            strict: Whether to raise exceptions on parse failure
        """
        self.time_parser = time_parser or TimeParser()
        self.tissue_parser = tissue_parser or TissueParser()
        self.well_parser = well_parser or WellParser()
        self.group_animal_parser = group_animal_parser or GroupAnimalParser()
        self.strict = strict
        
        self._cache: Dict[str, Optional[ParsedSampleID]] = {}
        
    def parse(self, sample_id: str) -> Optional[ParsedSampleID]:
        """
        Parse complete sample ID.
        
        Args:
            sample_id: Sample ID string
            
        Returns:
            ParsedSampleID or None
            
        Raises:
            ParseError: If strict mode and parsing fails
        """
        if not sample_id:
            if self.strict:
                raise ParseError("Empty sample ID")
            return None
            
        # Check cache
        if sample_id in self._cache:
            return self._cache[sample_id]
            
        # Parse components
        result = self._parse_components(sample_id)
        
        if result is None and self.strict:
            raise ParseError(f"Failed to parse sample ID: {sample_id}")
            
        # Cache result
        self._cache[sample_id] = result
        return result
        
    def _parse_components(self, sample_id: str) -> Optional[ParsedSampleID]:
        """Parse individual components from sample ID."""
        # Check for negative values in the text before parsing
        import re
        neg_pattern = re.search(r'(_-\d+\.|\.-\d+)', sample_id)
        if neg_pattern and self.strict:
            raise ParseError("Invalid group/animal numbers found")
        elif neg_pattern:
            logger.warning(f"Negative values detected in: {sample_id}")
            return None
            
        # Remove .fcs extension if present
        clean_id = sample_id
        if clean_id.lower().endswith('.fcs'):
            clean_id = clean_id[:-4]
            
        # Parse group and animal (required)
        group_animal = self.group_animal_parser.parse(clean_id)
        if not group_animal:
            logger.warning(f"Failed to parse group/animal from: {sample_id}")
            return None
            
        # Parse optional components
        time_hours = self.time_parser.parse(clean_id)
        tissue = self.tissue_parser.parse(clean_id)
        well = self.well_parser.parse(clean_id)
        
        # Remove parsed components to check for remaining text
        remaining = clean_id
        
        # Remove time component
        if time_hours is not None:
            # Find and remove time pattern
            remaining = self._remove_time_pattern(remaining)
            
        # Remove tissue if found
        if tissue != self.tissue_parser.unknown_code:
            remaining = self._remove_tissue_pattern(remaining, tissue)
            
        # Remove well if found
        if well != self.well_parser.unknown_well:
            remaining = self._remove_well_pattern(remaining, well)
            
        # Remove group.animal pattern
        remaining = self._remove_group_animal_pattern(remaining, group_animal)
        
        # Log if there's significant remaining text
        remaining = remaining.strip('_- ')
        if remaining and len(remaining) > 2:
            logger.debug(f"Unparsed text in sample ID '{sample_id}': '{remaining}'")
            
        return ParsedSampleID(
            group=group_animal.group,
            animal=group_animal.animal,
            tissue=tissue,
            well=well,
            time_hours=time_hours
        )
        
    def _remove_time_pattern(self, text: str) -> str:
        """Remove time pattern from text."""
        # This is a simplified version - could be more sophisticated
        import re
        pattern = r'\d+(?:\.\d+)?\s*(?:hour|hr|h|minute|min|m|day|d)s?\s*[_-]?'
        return re.sub(pattern, '', text, flags=re.IGNORECASE)
        
    def _remove_tissue_pattern(self, text: str, tissue: str) -> str:
        """Remove tissue pattern from text."""
        # Remove tissue code at start
        if text.upper().startswith(tissue + '_'):
            return text[len(tissue) + 1:]
        elif text.upper().startswith(tissue):
            return text[len(tissue):]
        return text
        
    def _remove_well_pattern(self, text: str, well: str) -> str:
        """Remove well pattern from text."""
        import re
        # Remove well pattern with surrounding delimiters
        pattern = f'[_-]?{re.escape(well)}[_-]?'
        return re.sub(pattern, '_', text, flags=re.IGNORECASE).strip('_')
        
    def _remove_group_animal_pattern(self, text: str, group_animal) -> str:
        """Remove group.animal pattern from text."""
        import re
        pattern = f'{group_animal.group}\\.{group_animal.animal}'
        return re.sub(pattern, '', text)
        
    def clear_cache(self) -> None:
        """Clear parsing cache."""
        self._cache.clear()