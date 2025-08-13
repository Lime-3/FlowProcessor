"""Core aggregation helpers (single source of truth).

All public helpers return tidy DataFrames and follow consistent naming:
- mean, std, count, sem
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd


DataFrame = pd.DataFrame


def _compute_sem(std: pd.Series, count: pd.Series) -> pd.Series:
    return np.where((count > 1) & std.notna(), std / np.sqrt(count), 0.0)


def group_stats(
    df: DataFrame,
    value_col: str,
    group_cols: Union[str, Sequence[str]] = "Group",
) -> DataFrame:
    """Aggregate one value column by group(s) with mean/std/count/sem.

    Returns columns: group_cols..., "mean", "std", "count", "sem".
    """
    if isinstance(group_cols, str):
        group_cols = [group_cols]

    result = df.groupby(list(group_cols))[value_col].agg(["mean", "std", "count"]).reset_index()
    result["mean"] = result["mean"].fillna(0.0)
    result["sem"] = _compute_sem(result["std"], result["count"])  # type: ignore[index]
    return result


def group_stats_multi(
    df: DataFrame,
    value_cols: Sequence[str],
    group_cols: Union[str, Sequence[str]] = "Group",
    long_name: str = "Variable",
    value_name: str = "Value",
) -> DataFrame:
    """Aggregate multiple value columns by group(s) and return long-form.

    Output columns: group_cols..., long_name, "mean", "std", "count", "sem".
    """
    melted = df.melt(
        id_vars=list(group_cols) if isinstance(group_cols, (list, tuple)) else [group_cols],
        value_vars=list(value_cols),
        var_name=long_name,
        value_name=value_name,
    )
    melted = melted.dropna(subset=[value_name])
    agg_cols: List[str]
    if isinstance(group_cols, (list, tuple)):
        agg_cols = list(group_cols) + [long_name]
    else:
        agg_cols = [group_cols, long_name]

    result = (
        melted.groupby(agg_cols)[value_name]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    result["mean"] = result["mean"].fillna(0.0)
    result["sem"] = _compute_sem(result["std"], result["count"])  # type: ignore[index]
    return result


def timecourse_group_stats(
    df: DataFrame,
    value_col: str,
    time_col: str,
    group_col: Optional[str] = None,
) -> DataFrame:
    """Aggregate a single column over time and optional group.

    If group_col is provided, groups by [group_col, time_col], otherwise [time_col].
    """
    by: List[str] = [time_col]
    if group_col:
        by = [group_col, time_col]
    result = df.groupby(by)[value_col].agg(["mean", "std", "count"]).reset_index()
    result["sem"] = _compute_sem(result["std"], result["count"])  # type: ignore[index]
    return result


def timecourse_group_stats_multi(
    df: DataFrame,
    value_cols: Sequence[str],
    time_col: str,
    group_col: Optional[str] = None,
    long_name: str = "value_col",
) -> DataFrame:
    """Aggregate multiple columns over time and optional group in long form.

    Returns columns: (optional group_col), time_col, long_name, mean, std, count, sem.
    """
    frames: List[DataFrame] = []
    for col in value_cols:
        agg = timecourse_group_stats(df, col, time_col=time_col, group_col=group_col)
        agg[long_name] = col
        frames.append(agg)
    if not frames:
        return pd.DataFrame(columns=[
            *( [group_col] if group_col else [] ),
            time_col,
            long_name,
            "mean","std","count","sem",
        ])
    return pd.concat(frames, ignore_index=True)


def generic_aggregate(
    df: DataFrame,
    value_cols: Sequence[str],
    group_cols: Union[str, Sequence[str]],
    agg_methods: Optional[Dict[str, Union[str, callable]]] = None,
) -> DataFrame:
    """Generic aggregation helper used by export layer.

    agg_methods maps each value_col to an aggregation method name or callable.
    Adds an "N" column with group size.
    """
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    if not value_cols:
        return pd.DataFrame()

    if agg_methods is None:
        agg_methods = {col: "mean" for col in value_cols}

    # Convert method names to callables where possible
    dispatch = {
        "mean": np.mean,
        "median": np.median,
        "std": np.std,
        "sem": lambda x: np.std(x) / np.sqrt(len(x)) if len(x) > 0 else np.nan,
        "cv": lambda x: (np.std(x) / np.mean(x) * 100) if np.mean(x) != 0 else np.nan,
        "min": np.min,
        "max": np.max,
        "count": len,
    }

    agg_funcs: Dict[str, Union[str, callable]] = {}
    for col, method in agg_methods.items():
        if isinstance(method, str) and method in dispatch:
            agg_funcs[col] = dispatch[method]
        else:
            agg_funcs[col] = method

    clean = df.dropna(subset=value_cols, how="all")
    if clean.empty:
        return pd.DataFrame()

    out = clean.groupby(list(group_cols)).agg(agg_funcs).reset_index()
    counts = clean.groupby(list(group_cols)).size().reset_index(name="N")
    out = out.merge(counts, on=list(group_cols))
    return out


