# tests/test_sample_parser.py
"""Comprehensive tests for sample ID parsing."""
import pytest
import pandas as pd
from pathlib import Path
import logging
from io import StringIO
from flowproc.domain.parsing.sample_id_parser import SampleIDParser, ParsedSampleID
from flowproc.core.exceptions import ParsingError as ParseError, ValidationError


class TestSampleIDParser:
    """Test sample ID parsing functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return SampleIDParser(strict=False)
        
    @pytest.fixture
    def strict_parser(self):
        """Create strict parser instance."""
        return SampleIDParser(strict=True)
        
    @pytest.mark.parametrize("sample_id,expected", [
        # Standard format
        ("SP_A1_1.1", ParsedSampleID(1, 1, "SP", "A1")),
        ("BM_B2_2.3", ParsedSampleID(2, 3, "BM", "B2")),
        
        # With time
        ("2h_SP_A1_1.1", ParsedSampleID(1, 1, "SP", "A1", 2.0)),
        ("30min_BM_B2_2.3", ParsedSampleID(2, 3, "BM", "B2", 0.5)),
        ("1day_LN_C3_3.4", ParsedSampleID(3, 4, "LN", "C3", 24.0)),
        
        # Simple format
        ("1.1", ParsedSampleID(1, 1, "UNK", "UNK")),
        ("10.15", ParsedSampleID(10, 15, "UNK", "UNK")),
        
        # With .fcs extension
        ("SP_A1_1.1.fcs", ParsedSampleID(1, 1, "SP", "A1")),
        ("2h_BM_B2_2.3.fcs", ParsedSampleID(2, 3, "BM", "B2", 2.0)),
    ])
    def test_valid_sample_ids(self, parser, sample_id, expected):
        """Test parsing valid sample IDs."""
        result = parser.parse(sample_id)
        assert result == expected
        
    @pytest.mark.parametrize("sample_id", [
        "",
        None,
        123,  # Not a string
        "invalid",
        "SP_1.",  # Missing animal
        "SP_.1",  # Missing group
        "SP_-1.1",  # Negative group
        "SP_1.-1",  # Negative animal
    ])
    def test_invalid_sample_ids(self, parser, strict_parser, sample_id):
        """Test parsing invalid sample IDs."""
        # Non-strict should return None
        assert parser.parse(sample_id) is None
        
        # Strict should raise exception
        with pytest.raises(ParseError):
            strict_parser.parse(sample_id)
            
    def test_property_based_parsing(self, parser):
        """Property-based test for sample ID parsing."""
        # Test with valid sample ID
        sample_id = "SP_A1_1.1"
        result = parser.parse(sample_id)
        
        assert result is not None
        assert result.tissue == "SP"
        assert result.well == "A1"
        assert result.group == 1
        assert result.animal == 1
        
    def test_cache_behavior(self, parser):
        """Test parsing cache."""
        sample_id = "SP_A1_1.1"
        
        # First parse
        result1 = parser.parse(sample_id)
        
        # Second parse should use cache
        result2 = parser.parse(sample_id)
        
        assert result1 == result2
        assert sample_id in parser._cache
        
        # Clear cache
        parser.clear_cache()
        assert sample_id not in parser._cache