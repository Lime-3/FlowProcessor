"""Parse well identifiers from sample IDs."""
import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class WellParser:
    """Parses plate well identifiers."""
    
    # Standard 96-well plate pattern
    WELL_PATTERN = re.compile(r'([A-H])(\d{1,2})', re.IGNORECASE)
    
    # 384-well plate pattern (A-P, 1-24)
    WELL_384_PATTERN = re.compile(r'([A-P])(\d{1,2})', re.IGNORECASE)
    
    def __init__(self, plate_format: str = '96', unknown_well: str = 'UNK'):
        """
        Initialize well parser.
        
        Args:
            plate_format: Plate format ('96' or '384')
            unknown_well: Value for unknown wells
        """
        self.plate_format = plate_format
        self.unknown_well = unknown_well
        
        if plate_format == '384':
            self.pattern = self.WELL_384_PATTERN
            self.max_row = 'P'
            self.max_col = 24
        else:
            self.pattern = self.WELL_PATTERN
            self.max_row = 'H'
            self.max_col = 12
            
    def parse(self, text: str) -> str:
        """
        Parse well identifier from text.
        
        Args:
            text: Text containing well identifier
            
        Returns:
            Well identifier (e.g., 'A1') or unknown value
        """
        if not text:
            return self.unknown_well
            
        # Search for well pattern
        match = self.pattern.search(text)
        if not match:
            return self.unknown_well
            
        row, col_str = match.groups()
        
        # Validate well
        if self._is_valid_well(row.upper(), int(col_str)):
            return f"{row.upper()}{col_str}"
        else:
            return self.unknown_well
            
    def _is_valid_well(self, row: str, col: int) -> bool:
        """Check if well is valid for plate format."""
        return (
            'A' <= row <= self.max_row and
            1 <= col <= self.max_col
        )
        
    def parse_row_col(self, text: str) -> Optional[Tuple[str, int]]:
        """
        Parse well into row and column.
        
        Args:
            text: Text containing well identifier
            
        Returns:
            Tuple of (row, column) or None
        """
        well = self.parse(text)
        if well == self.unknown_well:
            return None
            
        match = self.pattern.match(well)
        if match:
            row, col_str = match.groups()
            return (row.upper(), int(col_str))
            
        return None
        
    def get_index(self, well: str) -> Optional[int]:
        """
        Get numeric index for well (0-based).
        
        Args:
            well: Well identifier
            
        Returns:
            Numeric index or None
        """
        parsed = self.parse_row_col(well)
        if not parsed:
            return None
            
        row, col = parsed
        row_idx = ord(row) - ord('A')
        
        if self.plate_format == '384':
            return row_idx * 24 + (col - 1)
        else:
            return row_idx * 12 + (col - 1)
            
    def from_index(self, index: int) -> str:
        """
        Convert numeric index to well identifier.
        
        Args:
            index: 0-based well index
            
        Returns:
            Well identifier
        """
        if index < 0:
            return self.unknown_well
            
        if self.plate_format == '384':
            row_idx = index // 24
            col_idx = index % 24
            max_idx = 16 * 24
        else:
            row_idx = index // 12
            col_idx = index % 12
            max_idx = 8 * 12
            
        if index >= max_idx:
            return self.unknown_well
            
        row = chr(ord('A') + row_idx)
        col = col_idx + 1
        
        return f"{row}{col}"