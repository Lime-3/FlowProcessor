import pytest
import pandas as pd
from pathlib import Path
from typing import Optional
import logging
from flowproc.domain.parsing import parse_time, extract_group_animal, extract_tissue, get_tissue_full_name, load_and_parse_df, is_likely_id_column, ParsedID, Constants

@pytest.fixture(autouse=True)
def setup_logging_for_tests():
    """Configure logging for all tests."""
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    yield

@pytest.fixture
def static_did_csv(tmp_path: Path) -> Path:
    """Copy DiD.csv to tmp_path for testing."""
    content = """,DiD-A+ | Freq. of Parent (%),DiD-A+ | Median
Spleen_A1_1.1.fcs,0.73,1429
Whole Blood_B1_1.1.fcs,0.89,1103
SP_A2_1.2.fcs,0.65,1384
Whole Blood_B2_4.2.fcs,0.81,889 Gasp
Mean,,
"""
    csv_file = tmp_path / "did.csv"
    csv_file.write_text(content)
    return csv_file

@pytest.fixture
def large_csv(tmp_path: Path) -> Path:
    """Create a large CSV for performance testing (~10k rows)."""
    data = ["SampleID,Count\n" + "\n".join(f"SP_A{i}_{i}.{i}.fcs,{i*10}" for i in range(1, 10001))]
    csv_file = tmp_path / "large.csv"
    csv_file.write_text(data[0])
    return csv_file

@pytest.fixture
def static_day4_csv(tmp_path: Path) -> Path:
    """Copy sample_study_004_day4.csv snippet to tmp_path."""
    content = """,FlowAIGoodEvents/Singlets/Live/T cells/CD4+/CD4+GFP+ | Freq. of Parent (%)
2 hour_A1_1.15.fcs,0.89
5 hour_A7_1.11.fcs,0.85
"""
    csv_file = tmp_path / "day4.csv"
    csv_file.write_text(content)
    return csv_file

@pytest.mark.parametrize("sample_id, expected", [
    ("2 hours_SP_1.1", 2.0),
    ("30 minutes_BM_2.3", 0.5),
    ("1 day_LN_3.2", 24.0),
    ("SP_1.1", None),
    ("", None),
])
def test_parse_time(sample_id: str, expected: Optional[float]) -> None:
    """Test parsing of time from sample IDs."""
    assert parse_time(sample_id) == expected

def test_parse_time_invalid() -> None:
    """Test parse_time with non-string input."""
    with pytest.raises(ValueError, match="Sample ID must be a string"):
        parse_time(123)

@pytest.mark.parametrize("sample_id, expected", [
    ("2 hours_SP_A1_1.1", ParsedID(well="A1", group=1, animal=1, time=2.0)),
    ("BM_2.3", ParsedID(well=Constants.UNKNOWN_WELL.value, group=2, animal=3, time=None)),
    ("spleen_1.2", ParsedID(well=Constants.UNKNOWN_WELL.value, group=1, animal=2, time=None)),
    ("Whole Blood_B1_1.1.fcs", ParsedID(well="B1", group=1, animal=1, time=None)),
])
def test_extract_group_animal(sample_id: str, expected: ParsedID) -> None:
    """Test extraction of group, animal, well, and time from sample IDs."""
    assert extract_group_animal(sample_id) == expected

@pytest.mark.parametrize("sample_id, error_msg", [
    ("invalid", "ID 'invalid' format mismatch"),
    ("SP_-1.2", "Invalid group/animal"),
    ("SP_1.-2", "Invalid group/animal"),
])
def test_extract_group_animal_errors(sample_id: str, error_msg: str) -> None:
    """Test extract_group_animal with invalid inputs."""
    if error_msg.startswith("Invalid"):
        with pytest.raises(ValueError, match=error_msg):
            extract_group_animal(sample_id)
    else:
        assert extract_group_animal(sample_id) is None

def test_extract_group_animal_non_string() -> None:
    """Test extract_group_animal with non-string input."""
    with pytest.raises(ValueError, match="Sample ID must be a string"):
        extract_group_animal(123)

