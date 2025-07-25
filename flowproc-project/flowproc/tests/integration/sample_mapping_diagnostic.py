#!/usr/bin/env python3
"""
Sample Mapping Diagnostic Tool

This script helps diagnose issues with sample ID parsing and replicate mapping
in FlowProcessor. Run it on your CSV file to see exactly how sample IDs are
being parsed and mapped to groups, animals, and replicates.

Usage:
    python sample_mapping_diagnostic.py path/to/your/file.csv
"""

import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

# Import FlowProc modules
sys.path.insert(0, str(Path(__file__).parent / "flowproc"))
from flowproc.domain.parsing import load_and_parse_df, extract_group_animal, extract_tissue
from flowproc.transform import map_replicates


def analyze_sample_parsing(csv_path: str) -> None:
    """Analyze how sample IDs are being parsed."""
    print(f"🔍 SAMPLE MAPPING DIAGNOSTIC")
    print(f"=" * 60)
    print(f"File: {csv_path}")
    print()
    
    # Load raw CSV
    try:
        raw_df = pd.read_csv(csv_path)
        print(f"✅ Loaded CSV with {len(raw_df)} rows, {len(raw_df.columns)} columns")
        print(f"   Columns: {list(raw_df.columns)[:5]}...")
        print()
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return
    
    # Load and parse using FlowProc
    try:
        df, sid_col = load_and_parse_df(Path(csv_path))
        print(f"✅ FlowProc parsing successful")
        print(f"   Sample ID column identified: '{sid_col}'")
        print(f"   Parsed rows: {len(df)}")
        print()
    except Exception as e:
        print(f"❌ FlowProc parsing failed: {e}")
        return
    
    if df.empty:
        print("❌ No data after parsing - check your sample ID format")
        return
    
    # Show sample ID parsing details
    print("📋 SAMPLE ID PARSING ANALYSIS")
    print("-" * 40)
    
    # Get unique sample IDs for analysis
    sample_ids = df['SampleID'].unique()[:10]  # First 10 for analysis
    
    print(f"Sample parsing for first {min(len(sample_ids), 10)} IDs:")
    for sid in sample_ids:
        parsed = extract_group_animal(sid)
        tissue = extract_tissue(sid)
        
        if parsed:
            print(f"  '{sid}' → Group: {parsed.group}, Animal: {parsed.animal}, "
                  f"Well: {parsed.well}, Tissue: {tissue}, Time: {parsed.time}")
        else:
            print(f"  '{sid}' → ❌ FAILED TO PARSE")
    
    print()
    
    # Show group/animal distribution
    print("📊 GROUP & ANIMAL DISTRIBUTION")
    print("-" * 40)
    
    group_animal_counts = df.groupby(['Group', 'Animal']).size().reset_index(name='Count')
    print("Group-Animal combinations found:")
    for _, row in group_animal_counts.iterrows():
        print(f"  Group {row['Group']}, Animal {row['Animal']}: {row['Count']} samples")
    
    print()
    print(f"Unique groups: {sorted(df['Group'].unique())}")
    print(f"Unique animals: {sorted(df['Animal'].unique())}")
    print(f"Unique tissues: {sorted(df['Tissue'].unique())}")
    print()
    
    # Test replicate mapping
    print("🔢 REPLICATE MAPPING ANALYSIS")
    print("-" * 40)
    
    try:
        df_mapped, n_reps = map_replicates(df, auto_parse=True)
        print(f"✅ Replicate mapping successful")
        print(f"   Number of replicates detected: {n_reps}")
        print(f"   Rows after mapping: {len(df_mapped)}")
        
        if len(df_mapped) < len(df):
            print(f"   ⚠️  {len(df) - len(df_mapped)} rows were dropped during mapping")
        
        print()
        
        # Show replicate distribution
        rep_dist = df_mapped.groupby(['Group', 'Replicate']).size().reset_index(name='Count')
        print("Replicate distribution:")
        for _, row in rep_dist.iterrows():
            print(f"  Group {row['Group']}, Replicate {row['Replicate']}: {row['Count']} samples")
        
        # Show animal-to-replicate mapping
        print()
        print("Animal → Replicate mapping:")
        animal_rep_map = df_mapped[['Group', 'Animal', 'Replicate']].drop_duplicates().sort_values(['Group', 'Replicate'])
        for _, row in animal_rep_map.iterrows():
            print(f"  Group {row['Group']}: Animal {row['Animal']} → Replicate {row['Replicate']}")
            
    except Exception as e:
        print(f"❌ Replicate mapping failed: {e}")
        return
    
    print()
    
    # Check for potential issues
    print("⚠️  POTENTIAL ISSUES CHECK")
    print("-" * 40)
    
    issues_found = False
    
    # Check for missing animals in groups
    group_sizes = df.groupby('Group')['Animal'].nunique()
    if group_sizes.min() != group_sizes.max():
        print(f"❌ Unequal group sizes: {dict(group_sizes)}")
        print("   This may cause replicate mapping issues")
        issues_found = True
    
    # Check for duplicate group-animal combinations
    duplicates = df.groupby(['Group', 'Animal']).size()
    duplicates = duplicates[duplicates > 1]
    if not duplicates.empty:
        print(f"❌ Duplicate Group-Animal combinations found:")
        for (group, animal), count in duplicates.items():
            print(f"   Group {group}, Animal {animal}: {count} times")
        issues_found = True
    
    # Check for animals mapped to multiple replicates
    if 'Replicate' in df_mapped.columns:
        animal_rep_check = df_mapped.groupby(['Group', 'Animal'])['Replicate'].nunique()
        bad_animals = animal_rep_check[animal_rep_check > 1]
        if not bad_animals.empty:
            print(f"❌ Animals mapped to multiple replicates:")
            for (group, animal), rep_count in bad_animals.items():
                print(f"   Group {group}, Animal {animal}: {rep_count} different replicates")
            issues_found = True
    
    if not issues_found:
        print("✅ No obvious issues detected")
    
    print()
    print("🎯 RECOMMENDATIONS")
    print("-" * 40)
    
    if issues_found:
        print("To fix mapping issues:")
        print("1. Ensure each group has the same number of animals")
        print("2. Check for duplicate sample IDs or inconsistent naming")
        print("3. Verify your sample ID format matches expected patterns:")
        print("   - Standard: 'TISSUE_WELL_GROUP.ANIMAL' (e.g., 'SP_A1_1.1')")
        print("   - Simple: 'GROUP.ANIMAL' (e.g., '1.1')")
        print("   - With time: 'TIME_TISSUE_WELL_GROUP.ANIMAL' (e.g., '2h_SP_A1_1.1')")
    else:
        print("✅ Your sample mapping looks good!")
        print("If you're still seeing issues, the problem may be in:")
        print("1. Data visualization or Excel output formatting")
        print("2. Group labeling (check your group label settings)")
        print("3. Time course vs. standard analysis mode")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sample_mapping_diagnostic.py <path_to_csv>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        print(f"Error: File '{csv_path}' does not exist")
        sys.exit(1)
    
    analyze_sample_parsing(csv_path) 