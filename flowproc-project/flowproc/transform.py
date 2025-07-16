# flowproc/transform.py
import logging
import numpy as np
import pandas as pd
from typing import Optional, Callable
from .config import USER_GROUPS, USER_REPLICATES, AUTO_PARSE_GROUPS
from .parsing import extract_tissue, UNKNOWN_TISSUE

logger = logging.getLogger(__name__)

def reshape_pair(df: pd.DataFrame, sid_col: str, mcols: list, n: int, use_tissue: bool = False) -> tuple[list, list, list, list]:
    """Reshape the DataFrame for multiple measurement columns, with optional tissue extraction."""
    sub = df[[sid_col, 'Group', 'Replicate', 'Time'] + mcols].dropna(subset=mcols, how='all').copy()
    logger.debug(f"Processing columns {mcols}: {len(sub)} rows after dropping NaN")
    
    if use_tissue:
        sub['Tissue'] = sub[sid_col].apply(extract_tissue)
        sub['Tissue'] = sub['Tissue'].fillna(UNKNOWN_TISSUE)
    
    sub = sub.dropna(subset=['Group', 'Replicate'])
    logger.debug(f"After dropping rows with missing Group/Replicate{' or Tissue' if use_tissue else ''}: {len(sub)} rows")

    if sub.empty:
        logger.warning(f"No valid data for columns {mcols} after filtering")
        return [], [], [], []

    tissues = sorted(sub['Tissue'].unique()) if use_tissue else [UNKNOWN_TISSUE]
    groups = sorted(sub['Group'].unique())
    times = sorted(t for t in sub['Time'].unique() if pd.notna(t)) if 'Time' in sub.columns and sub['Time'].notna().any() else [None]
    logger.debug(f"Tissues found: {tissues}, Groups found: {groups}, Times found: {times}")

    val_blocks, id_blocks = [], []
    tissue_row_counts = []
    group_numbers = []

    for tissue in tissues:
        part = sub[sub['Tissue'] == tissue] if use_tissue else sub
        if part.empty:
            logger.debug(f"No data for tissue {tissue}")
            continue

        for group in groups:
            grp = part[part['Group'] == group]
            if grp.empty:
                logger.debug(f"No data for tissue {tissue}, group {group}")
                continue

            logger.debug(f"For tissue {tissue}, group {group}, grp length: {len(grp)}")

            row_vals = []
            row_ids = []
            for col in mcols:
                for rep in range(1, n + 1):
                    rep_row = grp[grp['Replicate'] == rep]
                    logger.debug(f"For col {col}, rep {rep}, rep_row length: {len(rep_row)}")
                    if not rep_row.empty:
                        value = rep_row[col].iloc[0]
                        row_vals.append(float(value) if isinstance(value, np.number) else value)
                        row_ids.append(rep_row[sid_col].iloc[0])
                    else:
                        row_vals.append(np.nan)
                        row_ids.append(np.nan)
            val_blocks.append(row_vals)
            id_blocks.append(row_ids)
            tissue_row_counts.append((tissue, 1))
            group_numbers.append(group)
            logger.debug(f"Appended row_vals for group {group}: length {len(row_vals)}")

    return val_blocks, id_blocks, tissue_row_counts, group_numbers

def map_replicates(df: pd.DataFrame) -> pd.DataFrame:
    """Map animals to replicates, auto or manual."""
    global USER_GROUPS, USER_REPLICATES
    logger.info(f"Parsing mode: {'Automatic' if AUTO_PARSE_GROUPS else 'Manual'}")
    if AUTO_PARSE_GROUPS:
        USER_GROUPS = sorted(df['Group'].unique())
        if df['Time'].notna().any():
            group_counts = df.groupby(['Time', 'Group'])['Animal'].nunique()
        else:
            group_counts = df.groupby('Group')['Animal'].nunique()
        if group_counts.empty:
            raise ValueError("No animals found to determine replicates.")
        n = group_counts.max()
        USER_REPLICATES = list(range(1, n + 1))
        logger.info(f"Automatically parsed groups: {USER_GROUPS}, max replicates per group: {n}")
    elif not USER_GROUPS or not USER_REPLICATES:
        logger.error("USER_GROUPS and USER_REPLICATES must be defined for manual parsing")
        raise ValueError("USER_GROUPS and USER_REPLICATES must be defined when manual parsing is enabled.")

    n = len(USER_REPLICATES)
    logger.info(f"Enforcing {len(USER_GROUPS)} groups and {n} replicates per group")

    animal_mapping = {}
    for time in df['Time'].unique():
        if pd.isna(time):
            time_df = df[df['Time'].isna()]
        else:
            time_df = df[df['Time'] == time]
        for group in USER_GROUPS:
            group_df = time_df[time_df['Group'] == group]
            unique_animals = sorted(group_df['Animal'].unique())
            logger.debug(f"Time {time}, Group {group} animals: {unique_animals}")
            num_found = len(unique_animals)
            if num_found < n:
                logger.warning(f"Group {group} at time {time} has fewer animals ({num_found}) than expected ({n}). Missing will be NaN.")
            if num_found > n:
                logger.warning(f"Group {group} at time {time} has more animals ({num_found}) than expected ({n}). Extra ignored.")
            for rep_idx, animal in enumerate(unique_animals[:n], 1):
                animal_mapping[(time, group, animal)] = rep_idx

    df['Replicate'] = df.apply(lambda row: animal_mapping.get((row['Time'], row['Group'], row['Animal']), None), axis=1)
    df = df.dropna(subset=['Replicate'])
    logger.debug(f"After mapping replicates: {len(df)} rows")
    return df