"""
Unit tests for the consolidated TimeService.

Tests all time parsing and formatting functionality that was previously
duplicated across multiple modules.
"""

import pytest
from flowproc.domain.parsing.time_service import TimeService, TimeFormat, parse_time, format_time, parse_formatted_time


class TestTimeService:
    """Test the comprehensive TimeService functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TimeService()
        
    def test_parse_timecourse_patterns(self):
        """Test parsing timecourse patterns like 'Day 3'."""
        test_cases = [
            ("Day 3", 72.0),
            ("day 3", 72.0),
            ("DAY 3", 72.0),
            ("Day 1.5", 36.0),
            ("day_3", 72.0),
            ("Day 3 ", 72.0),
            (" Day 3", 72.0),
        ]
        
        for text, expected in test_cases:
            result = self.service.parse(text)
            assert result == expected, f"Failed to parse '{text}': expected {expected}, got {result}"
            
    def test_parse_filename_patterns(self):
        """Test parsing time from filenames."""
        test_cases = [
            ("AT25-AS278_Day 3.csv", 72.0),
            ("AT25-AS278_Day3.csv", 72.0),
            ("AT25-AS278_3 Day.csv", 72.0),
            ("AT25-AS278_2 hour.csv", 2.0),
            ("AT25-AS278_30 min.csv", 0.5),
            ("AT25-AS278_1.5 days.csv", 36.0),
        ]
        
        for text, expected in test_cases:
            result = self.service.parse(text)
            assert result == expected, f"Failed to parse '{text}': expected {expected}, got {result}"
            
    def test_parse_prefix_patterns(self):
        """Test parsing time prefix patterns."""
        test_cases = [
            ("2 hour_SP_", 2.0),
            ("30 min_SP_", 0.5),
            ("1.5 days_SP_", 36.0),
            ("2h_SP_", 2.0),
            ("30m_SP_", 0.5),
        ]
        
        for text, expected in test_cases:
            result = self.service.parse(text)
            assert result == expected, f"Failed to parse '{text}': expected {expected}, got {result}"
            
    def test_parse_general_patterns(self):
        """Test parsing general time patterns."""
        test_cases = [
            ("Sample_2 hour", 2.0),
            ("Sample_30 min", 0.5),
            ("Sample_1.5 days", 36.0),
            ("Sample_2h", 2.0),
            ("Sample_30m", 0.5),
            ("Sample_1.5d", 36.0),
        ]
        
        for text, expected in test_cases:
            result = self.service.parse(text)
            assert result == expected, f"Failed to parse '{text}': expected {expected}, got {result}"
            
    def test_parse_formatted_strings(self):
        """Test parsing formatted time strings."""
        test_cases = [
            ("2:30", 2.5),
            ("2.5h", 2.5),
            ("30min", 0.5),
            ("1.5d", 36.0),
            ("2.5", 2.5),  # Plain number
        ]
        
        for text, expected in test_cases:
            result = self.service.parse_formatted(text)
            assert result == expected, f"Failed to parse formatted '{text}': expected {expected}, got {result}"
            
    def test_parse_ranges(self):
        """Test parsing time ranges."""
        test_cases = [
            ("0-24h", (0.0, 24.0)),
            ("1-2 days", (24.0, 48.0)),
            ("0.5-1.5 hours", (0.5, 1.5)),
            ("30-90 min", (0.5, 1.5)),
        ]
        
        for text, expected in test_cases:
            result = self.service.parse_range(text)
            assert result == expected, f"Failed to parse range '{text}': expected {expected}, got {result}"
            
    def test_format_time(self):
        """Test time formatting."""
        # Test HM format
        assert self.service.format(2.5) == "2:30"
        assert self.service.format(2.0) == "2:00"
        assert self.service.format(0.5) == "0:30"
        
        # Test HM_VERBOSE format
        assert self.service.format(2.5, TimeFormat.HM_VERBOSE) == "2h 30m"
        assert self.service.format(2.0, TimeFormat.HM_VERBOSE) == "2h"
        assert self.service.format(0.5, TimeFormat.HM_VERBOSE) == "0h 30m"
        
        # Test DECIMAL format
        assert self.service.format(2.5, TimeFormat.DECIMAL) == "2.5h"
        assert self.service.format(0.5, TimeFormat.DECIMAL) == "0.5h"
        
        # Test AUTO format
        assert self.service.format(0.5, TimeFormat.AUTO) == "30min"
        assert self.service.format(2.5, TimeFormat.AUTO) == "2:30"
        assert self.service.format(48.0, TimeFormat.AUTO) == "2d"
        
    def test_excel_serial_conversion(self):
        """Test Excel serial time conversion."""
        hours = 6.0  # 6 hours
        serial = self.service.to_excel_serial(hours)
        assert serial == 0.25  # 6/24 = 0.25
        
        # Convert back
        converted_hours = self.service.from_excel_serial(serial)
        assert converted_hours == hours
        
    def test_validate_time(self):
        """Test time validation."""
        assert self.service.validate_time(0.0) == True
        assert self.service.validate_time(24.0) == True
        assert self.service.validate_time(1000.0) == True
        assert self.service.validate_time(-1.0) == False
        assert self.service.validate_time(10000.0) == False
        assert self.service.validate_time("invalid") == False
        
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # None and empty strings
        assert self.service.parse(None) is None
        assert self.service.parse("") is None
        assert self.service.parse("   ") is None
        
        # Invalid formats
        assert self.service.parse("invalid") is None
        assert self.service.parse("no_time_here") is None
        
        # Invalid numeric values
        assert self.service.parse("abc hour") is None
        assert self.service.parse("2 invalid_unit") is None
        
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test parse_time
        assert parse_time("Day 3") == 72.0
        assert parse_time("2 hour") == 2.0
        # Test that None raises ValueError (backward compatibility)
        with pytest.raises(ValueError, match="Sample ID must be a string"):
            parse_time(None)
        
        # Test format_time
        assert format_time(2.5) == "2:30"
        assert format_time(2.5, TimeFormat.HM_VERBOSE) == "2h 30m"
        assert format_time(None) == ""
        
        # Test parse_formatted_time
        assert parse_formatted_time("2:30") == 2.5
        assert parse_formatted_time("2.5h") == 2.5
        assert parse_formatted_time("") is None
        
    def test_backward_compatibility(self):
        """Test that the new service maintains backward compatibility."""
        # Test that old patterns still work
        old_patterns = [
            ("2 hour_SP_", 2.0),
            ("Day 3", 72.0),
            ("30 min", 0.5),
            ("1.5 days", 36.0),
        ]
        
        for text, expected in old_patterns:
            result = self.service.parse(text)
            assert result == expected, f"Backward compatibility failed for '{text}'"
            
    def test_comprehensive_unit_conversions(self):
        """Test all supported time units."""
        unit_tests = [
            # Hours
            ("1h", 1.0), ("1hr", 1.0), ("1hrs", 1.0), ("1hour", 1.0), ("1hours", 1.0),
            # Minutes
            ("60m", 1.0), ("60min", 1.0), ("60mins", 1.0), ("60minute", 1.0), ("60minutes", 1.0),
            # Days
            ("1d", 24.0), ("1day", 24.0), ("1days", 24.0),
            # Seconds
            ("3600s", 1.0), ("3600sec", 1.0), ("3600secs", 1.0), ("3600second", 1.0), ("3600seconds", 1.0),
        ]
        
        for text, expected in unit_tests:
            result = self.service.parse(text)
            assert result == expected, f"Unit conversion failed for '{text}': expected {expected}, got {result}"


class TestTimeServiceIntegration:
    """Test integration with existing code patterns."""
    
    def test_sample_id_parsing_integration(self):
        """Test that TimeService works with sample ID parsing patterns."""
        service = TimeService()
        
        # Test patterns from the original time_parser.py
        sample_ids = [
            "SP_1.2_2 hour",
            "SP_1.2_Day 3",
            "SP_1.2_30 min",
            "AT25-AS278_Day 3.csv",
            "AT25-AS278_2 hour.csv",
        ]
        
        expected_times = [2.0, 72.0, 0.5, 72.0, 2.0]
        
        for sample_id, expected_time in zip(sample_ids, expected_times):
            result = service.parse(sample_id)
            assert result == expected_time, f"Integration test failed for '{sample_id}'"
            
    def test_excel_formatting_integration(self):
        """Test that TimeService works with Excel formatting patterns."""
        service = TimeService()
        
        # Test Excel time formats
        excel_times = [
            ("2:30", 2.5),
            ("0:45", 0.75),
            ("1:00", 1.0),
        ]
        
        for formatted, expected in excel_times:
            result = service.parse_formatted(formatted)
            assert result == expected, f"Excel integration failed for '{formatted}'"
            
    def test_persistence_integration(self):
        """Test that TimeService works with persistence layer patterns."""
        service = TimeService()
        
        # Test simple time parsing (from data_io.py)
        simple_times = [
            ("2:30", 2.5),
            ("2.5", 2.5),
            ("", None),
            (None, None),
        ]
        
        for time_str, expected in simple_times:
            result = service.parse_formatted(time_str)
            assert result == expected, f"Persistence integration failed for '{time_str}'" 