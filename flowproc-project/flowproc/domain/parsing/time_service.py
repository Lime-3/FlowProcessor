"""
Comprehensive Time Service for parsing and formatting time values.

This service consolidates all time parsing and formatting functionality
that was previously duplicated across multiple modules:
- flowproc/domain/parsing/time_parser.py
- flowproc/domain/export/time_formatter.py  
- flowproc/infrastructure/persistence/data_io.py
- experimental/archive/parsing.py

Provides unified parsing, formatting, and conversion capabilities.
"""

import re
import logging
from typing import Optional, Dict, Tuple, Union
from enum import Enum

logger = logging.getLogger(__name__)


class TimeFormat(Enum):
    """Supported time format styles."""
    HM = 'hm'                    # 2:30
    HM_VERBOSE = 'hm_verbose'    # 2h 30m
    DECIMAL = 'decimal'          # 2.5h
    AUTO = 'auto'                # Automatic selection
    EXCEL_SERIAL = 'excel'       # Excel serial time


class TimeService:
    """
    Comprehensive time parsing and formatting service.
    
    Consolidates all time-related functionality from multiple modules
    into a single, robust service with consistent behavior.
    """
    
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
    
    # Comprehensive regex patterns for time extraction
    PATTERNS = {
        # Timecourse pattern (e.g., "Day 3", "d3", "day_3")
        'TIMECOURSE': re.compile(
            r'(?:^|\s|_)(day)\s*(\d+(?:\.\d+)?)(?:\s|_|$)',
            re.IGNORECASE
        ),
        
        # Pattern for unit-first format (e.g., "day_3", "hour_2")
        'UNIT_FIRST': re.compile(
            r'(?:^|\s|_)(day|hour|hr|h|minute|min|m|days|hours|minutes)\s*_?(\d+(?:\.\d+)?)(?:\s|_|$)',
            re.IGNORECASE
        ),
        
        # Filename time pattern (e.g., "Sample_Study_Day 3.csv")
        'FILENAME': re.compile(
            r'(?:^|\s|_)(?:(\d+(?:\.\d+)?)\s*(day|hour|hr|h|minute|min|m|days|hours|minutes)|(day|hour|hr|h|minute|min|m|days|hours|minutes)\s*(\d+(?:\.\d+)?))(?:\s|_|\.|$)',
            re.IGNORECASE
        ),
        
        # Time prefix pattern (e.g., "2 hour_SP_...")
        'PREFIX': re.compile(
            r'^(\d+(?:\.\d+)?)\s*([a-z]+)(?:\s|_)',
            re.IGNORECASE
        ),
        
        # General time pattern with required units
        'GENERAL': re.compile(
            r'(?:^|\s|_)(\d+(?:\.\d+)?)\s*([a-z]+)(?:\s|_|$)',
            re.IGNORECASE
        ),
        
        # Range pattern (e.g., "0-24h")
        'RANGE': re.compile(
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*([a-z]+)?',
            re.IGNORECASE
        ),
        
        # Excel time format (H:MM)
        'EXCEL_HM': re.compile(
            r'^(\d+):(\d{2})$'
        ),
        
        # Unit suffix patterns for parsing formatted strings
        'UNIT_SUFFIX': re.compile(
            r'^(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|d|day|days|s|sec|secs|second|seconds)$',
            re.IGNORECASE
        )
    }
    
    def __init__(self, default_unit: str = 'h', default_format: TimeFormat = TimeFormat.HM):
        """
        Initialize time service.
        
        Args:
            default_unit: Default unit when none specified
            default_format: Default format style for output
        """
        self.default_unit = default_unit
        self.default_format = default_format
        
    def parse(self, text: Union[str, None]) -> Optional[float]:
        """
        Parse time value from text with comprehensive pattern matching.
        
        Args:
            text: Text containing time value
            
        Returns:
            Time in hours, or None if not found
            
        Examples:
            >>> service = TimeService()
            >>> service.parse("Day 3")  # 72.0
            >>> service.parse("2 hour_SP")  # 2.0
            >>> service.parse("30 min")  # 0.5
            >>> service.parse("Sample_Study_Day 3.csv")  # 72.0
        """
        if not text or not isinstance(text, str):
            return None
            
        logger.debug(f"Parsing time from text: '{text}'")
        
        # Try timecourse pattern first (e.g., "Day 3", "d3")
        match = self.PATTERNS['TIMECOURSE'].search(text)
        if match:
            unit, value_str = match.groups()
            result = self._convert_to_hours(value_str, unit)
            logger.debug(f"TIMECOURSE pattern match: unit='{unit}', value='{value_str}', result={result}")
            return result
        
        # Try unit-first pattern (e.g., "day_3", "hour_2")
        match = self.PATTERNS['UNIT_FIRST'].search(text)
        if match:
            unit, value_str = match.groups()
            result = self._convert_to_hours(value_str, unit)
            logger.debug(f"UNIT_FIRST pattern match: unit='{unit}', value='{value_str}', result={result}")
            return result
        
        # Try filename time pattern (e.g., "Sample_Study_Day 3.csv")
        match = self.PATTERNS['FILENAME'].search(text)
        if match:
            groups = match.groups()
            # Handle both "3 Day" and "Day 3" patterns
            if groups[0] and groups[1]:  # "3 Day" pattern
                value_str, unit = groups[0], groups[1]
            elif groups[2] and groups[3]:  # "Day 3" pattern
                unit, value_str = groups[2], groups[3]
            else:
                logger.debug(f"FILENAME pattern matched but groups are invalid: {groups}")
                value_str, unit = None, None
                
            if value_str and unit:
                result = self._convert_to_hours(value_str, unit)
                logger.debug(f"FILENAME pattern match: value='{value_str}', unit='{unit}', result={result}")
                return result
        
        # Try time prefix pattern (e.g., "2 hour_SP_...")
        match = self.PATTERNS['PREFIX'].search(text)
        if match:
            value_str, unit = match.groups()
            result = self._convert_to_hours(value_str, unit)
            logger.debug(f"PREFIX pattern match: value='{value_str}', unit='{unit}', result={result}")
            return result
        
        # Try general time pattern with required units
        match = self.PATTERNS['GENERAL'].search(text)
        if match:
            value_str, unit = match.groups()
            # Unit is required for general pattern
            if unit:
                result = self._convert_to_hours(value_str, unit)
                logger.debug(f"GENERAL pattern match: value='{value_str}', unit='{unit}', result={result}")
                return result
            
        logger.debug(f"No time pattern matched for text: '{text}'")
        return None
        
    def parse_formatted(self, time_str: str) -> Optional[float]:
        """
        Parse time from formatted string (e.g., "2:30", "2.5h", "30min").
        
        Args:
            time_str: Formatted time string
            
        Returns:
            Time in hours or None
            
        Examples:
            >>> service = TimeService()
            >>> service.parse_formatted("2:30")  # 2.5
            >>> service.parse_formatted("2.5h")  # 2.5
            >>> service.parse_formatted("30min")  # 0.5
        """
        if not time_str:
            return None
            
        time_str = str(time_str).strip()
        
        # Try H:MM format
        match = self.PATTERNS['EXCEL_HM'].match(time_str)
        if match:
            try:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                return hours + minutes / 60
            except (ValueError, IndexError):
                pass
                
        # Try unit suffix patterns
        match = self.PATTERNS['UNIT_SUFFIX'].match(time_str)
        if match:
            value_str, unit = match.groups()
            return self._convert_to_hours(value_str, unit)
                
        # Try as plain number (assume hours)
        try:
            return float(time_str)
        except ValueError:
            logger.warning(f"Could not parse formatted time: {time_str}")
            return None
            
    def parse_range(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Parse time range (e.g., "0-24h").
        
        Args:
            text: Text containing time range
            
        Returns:
            Tuple of (start_hours, end_hours) or None
            
        Examples:
            >>> service = TimeService()
            >>> service.parse_range("0-24h")  # (0.0, 24.0)
            >>> service.parse_range("1-2 days")  # (24.0, 48.0)
        """
        match = self.PATTERNS['RANGE'].search(text)
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
        
    def format(self, hours: Optional[float], 
               format_style: Optional[Union[TimeFormat, str]] = None) -> str:
        """
        Format time value for display.
        
        Args:
            hours: Time in hours
            format_style: Format style to use
            
        Returns:
            Formatted time string
            
        Examples:
            >>> service = TimeService()
            >>> service.format(2.5)  # "2:30"
            >>> service.format(2.5, TimeFormat.HM_VERBOSE)  # "2h 30m"
            >>> service.format(2.5, TimeFormat.DECIMAL)  # "2.5h"
        """
        if hours is None:
            return ""
            
        if format_style is None:
            format_style = self.default_format
            
        # Convert string to enum if needed
        if isinstance(format_style, str):
            try:
                format_style = TimeFormat(format_style)
            except ValueError:
                format_style = self.default_format
            
        if format_style == TimeFormat.AUTO:
            return self._auto_format(hours)
        elif format_style == TimeFormat.HM:
            return self._format_hm(hours)
        elif format_style == TimeFormat.HM_VERBOSE:
            return self._format_hm_verbose(hours)
        elif format_style == TimeFormat.DECIMAL:
            return self._format_decimal(hours)
        elif format_style == TimeFormat.EXCEL_SERIAL:
            return str(self.to_excel_serial(hours))
        else:
            return str(hours)
            
    def _auto_format(self, hours: float) -> str:
        """Automatically select best format based on time value."""
        if hours < 1:
            # Show as minutes
            minutes = int(hours * 60)
            return f"{minutes}min"
        elif hours < 24:
            # Show as H:MM
            return self._format_hm(hours)
        else:
            # Show as days
            days = hours / 24
            if days == int(days):
                return f"{int(days)}d"
            else:
                return f"{days:.1f}d"
                
    def _format_hm(self, hours: float) -> str:
        """Format as H:MM."""
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h}:{m:02d}"
        
    def _format_hm_verbose(self, hours: float) -> str:
        """Format as Xh Ym."""
        h = int(hours)
        m = int((hours - h) * 60)
        
        if m == 0:
            return f"{h}h"
        else:
            return f"{h}h {m}m"
            
    def _format_decimal(self, hours: float) -> str:
        """Format as decimal hours."""
        return f"{hours:.1f}h"
        
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
        
    def to_excel_serial(self, hours: float) -> float:
        """
        Convert hours to Excel serial time.
        
        Excel stores times as fractions of a day.
        
        Args:
            hours: Time in hours
            
        Returns:
            Excel serial time value
        """
        return hours / 24
        
    def from_excel_serial(self, serial: float) -> float:
        """
        Convert Excel serial time to hours.
        
        Args:
            serial: Excel serial time value
            
        Returns:
            Time in hours
        """
        return serial * 24
        
    def validate_time(self, hours: float) -> bool:
        """
        Validate time value is reasonable.
        
        Args:
            hours: Time in hours
            
        Returns:
            True if time is valid and reasonable
        """
        return isinstance(hours, (int, float)) and hours >= 0 and hours < 10000  # Max 10000 hours


# Global instance for convenience
_time_service = TimeService()


def parse_time(text: Union[str, None]) -> Optional[float]:
    """
    Convenience function to parse time from text.
    
    Args:
        text: Text containing time value
        
    Returns:
        Time in hours, or None if not found
        
    Raises:
        ValueError: If text is not a string
    """
    if not isinstance(text, str):
        raise ValueError("Sample ID must be a string")
    return _time_service.parse(text)


def format_time(hours: Optional[float], format_style: Optional[Union[TimeFormat, str]] = None) -> str:
    """
    Convenience function to format time value.
    
    Args:
        hours: Time in hours
        format_style: Format style to use
        
    Returns:
        Formatted time string
    """
    return _time_service.format(hours, format_style)


def parse_formatted_time(time_str: str) -> Optional[float]:
    """
    Convenience function to parse formatted time string.
    
    Args:
        time_str: Formatted time string
        
    Returns:
        Time in hours or None
    """
    return _time_service.parse_formatted(time_str) 