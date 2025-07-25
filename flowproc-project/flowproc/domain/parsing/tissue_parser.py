"""Parse and map tissue identifiers."""
from typing import Dict, List, Optional, Set
import re
import logging

logger = logging.getLogger(__name__)


class TissueParser:
    """Parses and maps tissue identifiers."""
    
    # Standard tissue mappings
    TISSUE_MAP: Dict[str, str] = {
        'SP': 'Spleen',
        'BM': 'Bone Marrow',
        'WB': 'Whole Blood',
        'PB': 'Peripheral Blood',
        'LN': 'Lymph Node',
        'TH': 'Thymus',
        'LI': 'Liver',
        'LU': 'Lung',
        'KD': 'Kidney',
        'BR': 'Brain',
        'HE': 'Heart',
        'SK': 'Skin',
        'MU': 'Muscle',
        'AD': 'Adipose',
        'PA': 'Pancreas',
        'IN': 'Intestine',
    }
    
    # Reverse mapping for full names to codes
    REVERSE_MAP: Dict[str, str] = {
        v.lower(): k for k, v in TISSUE_MAP.items()
    }
    
    # Additional patterns for tissue detection
    TISSUE_PATTERNS: Dict[str, List[re.Pattern]] = {
        'SP': [re.compile(r'\bspleen\b', re.I)],
        'BM': [re.compile(r'\bbone\s*marrow\b', re.I)],
        'WB': [re.compile(r'\bwhole\s*blood\b', re.I)],
        'PB': [re.compile(r'\bperipheral\s*blood\b', re.I)],
        'LN': [re.compile(r'\blymph\s*node\b', re.I)],
    }
    
    def __init__(self, unknown_code: str = 'UNK'):
        """
        Initialize tissue parser.
        
        Args:
            unknown_code: Code to use for unknown tissues
        """
        self.unknown_code = unknown_code
        self._cache: Dict[str, str] = {}
        
    def parse(self, text: str) -> str:
        """
        Parse tissue code from text.
        
        Args:
            text: Text containing tissue identifier
            
        Returns:
            Tissue code
        """
        if not text:
            return self.unknown_code
            
        # Check cache
        if text in self._cache:
            return self._cache[text]
            
        # Try direct code match
        code = self._extract_code(text)
        
        if code == self.unknown_code:
            # Try pattern matching
            code = self._match_patterns(text)
            
        # Cache result
        self._cache[text] = code
        return code
        
    def _extract_code(self, text: str) -> str:
        """Extract tissue code from text."""
        # Check if text starts with a known code
        text_upper = text.upper()
        
        for code in self.TISSUE_MAP:
            if text_upper.startswith(code + '_') or text_upper.startswith(code + ' '):
                return code
                
        # Check if entire text is a code
        if text_upper in self.TISSUE_MAP:
            return text_upper
            
        # Check reverse mapping (exact matches)
        text_lower = text.lower()
        if text_lower in self.REVERSE_MAP:
            return self.REVERSE_MAP[text_lower]
            
        # Check for partial matches in text
        for full_name, code in self.REVERSE_MAP.items():
            if full_name in text_lower:
                return code
                
        return self.unknown_code
        
    def _match_patterns(self, text: str) -> str:
        """Match tissue patterns in text."""
        for code, patterns in self.TISSUE_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(text):
                    return code
                    
        return self.unknown_code
        
    def get_full_name(self, code: str) -> str:
        """
        Get full tissue name from code.
        
        Args:
            code: Tissue code
            
        Returns:
            Full tissue name
        """
        return self.TISSUE_MAP.get(code.upper(), code)
        
    def get_all_codes(self) -> Set[str]:
        """Get all known tissue codes."""
        return set(self.TISSUE_MAP.keys())
        
    def add_mapping(self, code: str, full_name: str) -> None:
        """
        Add custom tissue mapping.
        
        Args:
            code: Tissue code
            full_name: Full tissue name
        """
        self.TISSUE_MAP[code.upper()] = full_name
        self.REVERSE_MAP[full_name.lower()] = code.upper()
        self._cache.clear()  # Clear cache when mappings change

def extract_tissue(text: str) -> str:
    """Convenience function to parse tissue code from text."""
    if not isinstance(text, str):
        raise ValueError("Sample ID must be a string")
    return TissueParser().parse(text)

def get_tissue_full_name(code: str) -> str:
    """Convenience function to get full tissue name from code."""
    if not isinstance(code, str):
        return code
    return TissueParser().get_full_name(code)