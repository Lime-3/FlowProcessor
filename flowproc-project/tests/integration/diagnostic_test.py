#!/usr/bin/env python3
"""
Diagnostic script to test parsing and replicate mapping with AT25-AS293.csv
"""

import sys
import pandas as pd
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from flowproc.domain.parsing import load_and_parse_df
from flowproc.domain.processing.transform import map_replicates

def test_parsing_and_mapping():
    """Test the parsing and replicate mapping logic."""
    
    # Load the CSV file
    csv_path = Path("../AT25-AS293.csv")
    print(f"Loading CSV file: {csv_path}")
    
    try:
        # Load and parse the CSV
        df, sid_col = load_and_parse_df(csv_path)
        print(f"✅ CSV loaded successfully")
        print(f"   Sample ID column: {sid_col}")
        print(f"   Total rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}")
        
        # Check what groups were parsed
        if 'Group' in df.columns:
            groups_found = sorted(df['Group'].unique())
            print(f"   Groups found: {groups_found}")
            
            # Check group distribution
            group_counts = df['Group'].value_counts().sort_index()
            print(f"   Group distribution:")
            for group, count in group_counts.items():
                print(f"     Group {group}: {count} rows")
        
        # Check tissues
        if 'Tissue' in df.columns:
            tissues_found = df['Tissue'].unique()
            print(f"\n🔍 Tissue analysis:")
            print(f"   Tissues found: {tissues_found}")
            print(f"   Number of unique tissues: {len(tissues_found)}")
            
            tissue_counts = df['Tissue'].value_counts()
            print(f"   Tissue distribution:")
            for tissue, count in tissue_counts.items():
                print(f"     {tissue}: {count} rows")
        
        # Check animals per group
        if 'Animal' in df.columns:
            print(f"\n🔍 Animal distribution per group:")
            for group in sorted(df['Group'].unique()):
                group_df = df[df['Group'] == group]
                animals = sorted(group_df['Animal'].unique())
                print(f"   Group {group}: Animals {animals} ({len(animals)} animals)")
        
        # Test replicate mapping
        print(f"\n🔍 Testing replicate mapping...")
        try:
            df_mapped, replicate_count = map_replicates(
                df, 
                auto_parse=True,
                user_replicates=None,
                user_groups=None
            )
            
            print(f"✅ Replicate mapping successful")
            print(f"   Replicate count: {replicate_count}")
            print(f"   Rows after mapping: {len(df_mapped)}")
            
            # Check which groups survived the mapping
            if 'Group' in df_mapped.columns:
                groups_after_mapping = sorted(df_mapped['Group'].unique())
                print(f"   Groups after mapping: {groups_after_mapping}")
                
                # Check group distribution after mapping
                group_counts_after = df_mapped['Group'].value_counts().sort_index()
                print(f"   Group distribution after mapping:")
                for group, count in group_counts_after.items():
                    print(f"     Group {group}: {count} rows")
            
            # Check replicates per group
            if 'Replicate' in df_mapped.columns:
                print(f"\n🔍 Replicate distribution per group:")
                for group in sorted(df_mapped['Group'].unique()):
                    group_df = df_mapped[df_mapped['Group'] == group]
                    replicates = sorted(group_df['Replicate'].unique())
                    print(f"   Group {group}: Replicates {replicates} ({len(replicates)} replicates)")
                    
        except Exception as e:
            print(f"❌ Replicate mapping failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parsing_and_mapping() 