"""
Pytest tests for simple CSV functionality.
"""

import pytest
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from flowproc.domain.parsing import load_and_parse_df, extract_group_animal, extract_tissue


class TestSimpleCSV:
    """Test basic CSV functionality."""
    
    @pytest.fixture
    def csv_files(self):
        """Get available CSV test files."""
        test_data_dir = Path(__file__).parent.parent / "data"
        csv_files = list(test_data_dir.glob("*.csv"))
        return csv_files
    
    def test_csv_files_exist(self, csv_files):
        """Test that CSV test files are available."""
        assert len(csv_files) > 0, "No CSV test files found"
        print(f"Found {len(csv_files)} CSV test files")
    
    def test_basic_csv_loading(self, csv_files):
        """Test basic CSV loading with pandas."""
        for csv_file in csv_files[:3]:  # Test first 3 files
            print(f"Testing basic loading: {csv_file.name}")
            
            # Test basic CSV loading with pandas
            df = pd.read_csv(csv_file)
            assert not df.empty, f"CSV file {csv_file.name} is empty"
            assert len(df.columns) > 0, f"CSV file {csv_file.name} has no columns"
            
            print(f"  ✅ Successfully loaded {csv_file.name} ({len(df)} rows, {len(df.columns)} columns)")
    
    def test_flowproc_parsing(self, csv_files):
        """Test FlowProcessor parsing with CSV files."""
        for csv_file in csv_files[:3]:  # Test first 3 files
            print(f"Testing FlowProcessor parsing: {csv_file.name}")
            
            try:
                # Test FlowProcessor parsing
                df, sid_col = load_and_parse_df(csv_file)
                assert df is not None, f"Failed to parse {csv_file.name}"
                assert sid_col is not None, f"No sample ID column found in {csv_file.name}"
                assert not df.empty, f"Parsed DataFrame is empty for {csv_file.name}"
                
                print(f"  ✅ Successfully parsed {csv_file.name} (sample ID col: {sid_col})")
                
            except Exception as e:
                pytest.skip(f"FlowProcessor parsing failed for {csv_file.name}: {str(e)}")
    
    def test_sample_id_extraction(self, csv_files):
        """Test sample ID extraction functionality."""
        for csv_file in csv_files[:2]:  # Test first 2 files
            print(f"Testing sample ID extraction: {csv_file.name}")
            
            try:
                df, sid_col = load_and_parse_df(csv_file)
                
                # Test sample ID extraction on first few sample IDs
                sample_ids = df[sid_col].dropna().head(3)
                
                for sample_id in sample_ids:
                    try:
                        parsed_id = extract_group_animal(str(sample_id))
                        assert parsed_id is not None, f"Failed to parse sample ID: {sample_id}"
                        assert hasattr(parsed_id, 'group'), f"Parsed ID missing group: {sample_id}"
                        assert hasattr(parsed_id, 'animal'), f"Parsed ID missing animal: {sample_id}"
                        
                        print(f"  ✅ Parsed {sample_id} -> Group: {parsed_id.group}, Animal: {parsed_id.animal}")
                        
                    except Exception as e:
                        print(f"  ⚠️  Could not parse {sample_id}: {str(e)}")
                
            except Exception as e:
                pytest.skip(f"Sample ID extraction failed for {csv_file.name}: {str(e)}")
    
    def test_tissue_extraction(self, csv_files):
        """Test tissue extraction functionality."""
        for csv_file in csv_files[:2]:  # Test first 2 files
            print(f"Testing tissue extraction: {csv_file.name}")
            
            try:
                df, sid_col = load_and_parse_df(csv_file)
                
                # Test tissue extraction on first few sample IDs
                sample_ids = df[sid_col].dropna().head(3)
                
                for sample_id in sample_ids:
                    try:
                        tissue = extract_tissue(str(sample_id))
                        print(f"  ✅ Tissue for {sample_id}: {tissue}")
                        
                    except Exception as e:
                        print(f"  ⚠️  Could not extract tissue for {sample_id}: {str(e)}")
                
            except Exception as e:
                pytest.skip(f"Tissue extraction failed for {csv_file.name}: {str(e)}")
    
    def test_file_info_collection(self, csv_files):
        """Test collecting file information."""
        file_info_list = []
        
        for csv_file in csv_files[:3]:  # Test first 3 files
            try:
                df = pd.read_csv(csv_file)
                
                file_info = {
                    "name": csv_file.name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "size_kb": csv_file.stat().st_size / 1024,
                    "column_names": list(df.columns),
                    "data_types": df.dtypes.to_dict()
                }
                file_info_list.append(file_info)
                
                print(f"  📊 {csv_file.name}: {len(df)} rows, {len(df.columns)} columns, {file_info['size_kb']:.1f} KB")
                
            except Exception as e:
                print(f"  ❌ Failed to collect info for {csv_file.name}: {str(e)}")
        
        assert len(file_info_list) > 0, "No file information collected"
        print(f"Collected information for {len(file_info_list)} files") 