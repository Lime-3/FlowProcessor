"""Format time values for Excel output."""
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class TimeFormatter:
    """Formats time values for display in Excel."""
    
    # Format templates
    FORMATS = {
        'hm': '{h}:{m:02d}',           # 2:30
        'hm_verbose': '{h}h {m}m',     # 2h 30m
        'decimal': '{hours:.1f}h',     # 2.5h
        'auto': 'auto',                 # Automatic selection
    }
    
    def __init__(self, default_format: str = 'hm'):
        """
        Initialize time formatter.
        
        Args:
            default_format: Default format style
        """
        self.default_format = default_format
        
    def format(self, hours: Optional[float], 
               format_style: Optional[str] = None) -> str:
        """
        Format time value.
        
        Args:
            hours: Time in hours
            format_style: Format style to use
            
        Returns:
            Formatted time string
        """
        if hours is None:
            return ""
            
        if format_style is None:
            format_style = self.default_format
            
        if format_style == 'auto':
            return self._auto_format(hours)
        elif format_style == 'hm':
            return self._format_hm(hours)
        elif format_style == 'hm_verbose':
            return self._format_hm_verbose(hours)
        elif format_style == 'decimal':
            return self._format_decimal(hours)
        else:
            return str(hours)
            
    def _auto_format(self, hours: float) -> str:
        """Automatically select best format."""
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
        
    def parse_excel_time(self, time_str: str) -> Optional[float]:
        """
        Parse time string from Excel back to hours.
        
        Args:
            time_str: Time string from Excel
            
        Returns:
            Time in hours or None
        """
        if not time_str:
            return None
            
        time_str = str(time_str).strip()
        
        # Try H:MM format
        if ':' in time_str:
            try:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours + minutes / 60
            except (ValueError, IndexError):
                pass
                
        # Try decimal format (e.g., "2.5h")
        if time_str.endswith('h'):
            try:
                return float(time_str[:-1])
            except ValueError:
                pass
                
        # Try minutes format (e.g., "30min")
        if time_str.endswith('min'):
            try:
                return float(time_str[:-3]) / 60
            except ValueError:
                pass
                
        # Try days format (e.g., "2d" or "2.5d")
        if time_str.endswith('d'):
            try:
                return float(time_str[:-1]) * 24
            except ValueError:
                pass
                
        # Try as plain number (assume hours)
        try:
            return float(time_str)
        except ValueError:
            logger.warning(f"Could not parse time: {time_str}")
            return None
            
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