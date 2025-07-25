"""Map samples to replicates for Excel output."""
from typing import Dict, List, Tuple, Optional, Set
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ReplicateMapper:
    """Maps samples to replicate numbers."""
    
    def __init__(self, auto_map: bool = True):
        """
        Initialize replicate mapper.
        
        Args:
            auto_map: Whether to automatically map replicates
        """
        self.auto_map = auto_map
        self._mapping_cache: Dict[str, Dict[int, int]] = {}
        
    def map_replicates(self, df: pd.DataFrame,
                      groups: Optional[List[int]] = None,
                      replicates: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Map animals to replicate numbers.
        
        Args:
            df: DataFrame with Group and Animal columns
            groups: List of groups to include
            replicates: List of replicate numbers to use
            
        Returns:
            DataFrame with Replicate column added
        """
        if 'Group' not in df.columns or 'Animal' not in df.columns:
            raise ValueError("DataFrame must have Group and Animal columns")
            
        # Get unique groups if not specified
        if groups is None:
            groups = sorted(df['Group'].dropna().unique())
            
        # Determine replicate numbers
        if self.auto_map:
            # Auto-detect number of replicates
            max_animals = df.groupby('Group')['Animal'].nunique().max()
            replicates = list(range(1, max_animals + 1))
            logger.info(f"Auto-detected {max_animals} replicates")
        elif replicates is None:
            raise ValueError("Replicates must be specified in manual mode")
            
        # Create mapping
        mapping = self._create_mapping(df, groups, replicates)
        
        # Apply mapping
        df['Replicate'] = df.apply(
            lambda row: mapping.get((row['Group'], row['Animal'])),
            axis=1
        )
        
        # Log mapping results
        mapped_count = df['Replicate'].notna().sum()
        total_count = len(df)
        logger.info(f"Mapped {mapped_count}/{total_count} samples to replicates")
        
        if mapped_count < total_count:
            unmapped = df[df['Replicate'].isna()]
            logger.warning(
                f"{total_count - mapped_count} samples not mapped. "
                f"Groups: {unmapped['Group'].unique()[:5]}"
            )
            
        return df
        
    def _create_mapping(self, df: pd.DataFrame,
                       groups: List[int],
                       replicates: List[int]) -> Dict[Tuple[int, int], int]:
        """Create group/animal to replicate mapping."""
        mapping = {}
        
        # Check for tissue-specific mapping
        has_tissues = 'Tissue' in df.columns and df['Tissue'].nunique() > 1
        
        # Create cache key
        cache_key = f"{tuple(groups)}_{tuple(replicates)}_{has_tissues}"
        
        if cache_key in self._mapping_cache:
            return self._mapping_cache[cache_key]
            
        if has_tissues:
            # Map within each tissue
            tissues = df['Tissue'].unique()
            
            for tissue in tissues:
                tissue_df = df[df['Tissue'] == tissue]
                
                for group in groups:
                    group_df = tissue_df[tissue_df['Group'] == group]
                    animals = sorted(group_df['Animal'].dropna().unique())
                    
                    # Map animals to replicates
                    for i, animal in enumerate(animals[:len(replicates)]):
                        mapping[(group, animal)] = replicates[i]
        else:
            # Map globally
            for group in groups:
                group_df = df[df['Group'] == group]
                animals = sorted(group_df['Animal'].dropna().unique())
                
                # Map animals to replicates
                for i, animal in enumerate(animals[:len(replicates)]):
                    mapping[(group, animal)] = replicates[i]
                    
        # Cache the mapping
        self._mapping_cache[cache_key] = mapping
        
        # Log mapping details
        logger.debug(f"Created mapping for {len(mapping)} group/animal combinations")
        
        return mapping
        
    def validate_mapping(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate replicate mapping.
        
        Args:
            df: DataFrame with Replicate column
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if 'Replicate' not in df.columns:
            errors.append("No Replicate column found")
            return False, errors
            
        # Check for unmapped samples
        unmapped = df['Replicate'].isna().sum()
        if unmapped > 0:
            errors.append(f"{unmapped} samples have no replicate assignment")
            
        # Check for duplicate assignments
        duplicates = df.groupby(['Group', 'Replicate']).size()
        duplicates = duplicates[duplicates > 1]
        
        if not duplicates.empty:
            for (group, rep), count in duplicates.items():
                errors.append(
                    f"Group {group}, Replicate {rep}: {count} samples "
                    "(should be 1)"
                )
                
        # Check for missing replicates
        for group in df['Group'].unique():
            group_df = df[df['Group'] == group]
            expected_reps = sorted(group_df['Replicate'].dropna().unique())
            
            if expected_reps:
                max_rep = int(max(expected_reps))
                missing = [r for r in range(1, max_rep + 1) 
                          if r not in expected_reps]
                
                if missing:
                    errors.append(
                        f"Group {group} missing replicates: {missing}"
                    )
                    
        return len(errors) == 0, errors
        
    def get_replicate_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get summary of replicate assignments.
        
        Args:
            df: DataFrame with replicate mapping
            
        Returns:
            Summary DataFrame
        """
        if 'Replicate' not in df.columns:
            raise ValueError("DataFrame must have Replicate column")
            
        # Group by relevant columns
        group_cols = ['Group']
        if 'Tissue' in df.columns:
            group_cols.append('Tissue')
            
        # Create summary
        summary = df.groupby(group_cols + ['Replicate'])['Animal'].agg([
            ('Animal', 'first'),
            ('Sample_Count', 'count')
        ]).reset_index()
        
        # Add validation status
        summary['Valid'] = summary['Sample_Count'] == 1
        
        return summary