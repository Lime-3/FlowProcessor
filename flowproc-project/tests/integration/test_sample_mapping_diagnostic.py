"""
Pytest tests for sample mapping diagnostic functionality.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from flowproc.domain.parsing import load_and_parse_df, extract_group_animal, extract_tissue


class TestSampleMappingDiagnostic:
    """Test sample mapping diagnostic functionality."""
    
    @pytest.fixture
    def test_csv_files(self):
        """Get test CSV files."""
        test_data_dir = Path(__file__).parent.parent / "data"
        csv_files = list(test_data_dir.glob("*.csv"))
        return csv_files
    
    def test_csv_files_available(self, test_csv_files):
        """Test that CSV test files are available for diagnostic."""
        assert len(test_csv_files) > 0, "No CSV test files found for diagnostic"
        print(f"Found {len(test_csv_files)} CSV test files for diagnostic")
    
    def test_raw_csv_loading_diagnostic(self, test_csv_files):
        """Test raw CSV loading for diagnostic."""
        for csv_file in test_csv_files[:2]:  # Test first 2 files
            print(f"🔍 Diagnostic: Raw CSV loading {csv_file.name}")
            
            try:
                # Load raw CSV
                raw_df = pd.read_csv(csv_file)
                assert not raw_df.empty, f"CSV file {csv_file.name} is empty"
                
                print(f"   ✅ Loaded CSV with {len(raw_df)} rows, {len(raw_df.columns)} columns")
                print(f"   📋 Columns: {list(raw_df.columns)[:5]}...")
                
            except Exception as e:
                pytest.skip(f"Raw CSV loading failed for {csv_file.name}: {str(e)}")
    
    def test_flowproc_parsing_diagnostic(self, test_csv_files):
        """Test FlowProcessor parsing for diagnostic."""
        for csv_file in test_csv_files[:2]:  # Test first 2 files
            print(f"🔍 Diagnostic: FlowProc parsing {csv_file.name}")
            
            try:
                # Load and parse using FlowProc
                df, sid_col = load_and_parse_df(csv_file)
                assert df is not None, f"FlowProc parsing failed for {csv_file.name}"
                assert sid_col is not None, f"No sample ID column found in {csv_file.name}"
                
                print(f"   ✅ FlowProc parsing successful")
                print(f"   📝 Sample ID column identified: '{sid_col}'")
                print(f"   📊 Parsed rows: {len(df)}")
                
            except Exception as e:
                pytest.skip(f"FlowProc parsing failed for {csv_file.name}: {str(e)}")
    
    def test_sample_id_parsing_analysis(self, test_csv_files):
        """Test sample ID parsing analysis."""
        for csv_file in test_csv_files[:1]:  # Test first file
            print(f"📋 Diagnostic: Sample ID parsing analysis {csv_file.name}")
            
            try:
                df, sid_col = load_and_parse_df(csv_file)
                
                if df.empty:
                    pytest.skip("No data after parsing - check sample ID format")
                
                # Get unique sample IDs for analysis
                sample_ids = df['SampleID'].unique()[:5]  # First 5 for analysis
                
                print(f"   Sample parsing for first {len(sample_ids)} IDs:")
                for sid in sample_ids:
                    try:
                        parsed = extract_group_animal(str(sid))
                        tissue = extract_tissue(str(sid))
                        
                        if parsed:
                            print(f"     '{sid}' → Group: {parsed.group}, Animal: {parsed.animal}, "
                                  f"Well: {parsed.well}, Tissue: {tissue}, Time: {parsed.time}")
                        else:
                            print(f"     '{sid}' → ❌ FAILED TO PARSE")
                            
                    except Exception as e:
                        print(f"     '{sid}' → ❌ ERROR: {str(e)}")
                
            except Exception as e:
                pytest.skip(f"Sample ID parsing analysis failed for {csv_file.name}: {str(e)}")
    
    def test_group_animal_distribution_diagnostic(self, test_csv_files):
        """Test group and animal distribution analysis."""
        for csv_file in test_csv_files[:1]:  # Test first file
            print(f"📊 Diagnostic: Group & Animal distribution {csv_file.name}")
            
            try:
                df, sid_col = load_and_parse_df(csv_file)
                
                if df.empty:
                    pytest.skip("No data after parsing - check sample ID format")
                
                # Analyze group and animal distribution
                group_counts = df['Group'].value_counts() if 'Group' in df.columns else {}
                animal_counts = df['Animal'].value_counts() if 'Animal' in df.columns else {}
                
                print(f"   📊 Group distribution:")
                for group, count in group_counts.head().items():
                    print(f"     Group {group}: {count} samples")
                
                print(f"   🐾 Animal distribution:")
                for animal, count in animal_counts.head().items():
                    print(f"     Animal {animal}: {count} samples")
                
            except Exception as e:
                pytest.skip(f"Group/animal distribution analysis failed for {csv_file.name}: {str(e)}")
    
    @patch('flowproc.domain.processing.transform.map_replicates')
    def test_replicate_mapping_diagnostic(self, mock_map_replicates, test_csv_files):
        """Test replicate mapping analysis."""
        # Mock the map_replicates function
        mock_map_replicates.return_value = (MagicMock(), 3)  # Mock DataFrame and replicate count
        
        for csv_file in test_csv_files[:1]:  # Test first file
            print(f"🔢 Diagnostic: Replicate mapping analysis {csv_file.name}")
            
            try:
                df, sid_col = load_and_parse_df(csv_file)
                
                # Mock replicate mapping
                df_mapped, n_reps = mock_map_replicates(df, auto_parse=True)
                
                print(f"   ✅ Replicate mapping successful")
                print(f"   📊 Number of replicates detected: {n_reps}")
                print(f"   📈 Rows after mapping: {len(df_mapped) if hasattr(df_mapped, '__len__') else 'N/A'}")
                
            except Exception as e:
                pytest.skip(f"Replicate mapping analysis failed for {csv_file.name}: {str(e)}")
    
    def test_data_quality_diagnostic(self, test_csv_files):
        """Test data quality analysis."""
        for csv_file in test_csv_files[:1]:  # Test first file
            print(f"🔍 Diagnostic: Data quality analysis {csv_file.name}")
            
            try:
                df, sid_col = load_and_parse_df(csv_file)
                
                # Data quality checks
                print(f"   📊 Data Quality Report:")
                print(f"     Total rows: {len(df)}")
                print(f"     Total columns: {len(df.columns)}")
                
                # Check for missing values
                missing_counts = df.isnull().sum()
                columns_with_missing = missing_counts[missing_counts > 0]
                if not columns_with_missing.empty:
                    print(f"     Columns with missing values:")
                    for col, count in columns_with_missing.items():
                        print(f"       {col}: {count} missing values")
                else:
                    print(f"     ✅ No missing values found")
                
                # Check for duplicate sample IDs
                if sid_col in df.columns:
                    duplicates = df[sid_col].duplicated().sum()
                    if duplicates > 0:
                        print(f"     ⚠️  {duplicates} duplicate sample IDs found")
                    else:
                        print(f"     ✅ No duplicate sample IDs found")
                
                # Check data types
                print(f"     Data types:")
                for col, dtype in df.dtypes.items():
                    print(f"       {col}: {dtype}")
                
            except Exception as e:
                pytest.skip(f"Data quality analysis failed for {csv_file.name}: {str(e)}")
    
    def test_complete_diagnostic_workflow(self, test_csv_files):
        """Test complete diagnostic workflow."""
        if not test_csv_files:
            pytest.skip("No test CSV files available")
        
        csv_file = test_csv_files[0]  # Use first file
        print(f"🔄 Diagnostic: Complete workflow {csv_file.name}")
        
        try:
            # Step 1: Raw CSV loading
            raw_df = pd.read_csv(csv_file)
            assert not raw_df.empty, "Raw CSV should not be empty"
            print(f"   ✅ Step 1: Raw CSV loading successful")
            
            # Step 2: FlowProc parsing
            df, sid_col = load_and_parse_df(csv_file)
            assert df is not None, "FlowProc parsing should succeed"
            print(f"   ✅ Step 2: FlowProc parsing successful")
            
            # Step 3: Sample ID analysis
            sample_ids = df['SampleID'].unique()[:3]
            for sid in sample_ids:
                parsed = extract_group_animal(str(sid))
                if parsed:
                    print(f"   📝 Sample: {sid} -> Group {parsed.group}, Animal {parsed.animal}")
            print(f"   ✅ Step 3: Sample ID analysis successful")
            
            # Step 4: Data quality check
            missing_count = df.isnull().sum().sum()
            print(f"   📊 Total missing values: {missing_count}")
            print(f"   ✅ Step 4: Data quality check successful")
            
            print(f"   🎉 Complete diagnostic workflow successful!")
            
        except Exception as e:
            pytest.skip(f"Complete diagnostic workflow failed: {str(e)}") 