from typing import Optional, Tuple, List, Dict, Any

import pandas as pd


def extract_population_name(column_name: str, metric: Optional[str] = None) -> str:
    """Extract a population name from a column.

    - Uses common separators and path tokens to isolate the population label
    - If a metric is provided, also trims a trailing metric suffix (case-insensitive)
    """
    # Prefer the last path segment when present (e.g., "Live/CD4+/GFP+ -> GFP+")
    if '/' in column_name:
        path_parts = column_name.split('/')
        if path_parts:
            column_name = path_parts[-1].strip()

    # Handle common separators between population and metric text
    separators = [' | ', ' |', '| ', ' - ', ' -', '- ']
    for separator in separators:
        if separator in column_name:
            parts = column_name.split(separator)
            if len(parts) >= 2:
                population_part = parts[0].strip()
                if population_part:
                    column_name = population_part
                    break

    # If a metric is given and appears at the end, trim it
    if metric:
        metric_lower = metric.lower()
        if column_name.lower().endswith(metric_lower):
            trimmed = column_name[: -len(metric)].strip()
            if trimmed:
                column_name = trimmed

    return column_name


def detect_population_options(df: pd.DataFrame, metric: Optional[str]) -> Tuple[List[str], Dict[str, str]]:
    """Detect available population shortnames and mapping from the data.

    Returns a sorted list of shortnames and a mapping shortname -> full column name.
    """
    from flowproc.core.constants import is_pure_metric_column
    from flowproc.domain.visualization.column_utils import (
        get_matching_columns_for_metric,
        detect_flow_columns,
        create_population_shortname,
    )

    available_populations: List[str] = []
    population_mapping: Dict[str, str] = {}

    if metric:
        matching_cols = get_matching_columns_for_metric(df, metric)
        for col in matching_cols:
            if not is_pure_metric_column(col, metric):
                population_name = extract_population_name(col, metric)
                if population_name and population_name not in available_populations:
                    shortname = create_population_shortname(col)
                    population_mapping[shortname] = col
                    available_populations.append(shortname)

    if not available_populations:
        flow_cols = detect_flow_columns(df)
        if flow_cols['frequencies']:
            for col in flow_cols['frequencies']:
                population_name = extract_population_name(col, None)
                if population_name and population_name not in available_populations:
                    shortname = create_population_shortname(col)
                    population_mapping[shortname] = col
                    available_populations.append(shortname)

    available_populations.sort()
    return available_populations, population_mapping


def build_tissue_entries(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], bool]:
    """Build display entries for tissues and whether real tissue data exists."""
    entries: List[Dict[str, Any]] = []
    has_real_tissue_data = False

    if 'Tissue' in df.columns:
        unique_tissues = df['Tissue'].dropna().unique()
        real_tissues = [t for t in unique_tissues if t != 'UNK']
        has_real_tissue_data = len(real_tissues) > 0

        if len(unique_tissues) > 0:
            from flowproc.domain.parsing.tissue_parser import TissueParser
            tissue_parser = TissueParser()

            for tissue_code in sorted(unique_tissues):
                tissue_count = len(df[df['Tissue'] == tissue_code])
                if tissue_code == 'UNK':
                    display_text = f"UNK (Unknown) [{tissue_count} samples]"
                else:
                    full_name = tissue_parser.get_full_name(tissue_code)
                    display_text = f"{tissue_code} ({full_name}) [{tissue_count} samples]"
                entries.append({
                    'display': display_text,
                    'value': tissue_code,
                    'checked': True,
                })

    return entries, has_real_tissue_data


def build_time_entries(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], bool]:
    """Build display entries for time filter and whether time data exists."""
    entries: List[Dict[str, Any]] = []
    has_time_data = False

    if 'Time' in df.columns:
        unique_times = df['Time'].dropna().unique()
        if len(unique_times) > 0:
            has_time_data = True
            from flowproc.domain.parsing.time_service import TimeService
            time_service = TimeService()

            for time_hours in sorted(unique_times):
                if pd.notna(time_hours):
                    time_count = len(df[df['Time'] == time_hours])
                    formatted_time = time_service.format(time_hours, format_style='auto')
                    display_text = f"{formatted_time} ({time_hours}h) [{time_count} samples]"
                    entries.append({
                        'display': display_text,
                        'value': time_hours,
                        'checked': True,
                    })

    return entries, has_time_data


def detect_time_column(df: pd.DataFrame) -> str:
    """Detect a suitable time column name in the dataframe."""
    if 'Time' in df.columns:
        return 'Time'
    if 'time' in df.columns:
        return 'time'

    time_candidates = [
        col for col in df.columns
        if any(keyword in col.lower() for keyword in ['time', 'day', 'hour', 'week', 'minute'])
    ]
    if time_candidates:
        return time_candidates[0]

    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 1:
        return numeric_cols[0]

    return 'Time'


