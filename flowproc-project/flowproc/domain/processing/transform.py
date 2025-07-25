import logging
import pandas as pd
from typing import List, Tuple, Optional, Dict, Union
import numpy as np

from flowproc.domain.parsing import extract_tissue, Constants

logger = logging.getLogger(__name__)

def map_replicates(
    df: pd.DataFrame,
    auto_parse: bool = True,
    user_replicates: Optional[List[int]] = None,
    user_groups: Optional[List[int]] = None,
) -> Tuple[pd.DataFrame, int]:
    """Map animals to replicates, auto or manual."""
    logger.info(f"Mapping replicates: auto_parse={auto_parse}, groups={user_groups}, replicates={user_replicates}")
    
    if df.empty:
        logger.warning("Empty DataFrame provided for replicate mapping")
        return df, 0

    # Check if we have multiple tissues
    tissues_detected = df['Tissue'].nunique() > 1 if 'Tissue' in df.columns else False
    logger.info(f"Multiple tissues detected: {tissues_detected}")

    if auto_parse:
        # Get unique groups, converting numpy types to Python ints
        groups = sorted([int(g) for g in df['Group'].dropna().unique()]) if user_groups is None else user_groups
        if not groups:
            raise ValueError("No groups found")
        
        if 'Animal' not in df.columns:
            logger.warning("Animal column missing, using Group as fallback")
            df['Animal'] = df['Group'].astype(int)
        
        # Get unique animals, converting to Python ints
        unique_animals = sorted([int(a) for a in df['Animal'].dropna().unique()])
        if not unique_animals:
            raise ValueError("No animals found")
        
        # Calculate replicate count based on whether we have tissues
        has_time = 'Time' in df.columns and df['Time'].notna().any()
        
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
        
        n = int(group_counts.max()) if not group_counts.empty else len(unique_animals)
        
        if n == 0:
            raise ValueError("No unique animals")
        
        if group_counts.min() != group_counts.max():
            logger.warning(f"Inconsistent counts: min={group_counts.min()}, max={n}")
        
        replicates = list(range(1, n + 1)) if user_replicates is None else user_replicates
    else:
        if not user_groups or not user_replicates:
            raise ValueError("Groups and replicates required")
        groups = user_groups
        replicates = user_replicates
        n = len(replicates)

    # Create mapping for animals to replicates (tissue-aware)
    animal_mapping: Dict[Tuple[Optional[float], int, int, str], int] = {}
    
    # Get time points - handle missing Time column
    if 'Time' in df.columns:
        time_points = df['Time'].unique()
        # Convert NaN to None for consistent comparison
        time_points = [None if pd.isna(t) else t for t in time_points]
    else:
        time_points = [None]  # Single time point when no Time column
    
    for time in time_points:
        if 'Time' in df.columns:
            time_df = df[df['Time'].isna()] if pd.isna(time) else df[df['Time'] == time]
        else:
            time_df = df  # Use all data when no Time column
        
        for group in groups:
            group_df = time_df[time_df['Group'] == group]
            
            if tissues_detected:
                # Handle each tissue separately
                if group_df.empty:
                    continue  # Skip empty groups
                for tissue in group_df['Tissue'].unique():
                    tissue_df = group_df[group_df['Tissue'] == tissue]
                    unique_animals = sorted([int(a) for a in tissue_df['Animal'].dropna().unique()])
                    
                    for rep_idx, animal in enumerate(unique_animals[:n], 1):
                        animal_mapping[(time, group, animal, tissue)] = rep_idx
            else:
                # Single tissue handling (original logic)
                if group_df.empty:
                    continue  # Skip empty groups
                unique_animals = sorted([int(a) for a in group_df['Animal'].dropna().unique()])
                tissue = group_df['Tissue'].iloc[0] if 'Tissue' in group_df.columns and not group_df.empty else Constants.UNKNOWN_TISSUE.value
                
                for rep_idx, animal in enumerate(unique_animals[:n], 1):
                    animal_mapping[(time, group, animal, tissue)] = rep_idx
    
    # Apply mapping (tissue-aware)
    def get_replicate(row):
        time_val = row['Time'] if 'Time' in row else None
        # Convert NaN to None for consistent comparison
        if pd.isna(time_val):
            time_val = None
        group_val = int(row['Group'])
        animal_val = int(row['Animal'])
        tissue_val = row['Tissue'] if 'Tissue' in row else Constants.UNKNOWN_TISSUE.value
        
        key = (time_val, group_val, animal_val, tissue_val)
        return animal_mapping.get(key, None)
    
    df['Replicate'] = df.apply(get_replicate, axis=1)
    
    # Remove rows without replicate assignment
    df = df.dropna(subset=['Replicate'])
    
    logger.debug(f"Replicates mapped, rows: {len(df)}")
    return df, n

