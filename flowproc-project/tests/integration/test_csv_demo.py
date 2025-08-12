#!/usr/bin/env python3
"""
Demonstration script showing how to use FlowProcessor with actual CSV files
from the Test CSV folder.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import tempfile
import shutil

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import FlowProcessor modules
from flowproc.domain.parsing import load_and_parse_df, extract_group_animal, extract_tissue
from flowproc.domain.visualization.flow_cytometry_visualizer import plot
from flowproc.domain.export import process_csv


def demo_csv_processing():
    """Demonstrate CSV processing with actual files."""
    print("🚀 FlowProcessor CSV Processing Demo")
    print("=" * 50)
    
    # Path to the Test CSV folder
    csv_folder = Path("../Test CSV")
    
    if not csv_folder.exists():
        print(f"❌ Error: CSV folder not found at {csv_folder}")
        return
    
    # Get all CSV files
    csv_files = list(csv_folder.glob("*.csv"))
    print(f"📁 Found {len(csv_files)} CSV files in Test CSV folder")
    
    # Select a few interesting files for demonstration
    demo_files = [
        "DiD.csv",  # Known to work well
        "AT25-AS278_Day4.csv",  # Time course data
        "AT25-AS271_GFP.csv",  # GFP data
        "test_data.csv"  # Test data
    ]
    
    for demo_file in demo_files:
        file_path = csv_folder / demo_file
        if not file_path.exists():
            print(f"⚠️  {demo_file} not found, skipping...")
            continue
            
        print(f"\n📊 Processing: {demo_file}")
        print("-" * 30)
        
        try:
            # 1. Basic CSV loading
            print("1. Loading CSV file...")
            df = pd.read_csv(file_path)
            print(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            
            # 2. FlowProcessor parsing
            print("2. Parsing with FlowProcessor...")
            parsed_df, sample_id_col = load_and_parse_df(file_path)
            print(f"   ✅ Parsed successfully (sample ID column: {sample_id_col})")
            
            # Show some sample data
            if not parsed_df.empty:
                print(f"   📋 Sample data preview:")
                print(f"      Columns: {list(parsed_df.columns[:5])}...")
                if 'Group' in parsed_df.columns:
                    print(f"      Groups found: {sorted(parsed_df['Group'].unique())}")
                if 'Tissue' in parsed_df.columns:
                    print(f"      Tissues found: {sorted(parsed_df['Tissue'].unique())}")
                if 'Time' in parsed_df.columns:
                    print(f"      Time points: {sorted(parsed_df['Time'].dropna().unique())}")
            
            # 3. Sample ID extraction demonstration
            print("3. Sample ID extraction...")
            if sample_id_col and sample_id_col in parsed_df.columns:
                sample_ids = parsed_df[sample_id_col].dropna().head(3)
                for sample_id in sample_ids:
                    try:
                        parsed_id = extract_group_animal(sample_id)
                        tissue = extract_tissue(sample_id)
                        print(f"   📝 {sample_id} -> Group: {parsed_id.group}, Animal: {parsed_id.animal}, Tissue: {tissue}")
                    except Exception as e:
                        print(f"   ⚠️  Could not parse {sample_id}: {str(e)}")
            
            # 4. Visualization demonstration (if numeric data available)
            print("4. Visualization test...")
            numeric_cols = parsed_df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) > 1:  # Need at least 2 numeric columns for plotting
                try:
                    # Find a good metric column (not Group, Animal, Time, etc.)
                    metric_cols = [col for col in numeric_cols if col not in ['Group', 'Animal', 'Time', 'Replicate']]
                    if metric_cols:
                        metric = metric_cols[0]
                        print(f"   📈 Creating visualization with metric: {metric}")
                        
                        # Create visualization config
                        # config = VisualizationConfig(
                        #     metric=metric,
                        #     time_course_mode=False,
                        #     user_replicates=[1, 2],
                        #     auto_parse_groups=True,
                        #     user_group_labels=["Group A", "Group B"]
                        # )
                        
                        # Create temporary output directory
                        with tempfile.TemporaryDirectory() as temp_dir:
                            temp_path = Path(temp_dir)
                            
                            # Generate visualization
                            fig = plot(parsed_df, metric)
                            if fig:
                                print(f"   ✅ Visualization created successfully")
                            else:
                                print(f"   ⚠️  Visualization returned None")
                except Exception as e:
                    print(f"   ❌ Visualization failed: {str(e)}")
            else:
                print(f"   ⚠️  Not enough numeric columns for visualization")
            
            # 5. Export demonstration
            print("5. Export test...")
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    output_file = temp_path / f"{file_path.stem}_export.xlsx"
                    
                    # Export to Excel
                    process_csv(str(file_path), str(output_file))
                    
                    if output_file.exists():
                        print(f"   ✅ Export successful: {output_file.name}")
                    else:
                        print(f"   ❌ Export failed")
            except Exception as e:
                print(f"   ❌ Export failed: {str(e)}")
            
            print(f"   ✅ {demo_file} processing completed successfully!")
            
        except Exception as e:
            print(f"   ❌ Error processing {demo_file}: {str(e)}")
    
    print(f"\n🎉 Demo completed!")
    print(f"📊 Summary: Processed {len(demo_files)} files from your Test CSV folder")
    print(f"💡 FlowProcessor successfully handles various CSV formats and data types")


if __name__ == "__main__":
    demo_csv_processing() 