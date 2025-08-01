"""Format time values for Excel output."""
from typing import Optional, Union
import logging

from ..parsing.time_service import TimeService, TimeFormat, parse_formatted_time

logger = logging.getLogger(__name__)


class TimeFormatter:
    """Formats time values for display in Excel."""
    
    def __init__(self, default_format: TimeFormat = TimeFormat.HM):
        """
        Initialize time formatter.
        
        Args:
            default_format: Default format style
        """
        self.default_format = default_format
        self.time_service = TimeService(default_format=default_format)
        
    def format(self, hours: Optional[float], 
               format_style: Optional[Union[TimeFormat, str]] = None) -> str:
        """
        Format time value.
        
        Args:
            hours: Time in hours
            format_style: Format style to use
            
        Returns:
            Formatted time string
        """
        return self.time_service.format(hours, format_style)
        
    def parse_excel_time(self, time_str: str) -> Optional[float]:
        """
        Parse time string from Excel back to hours.
        
        Args:
            time_str: Time string from Excel
            
        Returns:
            Time in hours or None
        """
        return parse_formatted_time(time_str)
            
    def to_excel_serial(self, hours: float) -> float:
        """
        Convert hours to Excel serial time.
        
        Excel stores times as fractions of a day.
        
        Args:
            hours: Time in hours
            
        Returns:
            Excel serial time value
        """
        return self.time_service.to_excel_serial(hours)
        
    def from_excel_serial(self, serial: float) -> float:
        """
        Convert Excel serial time to hours.
        
        Args:
            serial: Excel serial time value
            
        Returns:
            Time in hours
        """
        return self.time_service.from_excel_serial(serial)