def reshape_pair(
    df: pd.DataFrame,
    sid_col: str,
    mcols: List[str],
    n: int,
    use_tissue: bool = False,
    include_time: bool = False,
) -> Tuple[List[List[float]], List[List[str]], List[Union[Tuple[str, int], str]], List[int], List[Optional[float]]]:
    """Reshape data into paired value/ID blocks for Excel output."""
    logger.debug(f"Reshaping data for columns: {mcols}, replicates: {n}, use_tissue: {use_tissue}, include_time: {include_time}")
    
    # Create subset with required columns
    required_cols = [sid_col, 'Group', 'Replicate'] + mcols
    if 'Time' in df.columns:
        required_cols.append('Time')
    sub = df[required_cols].dropna(subset=mcols, how='all').copy()
    
    if use_tissue:
        sub['Tissue'] = sub[sid_col].apply(extract_tissue)
    
    # Ensure Group and Replicate are present
    sub = sub.dropna(subset=['Group', 'Replicate'])
    
    if sub.empty:
        logger.warning(f"No valid data for {mcols}")
        return [], [], [], [], []

    # Get unique values, converting numpy types
    tissues = sorted(sub['Tissue'].unique()) if use_tissue else [Constants.UNKNOWN_TISSUE.value]
    groups = sorted([int(g) for g in sub['Group'].unique()])
    times = sorted([t for t in sub['Time'].unique() if pd.notna(t)]) if 'Time' in sub.columns else [None]
    
    logger.debug(f"Tissues: {tissues}, Groups: {groups}, Times: {times}")

    val_blocks: List[List[float]] = []
    id_blocks: List[List[str]] = []
    tissue_row_counts: List[Union[Tuple[str, int], str]] = []
    group_numbers: List[int] = []
    time_values: List[Optional[float]] = []

    # If including time, we need to iterate through times as well
    if include_time and times and times != [None]:
        for tissue in tissues:
            tissue_part = sub[sub['Tissue'] == tissue] if use_tissue else sub
            if tissue_part.empty:
                continue
            
            for time in times:
                time_part = tissue_part[tissue_part['Time'] == time] if pd.notna(time) else tissue_part[tissue_part['Time'].isna()]
                if time_part.empty:
                    continue
                    
                for group in groups:
                    grp = time_part[time_part['Group'] == group]
                    if grp.empty:
                        continue
                    
                    for col in mcols:
                        row_vals = []
                        row_ids = []
                        
                        for rep in range(1, n + 1):
                            rep_row = grp[grp['Replicate'] == rep]
                            
                            if not rep_row.empty and col in rep_row.columns:
                                value = rep_row[col].iloc[0]
                                row_vals.append(float(value) if pd.notnull(value) else np.nan)
                                row_ids.append(str(rep_row[sid_col].iloc[0]))
                            else:
                                row_vals.append(np.nan)
                                row_ids.append("")
                        
                        # Only add blocks with at least one non-NaN value
                        if any(not pd.isna(v) for v in row_vals):
                            val_blocks.append(row_vals)
                            id_blocks.append(row_ids)
                            tissue_row_counts.append((tissue, 1) if use_tissue else tissue)
                            group_numbers.append(group)
                            time_values.append(time)
    else:
        # Original logic without time grouping
        for tissue in tissues:
            part = sub[sub['Tissue'] == tissue] if use_tissue else sub
            if part.empty:
                continue
            
            for group in groups:
                grp = part[part['Group'] == group]
                if grp.empty:
                    continue
                
                for col in mcols:
                    row_vals = []
                    row_ids = []
                    
                    for rep in range(1, n + 1):
                        rep_row = grp[grp['Replicate'] == rep]
                        
                        if not rep_row.empty and col in rep_row.columns:
                            value = rep_row[col].iloc[0]
                            row_vals.append(float(value) if pd.notnull(value) else np.nan)
                            row_ids.append(str(rep_row[sid_col].iloc[0]))
                        else:
                            row_vals.append(np.nan)
                            row_ids.append("")
                    
                    # Only add blocks with at least one non-NaN value
                    if any(not pd.isna(v) for v in row_vals):
                        val_blocks.append(row_vals)
                        id_blocks.append(row_ids)
                        tissue_row_counts.append((tissue, 1) if use_tissue else tissue)
                        group_numbers.append(group)
                        time_values.append(None)
    
    logger.debug(f"Generated {len(val_blocks)} blocks for {mcols}")
    return val_blocks, id_blocks, tissue_row_counts, group_numbers, time_values