"""Parse time values from sample IDs and data."""
import re
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class TimeParser:
    """Parses time values with unit conversion."""
    
    # Time unit conversions to hours
    UNIT_CONVERSIONS: Dict[str, float] = {
        # Hours
        'h': 1.0, 'hr': 1.0, 'hrs': 1.0, 'hour': 1.0, 'hours': 1.0,
        # Minutes
        'm': 1/60, 'min': 1/60, 'mins': 1/60, 'minute': 1/60, 'minutes': 1/60,
        # Days
        'd': 24.0, 'day': 24.0, 'days': 24.0,
        # Seconds (rare but possible)
        's': 1/3600, 'sec': 1/3600, 'secs': 1/3600, 'second': 1/3600, 'seconds': 1/3600,
    }
    
    # Regex for time extraction - more selective patterns
    TIME_PATTERN = re.compile(
        r'(?:^|\s)(\d+(?:\.\d+)?)\s*([a-z]+)(?:\s|_|$)',
        re.IGNORECASE
    )
    
    # Pattern for time prefixes (e.g., "2 hour_", "30 min_")
    TIME_PREFIX_PATTERN = re.compile(
        r'^(\d+(?:\.\d+)?)\s*([a-z]+)(?:\s|_)',
        re.IGNORECASE
    )
    
    def __init__(self, default_unit: str = 'h'):
        """
        Initialize time parser.
        
        Args:
            default_unit: Default unit when none specified
        """
        self.default_unit = default_unit
        
    def parse(self, text: str) -> Optional[float]:
        """
        Parse time value from text.
        
        Args:
            text: Text containing time value
            
        Returns:
            Time in hours, or None if not found
        """
        if not text:
            return None
            
        # Try time prefix pattern first (e.g., "2 hour_SP_...")
        match = self.TIME_PREFIX_PATTERN.search(text)
        if match:
            value_str, unit = match.groups()
            return self._convert_to_hours(value_str, unit)
        
        # Try general time pattern with required units
        match = self.TIME_PATTERN.search(text)
        if match:
            value_str, unit = match.groups()
            # Unit is required for general pattern
            if unit:
                return self._convert_to_hours(value_str, unit)
            
        return None
        
    def _convert_to_hours(self, value_str: str, unit: str) -> Optional[float]:
        """Convert time value with unit to hours."""
        # Parse numeric value
        try:
            value = float(value_str)
        except ValueError:
            logger.warning(f"Invalid time value: {value_str}")
            return None
            
        # Get unit multiplier
        unit_lower = unit.lower()
        multiplier = self.UNIT_CONVERSIONS.get(unit_lower)
        
        if multiplier is None:
            logger.warning(f"Unknown time unit: {unit}")
            return None
            
        return value * multiplier
        
    def format_time(self, hours: float, format_type: str = 'hm') -> str:
        """
        Format time value for display.
        
        Args:
            hours: Time in hours
            format_type: Format type ('hm' for H:MM, 'auto' for automatic)
            
        Returns:
            Formatted time string
        """
        if format_type == 'hm':
            # Format as H:MM
            h = int(hours)
            m = int((hours - h) * 60)
            return f"{h}:{m:02d}"
            
        elif format_type == 'auto':
            # Choose appropriate format
            if hours < 1:
                return f"{int(hours * 60)}min"
            elif hours < 24:
                return f"{hours:.1f}h"
            else:
                days = hours / 24
                return f"{days:.1f}d"
                
        else:
            return f"{hours:.1f}h"
            
    def parse_range(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Parse time range (e.g., "0-24h").
        
        Args:
            text: Text containing time range
            
        Returns:
            Tuple of (start_hours, end_hours) or None
        """
        # Pattern for range: number-number unit
        range_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*([a-z]+)?',
            re.IGNORECASE
        )
        
        match = range_pattern.search(text)
        if not match:
            return None
            
        start_str, end_str, unit = match.groups()
        
        try:
            start = float(start_str)
            end = float(end_str)
        except ValueError:
            return None
            
        # Get unit multiplier
        if unit:
            multiplier = self.UNIT_CONVERSIONS.get(unit.lower(), 1.0)
        else:
            multiplier = 1.0
            
        return (start * multiplier, end * multiplier)

def parse_time(text: str) -> float:
    """Convenience function to parse time from text."""
    if not isinstance(text, str):
        raise ValueError("Sample ID must be a string")
    return TimeParser().parse(text)