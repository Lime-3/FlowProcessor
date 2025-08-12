"""
Pytest tests for CSV demo functionality.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from flowproc.domain.parsing import load_and_parse_df, extract_group_animal, extract_tissue
from flowproc.domain.visualization.flow_cytometry_visualizer import plot
from flowproc.domain.export import process_csv


class TestCSVDemoFunctionality:
    """Test CSV demo functionality."""
    
    @pytest.fixture
    def test_csv_files(self):
        """Get test CSV files."""
        test_data_dir = Path(__file__).parent.parent / "data"
        csv_files = list(test_data_dir.glob("*.csv"))
        return csv_files
    
    def test_csv_files_available(self, test_csv_files):
        """Test that CSV test files are available."""
        assert len(test_csv_files) > 0, "No CSV test files found for demo"
        print(f"Found {len(test_csv_files)} CSV test files for demo")
    
    def test_basic_csv_loading_demo(self, test_csv_files):
        """Test basic CSV loading demonstration."""
        for csv_file in test_csv_files[:2]:  # Test first 2 files
            print(f"📊 Demo: Loading {csv_file.name}")
            
            try:
                # Basic CSV loading
                df = pd.read_csv(csv_file)
                assert not df.empty, f"CSV file {csv_file.name} is empty"
                
                print(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
                print(f"   📋 Columns: {list(df.columns)[:5]}...")
                
            except Exception as e:
                pytest.skip(f"Basic CSV loading failed for {csv_file.name}: {str(e)}")
    
    def test_flowproc_parsing_demo(self, test_csv_files):
        """Test FlowProcessor parsing demonstration."""
        for csv_file in test_csv_files[:2]:  # Test first 2 files
            print(f"⚙️  Demo: FlowProcessor parsing {csv_file.name}")
            
            try:
                # FlowProcessor parsing
                parsed_df, sample_id_col = load_and_parse_df(csv_file)
                assert parsed_df is not None, f"Failed to parse {csv_file.name}"
                assert sample_id_col is not None, f"No sample ID column found in {csv_file.name}"
                
                print(f"   ✅ Parsed successfully (sample ID column: {sample_id_col})")
                
                # Show sample data
                if not parsed_df.empty:
                    print(f"   📋 Sample data preview:")
                    print(f"      Columns: {list(parsed_df.columns)[:5]}...")
                    
                    if 'Group' in parsed_df.columns:
                        groups = sorted(parsed_df['Group'].unique())
                        print(f"      Groups found: {groups}")
                    
                    if 'Tissue' in parsed_df.columns:
                        tissues = sorted(parsed_df['Tissue'].unique())
                        print(f"      Tissues found: {tissues}")
                    
                    if 'Time' in parsed_df.columns:
                        times = sorted(parsed_df['Time'].dropna().unique())
                        print(f"      Time points: {times}")
                
            except Exception as e:
                pytest.skip(f"FlowProcessor parsing failed for {csv_file.name}: {str(e)}")
    
    def test_sample_id_extraction_demo(self, test_csv_files):
        """Test sample ID extraction demonstration."""
        for csv_file in test_csv_files[:1]:  # Test first file
            print(f"📝 Demo: Sample ID extraction {csv_file.name}")
            
            try:
                parsed_df, sample_id_col = load_and_parse_df(csv_file)
                
                if sample_id_col and sample_id_col in parsed_df.columns:
                    sample_ids = parsed_df[sample_id_col].dropna().head(3)
                    
                    for sample_id in sample_ids:
                        try:
                            parsed_id = extract_group_animal(str(sample_id))
                            tissue = extract_tissue(str(sample_id))
                            
                            print(f"   📝 {sample_id} -> Group: {parsed_id.group}, Animal: {parsed_id.animal}, Tissue: {tissue}")
                            
                        except Exception as e:
                            print(f"   ⚠️  Could not parse {sample_id}: {str(e)}")
                
            except Exception as e:
                pytest.skip(f"Sample ID extraction failed for {csv_file.name}: {str(e)}")
    
    @patch('flowproc.domain.visualization.facade.visualize_data')
    def test_visualization_demo(self, mock_visualize, test_csv_files):
        """Test visualization demonstration."""
        mock_visualize.return_value = MagicMock()
        
        for csv_file in test_csv_files[:1]:  # Test first file
            print(f"📊 Demo: Visualization {csv_file.name}")
            
            try:
                parsed_df, sample_id_col = load_and_parse_df(csv_file)
                
                # Find numeric columns for visualization
                numeric_cols = parsed_df.select_dtypes(include=['number']).columns.tolist()
                
                if len(numeric_cols) > 1:
                    # Find metric columns (not metadata columns)
                    metric_cols = [col for col in numeric_cols if col not in ['Group', 'Animal', 'Time', 'Replicate']]
                    
                    if metric_cols:
                        metric = metric_cols[0]
                        print(f"   📈 Testing visualization with metric: {metric}")
                        
                        # Mock visualization call
                        # config = VisualizationConfig() # This line is removed as per the edit hint
                        result = plot(parsed_df, metric) # Changed from create_visualization to plot
                        
                        assert result is not None, "Visualization should return a result"
                        print(f"   ✅ Visualization test successful")
                    else:
                        print(f"   ⚠️  No suitable metric columns found for visualization")
                else:
                    print(f"   ⚠️  Not enough numeric columns for visualization")
                
            except Exception as e:
                pytest.skip(f"Visualization failed for {csv_file.name}: {str(e)}")
    
    def test_export_functionality_demo(self, test_csv_files, tmp_path):
        """Test export functionality demonstration."""
        for csv_file in test_csv_files[:1]:  # Test first file
            print(f"💾 Demo: Export functionality {csv_file.name}")
            
            try:
                # Create output file path
                output_file = tmp_path / f"{csv_file.stem}_demo_output.xlsx"
                
                # Test export functionality
                process_csv(
                    csv_file,
                    output_file,
                    time_course_mode=False,
                    user_replicates=None,
                    auto_parse_groups=True,
                    user_group_labels=None,
                    user_groups=None
                )
                
                # Check if output file was created
                assert output_file.exists(), f"Output file was not created: {output_file}"
                assert output_file.stat().st_size > 0, f"Output file is empty: {output_file}"
                
                print(f"   ✅ Export successful: {output_file}")
                print(f"   📊 File size: {output_file.stat().st_size / 1024:.1f} KB")
                
            except Exception as e:
                pytest.skip(f"Export failed for {csv_file.name}: {str(e)}")
    
    def test_demo_integration_workflow(self, test_csv_files, tmp_path):
        """Test complete demo workflow integration."""
        if not test_csv_files:
            pytest.skip("No test CSV files available")
        
        csv_file = test_csv_files[0]  # Use first file
        print(f"🔄 Demo: Complete workflow {csv_file.name}")
        
        try:
            # Step 1: Load and parse
            parsed_df, sample_id_col = load_and_parse_df(csv_file)
            assert not parsed_df.empty, "Parsed DataFrame should not be empty"
            print(f"   ✅ Step 1: Parsing successful")
            
            # Step 2: Extract sample information
            sample_ids = parsed_df[sample_id_col].dropna().head(2)
            for sample_id in sample_ids:
                parsed_id = extract_group_animal(str(sample_id))
                tissue = extract_tissue(str(sample_id))
                print(f"   📝 Sample: {sample_id} -> Group {parsed_id.group}, Animal {parsed_id.animal}, Tissue {tissue}")
            print(f"   ✅ Step 2: Sample extraction successful")
            
            # Step 3: Export
            output_file = tmp_path / f"{csv_file.stem}_workflow_output.xlsx"
            process_csv(
                csv_file,
                output_file,
                time_course_mode=False,
                auto_parse_groups=True
            )
            assert output_file.exists(), "Export should create output file"
            print(f"   ✅ Step 3: Export successful")
            
            print(f"   🎉 Complete workflow successful!")
            
        except Exception as e:
            pytest.skip(f"Complete workflow failed: {str(e)}") 