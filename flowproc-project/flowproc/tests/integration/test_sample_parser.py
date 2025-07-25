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
        ("SP_A1_1.1", ParsedSampleID("SP", "A1", 1, 1)),
        ("BM_B2_2.3", ParsedSampleID("BM", "B2", 2, 3)),
        
        # With time
        ("2h_SP_A1_1.1", ParsedSampleID("SP", "A1", 1, 1, 2.0)),
        ("30min_BM_B2_2.3", ParsedSampleID("BM", "B2", 2, 3, 0.5)),
        ("1day_LN_C3_3.4", ParsedSampleID("LN", "C3", 3, 4, 24.0)),
        
        # Simple format
        ("1.1", ParsedSampleID("UNK", "UNK", 1, 1)),
        ("10.15", ParsedSampleID("UNK", "UNK", 10, 15)),
        
        # With .fcs extension
        ("SP_A1_1.1.fcs", ParsedSampleID("SP", "A1", 1, 1)),
        ("2h_BM_B2_2.3.fcs", ParsedSampleID("BM", "B2", 2, 3, 2.0)),
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
    def test_property_based_parsing(self, parser, group, animal, tissue, well):
        """Property-based test for sample ID parsing."""
        sample_id = f"{tissue}_{well}_{group}.{animal}"
        result = parser.parse(sample_id)
        
        assert result is not None
        assert result.tissue == tissue
        assert result.well == well
        assert result.group == group
        assert result.animal == animal
        
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