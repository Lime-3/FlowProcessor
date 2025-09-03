"""
Standard naming utilities for visualization outputs.
Generates concise, descriptive filenames following the format:
Plot_Tissue_Timepoints_Filename
"""

import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from ...core.constants import TISSUE_MAPPINGS


class NamingUtils:
    """Standard naming utilities for visualization outputs."""
    
    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 50) -> str:
        """Sanitize filename for filesystem compatibility."""
        filename = unicodedata.normalize('NFKD', filename)
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'[^\w\s\-_.]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('_.')
        
        if len(filename) > max_length:
            filename = filename[:max_length].rstrip('_.')
            
        return filename
    
    @staticmethod
    def extract_data_summary(data: pd.DataFrame) -> Dict[str, Any]:
        """Extract concise summary of data characteristics."""
        summary = {
            'tissue': '',
            'timepoints': '',
            'has_time_data': False,
            'has_tissue_data': False
        }
        
        # Extract tissue (most common)
        if 'Tissue' in data.columns:
            tissues = data['Tissue'].dropna().unique()
            valid_tissues = [str(t) for t in tissues if str(t) != 'UNK']
            if valid_tissues:
                tissue_counts = data['Tissue'].value_counts()
                most_common_tissue = tissue_counts.index[0]
                if most_common_tissue != 'UNK':
                    summary['tissue'] = most_common_tissue.upper()
                    summary['has_tissue_data'] = True
        
        # Extract timepoints (summarized)
        if 'Time' in data.columns:
            times = data['Time'].dropna().unique()
            if len(times) > 0:
                summary['has_time_data'] = True
                if len(times) == 1:
                    summary['timepoints'] = f"T{times[0]:.0f}h"
                else:
                    min_time, max_time = min(times), max(times)
                    if min_time == max_time:
                        summary['timepoints'] = f"T{min_time:.0f}h"
                    else:
                        summary['timepoints'] = f"T{min_time:.0f}-{max_time:.0f}h"
        
        return summary
    
    @staticmethod
    def get_plot_type_name(plot_type: str) -> str:
        """Get plot type name for filename."""
        plot_names = {
            'scatter': 'Scatter',
            'bar': 'Bar',
            'line': 'Line',
            'box': 'Box',
            'violin': 'Violin',
            'histogram': 'Hist',
            'area': 'Area'
        }
        return plot_names.get(plot_type.lower(), plot_type.title())
    
    @staticmethod
    def get_tissue_abbreviation(tissue: str) -> str:
        """Get abbreviated tissue name."""
        tissue_upper = tissue.upper()
        if tissue_upper in TISSUE_MAPPINGS:
            tissue_name = TISSUE_MAPPINGS[tissue_upper]
        else:
            tissue_name = tissue
        
        # Shorten tissue names
        tissue_short = {
            'Spleen': 'Spleen',
            'Bone Marrow': 'BM',
            'Lymph Node': 'LN',
            'Peripheral Blood': 'PB',
            'Thymus': 'Thymus',
            'Liver': 'Liver',
            'Kidney': 'Kidney',
            'Lung': 'Lung',
            'Brain': 'Brain',
            'Heart': 'Heart',
            'Stomach': 'Stomach',
            'Intestine': 'Intestine',
            'Skin': 'Skin',
            'Muscle': 'Muscle',
            'Fat': 'Fat'
        }
        return tissue_short.get(tissue_name, tissue_name)
    
    @staticmethod
    def summarize_filename(source_file: Optional[Path]) -> str:
        """Create concise summary of source filename."""
        if not source_file:
            return "Data"
        
        stem = source_file.stem
        
        # Remove common prefixes/suffixes
        stem = re.sub(r'^(processed_|raw_|data_|study_)', '', stem, flags=re.IGNORECASE)
        stem = re.sub(r'(_processed|_data|_study|_results)$', '', stem, flags=re.IGNORECASE)
        
        # Take meaningful parts
        parts = stem.split('_')
        if len(parts) > 3:
            meaningful_parts = []
            for part in parts[:3]:
                if len(part) > 2 and not part.isdigit():
                    meaningful_parts.append(part)
            
            if meaningful_parts:
                stem = '_'.join(meaningful_parts)
            else:
                stem = parts[0]
        
        stem = NamingUtils.sanitize_filename(stem, 20)
        return stem if stem else "Data"
    
    @staticmethod
    def generate_plot_filename(
        plot_config: Dict[str, Any],
        data: pd.DataFrame,
        source_file: Optional[Path] = None,
        plot_index: int = 1
    ) -> str:
        """
        Generate standard plot filename: Plot_Tissue_Timepoints_Filename
        
        Args:
            plot_config: Plot configuration
            data: Data being plotted
            source_file: Source file path
            plot_index: Plot index for multiple plots
            
        Returns:
            Standard filename
        """
        # Extract plot information
        plot_type = plot_config.get('type', 'scatter')
        plot_name = NamingUtils.get_plot_type_name(plot_type)
        
        # Extract data summary
        summary = NamingUtils.extract_data_summary(data)
        
        # Build components
        components = []
        
        # 1. Plot type
        components.append(plot_name)
        
        # 2. Tissue (if available)
        if summary['tissue']:
            tissue_abbr = NamingUtils.get_tissue_abbreviation(summary['tissue'])
            components.append(tissue_abbr)
        
        # 3. Timepoints (if available)
        if summary['timepoints']:
            components.append(summary['timepoints'])
        
        # 4. Source filename
        filename_summary = NamingUtils.summarize_filename(source_file)
        components.append(filename_summary)
        
        # 5. Plot index (only if multiple plots)
        if plot_index > 1:
            components.append(f"P{plot_index}")
        
        # Join and sanitize
        filename = "_".join(components)
        filename = NamingUtils.sanitize_filename(filename)
        
        # Add extension
        file_format = plot_config.get('format', 'html')
        filename = f"{filename}.{file_format}"
        
        return filename
    
    @staticmethod
    def generate_comparison_filename(
        comparison_config: Dict[str, Any],
        data_dict: Dict[str, pd.DataFrame],
        source_files: Optional[list[Path]] = None,
        comparison_index: int = 1
    ) -> str:
        """
        Generate standard comparison filename.
        
        Args:
            comparison_config: Comparison configuration
            data_dict: Datasets being compared
            source_files: Source file paths
            comparison_index: Comparison index for multiple comparisons
            
        Returns:
            Standard comparison filename
        """
        components = []
        
        # 1. Comparison type
        comparison_type = comparison_config.get('type', 'Comparison')
        components.append(comparison_type.title())
        
        # 2. Dataset summary
        dataset_names = list(data_dict.keys())
        if len(dataset_names) <= 2:
            for name in dataset_names:
                name_clean = NamingUtils.sanitize_filename(name, 15)
                components.append(name_clean)
        else:
            components.append(f"{len(dataset_names)}Sets")
        
        # 3. Source files summary
        if source_files:
            if len(source_files) == 1:
                filename_summary = NamingUtils.summarize_filename(source_files[0])
                components.append(filename_summary)
            else:
                components.append(f"{len(source_files)}Files")
        
        # 4. Comparison index (only if multiple comparisons)
        if comparison_index > 1:
            components.append(f"C{comparison_index}")
        
        # Join and sanitize
        filename = "_".join(components)
        filename = NamingUtils.sanitize_filename(filename)
        
        # Add extension
        file_format = comparison_config.get('format', 'html')
        filename = f"{filename}.{file_format}"
        
        return filename
