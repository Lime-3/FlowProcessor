#!/usr/bin/env python3
"""
Debug script to trace through the replicate mapping logic
"""

import sys
import pandas as pd
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from flowproc.domain.parsing import load_and_parse_df

def debug_mapping():
    """Debug the replicate mapping logic step by step."""
    
    # Load the CSV file
    csv_path = Path("../AT25-AS293.csv")
    print(f"Loading CSV file: {csv_path}")
    
    try:
        # Load and parse the CSV
        df, sid_col = load_and_parse_df(csv_path)
        print(f"✅ CSV loaded successfully")
        print(f"   Total rows: {len(df)}")
        
        # Check if we have multiple tissues
        tissues_detected = df['Tissue'].nunique() > 1 if 'Tissue' in df.columns else False
        print(f"   Multiple tissues detected: {tissues_detected}")
        
        # Get unique groups
        groups = sorted([int(g) for g in df['Group'].dropna().unique()])
        print(f"   Groups: {groups}")
        
        # Get unique animals
        unique_animals = sorted([int(a) for a in df['Animal'].dropna().unique()])
        print(f"   Unique animals: {unique_animals}")
        
        # Calculate replicate count
        has_time = 'Time' in df.columns and df['Time'].notna().any()
        print(f"   Has time data: {has_time}")
        
        if tissues_detected:
            # When multiple tissues: count unique animals per group per tissue
            if has_time:
                group_counts = df.groupby(['Time', 'Group', 'Tissue'])['Animal'].nunique()
            else:
                group_counts = df.groupby(['Group', 'Tissue'])['Animal'].nunique()
        else:
            # Single tissue: count unique animals per group
            if has_time:
                group_counts = df.groupby(['Time', 'Group'])['Animal'].nunique()
            else:
                group_counts = df.groupby('Group')['Animal'].nunique()
        
        print(f"   Group counts: {group_counts}")
        n = int(group_counts.max()) if not group_counts.empty else len(unique_animals)
        print(f"   Calculated replicate count (n): {n}")
        
        if group_counts.min() != group_counts.max():
            print(f"   WARNING: Inconsistent counts: min={group_counts.min()}, max={n}")
        
        # Now let's trace through the animal mapping creation
        print(f"\n🔍 Tracing animal mapping creation...")
        
        # Create mapping for animals to replicates (tissue-aware)
        animal_mapping = {}
        
        # Get time points - handle missing Time column
        if 'Time' in df.columns:
            time_points = df['Time'].unique()
            # Convert NaN to None for consistent comparison
            time_points = [None if pd.isna(t) else t for t in time_points]
        else:
            time_points = [None]  # Single time point when no Time column
        
        print(f"   Time points: {time_points}")
        
        for time in time_points:
            if 'Time' in df.columns:
                time_df = df[df['Time'].isna()] if pd.isna(time) else df[df['Time'] == time]
            else:
                time_df = df  # Use all data when no Time column
            
            print(f"   Processing time: {time}, DataFrame rows: {len(time_df)}")
            
            for group in groups:
                group_df = time_df[time_df['Group'] == group]
                print(f"     Group {group}: {len(group_df)} rows")
                
                if tissues_detected:
                    # Handle each tissue separately
                    if group_df.empty:
                        print(f"       Group {group} is empty, skipping")
                        continue
                    for tissue in group_df['Tissue'].unique():
                        tissue_df = group_df[group_df['Tissue'] == tissue]
                        unique_animals = sorted([int(a) for a in tissue_df['Animal'].dropna().unique()])
                        print(f"       Tissue {tissue}: Animals {unique_animals}")
                        
                        for rep_idx, animal in enumerate(unique_animals[:n], 1):
                            key = (time, group, animal, tissue)
                            animal_mapping[key] = rep_idx
                            print(f"         Mapping: {key} -> Replicate {rep_idx}")
                else:
                    # Single tissue handling (original logic)
                    if group_df.empty:
                        print(f"       Group {group} is empty, skipping")
                        continue
                    unique_animals = sorted([int(a) for a in group_df['Animal'].dropna().unique()])
                    tissue = group_df['Tissue'].iloc[0] if 'Tissue' in group_df.columns and not group_df.empty else 'UNK'
                    print(f"       Single tissue {tissue}: Animals {unique_animals}")
                    
                    for rep_idx, animal in enumerate(unique_animals[:n], 1):
                        key = (time, group, animal, tissue)
                        animal_mapping[key] = rep_idx
                        print(f"         Mapping: {key} -> Replicate {rep_idx}")
        
        print(f"\n📋 Final animal mapping:")
        for key, value in sorted(animal_mapping.items()):
            print(f"   {key} -> {value}")
        
        print(f"\n🔍 Testing mapping application...")
        
        # Apply mapping (tissue-aware)
        def get_replicate(row):
            time_val = row['Time'] if 'Time' in row else None
            # Convert NaN to None for consistent comparison
            if pd.isna(time_val):
                time_val = None
            group_val = int(row['Group'])
            animal_val = int(row['Animal'])
            tissue_val = row['Tissue'] if 'Tissue' in row else 'UNK'
            
            key = (time_val, group_val, animal_val, tissue_val)
            replicate = animal_mapping.get(key, None)
            print(f"   Row {row['SampleID']}: {key} -> {replicate}")
            return replicate
        
        df['Replicate'] = df.apply(get_replicate, axis=1)
        
        # Remove rows without replicate assignment
        df_filtered = df.dropna(subset=['Replicate'])
        
        print(f"\n📊 Results:")
        print(f"   Original rows: {len(df)}")
        print(f"   Rows after mapping: {len(df_filtered)}")
        print(f"   Rows dropped: {len(df) - len(df_filtered)}")
        
        # Check group distribution
        group_counts_after = df_filtered['Group'].value_counts().sort_index()
        print(f"   Group distribution after mapping:")
        for group, count in group_counts_after.items():
            print(f"     Group {group}: {count} rows")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_mapping() 