@pytest.mark.parametrize("sample_id, expected", [
    ("SP_A1_1.1", "SP"),
    ("spleen_1.2", "SP"),
    ("whole blood_2.3", "WB"),
    ("invalid", Constants.UNKNOWN_TISSUE.value),
])
def test_extract_tissue(sample_id: str, expected: str) -> None:
    """Test tissue extraction from sample IDs."""
    assert extract_tissue(sample_id) == expected

def test_extract_tissue_non_string() -> None:
    """Test extract_tissue with non-string input."""
    with pytest.raises(ValueError, match="Sample ID must be a string"):
        extract_tissue(123)

@pytest.mark.parametrize("tissue, expected", [
    ("SP", "Spleen"),
    ("WB", "Whole Blood"),
    ("unknown", "unknown"),
    ("", ""),
])
def test_get_tissue_full_name(tissue: str, expected: str) -> None:
    """Test mapping tissue shorthand to full name."""
    assert get_tissue_full_name(tissue) == expected

def test_load_and_parse_df_messy(static_did_csv: Path) -> None:
    """Test loading and parsing a messy CSV (like DiD.csv)."""
    df, sid_col = load_and_parse_df(static_did_csv)
    assert sid_col == "SampleID"
    assert len(df) == 4  # Drops 'Mean'
    assert df['Well'].tolist() == ["A1", "B1", "A2", "B2"]
    assert df['Group'].tolist() == [1, 1, 1, 4]
    assert df['Tissue'].tolist() == ["SP", "WB", "SP", "WB"]

def test_load_and_parse_df_empty(tmp_path: Path) -> None:
    """Test loading an empty CSV."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")
    with pytest.raises(pd.errors.EmptyDataError):
        load_and_parse_df(csv_file)

def test_load_and_parse_df_invalid_ids(tmp_path: Path) -> None:
    """Test CSV with only invalid IDs."""
    content = """SampleID,Count
invalid1,100
invalid2,200
"""
    csv_file = tmp_path / "invalid.csv"
    csv_file.write_text(content)
    with pytest.raises(ValueError, match="No valid sample ID column in .*"):
        load_and_parse_df(csv_file)

def test_load_and_parse_df_duplicates(tmp_path: Path) -> None:
    """Test CSV with duplicate sample IDs."""
    content = """SampleID,Count
SP_A1_1.1,100
SP_A1_1.1,200
"""
    csv_file = tmp_path / "duplicates.csv"
    csv_file.write_text(content)
    with pytest.raises(ValueError, match="Duplicate sample IDs found"):
        load_and_parse_df(csv_file)

def test_load_and_parse_df_negative_values(tmp_path: Path) -> None:
    """Test CSV with negative group/animal numbers."""
    content = """SampleID,Count
SP_A1_-1.2,100
BM_1.-3,200
"""
    csv_file = tmp_path / "negative.csv"
    csv_file.write_text(content)
    with pytest.raises(ValueError):
        load_and_parse_df(csv_file)

def test_is_likely_id_column() -> None:
    """Test ID column likelihood detection."""
    good_series = pd.Series(['SP_A1_1.1.fcs', 'BM_2.3.fcs', pd.NA])
    bad_series = pd.Series([1.0, 'text', pd.NA])
    assert is_likely_id_column(good_series)
    assert not is_likely_id_column(bad_series)

def test_load_and_parse_df_large(large_csv: Path) -> None:
    """Test parsing performance on large CSV (~10k rows)."""
    df, sid_col = load_and_parse_df(large_csv)
    assert sid_col == "SampleID"
    assert len(df) == 10000
    assert df['Well'].iloc[0] == "A1"

def test_load_and_parse_df_day4(static_day4_csv: Path) -> None:
    """Test parsing a time-prefixed CSV (like sample_study_004_day4.csv)."""
    df, sid_col = load_and_parse_df(static_day4_csv)
    assert sid_col == "SampleID"
    assert len(df) == 2
    assert df['Well'].tolist() == ["A1", "A7"]
    assert df['Time'].tolist() == [2.0, 5.0]
    assert df['Tissue'].tolist() == [Constants.UNKNOWN_TISSUE.value, Constants.UNKNOWN_TISSUE.value]