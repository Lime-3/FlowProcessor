"""
Centralized Plot Factory for Plotly Express constructors.

This module removes duplicated plot-type switching scattered across the
visualization code by providing a single registry/dispatcher for creating
Plotly Express figures in a consistent, modernized way.
"""

from __future__ import annotations

from typing import Callable, Optional, Dict, Any

import plotly.express as px


# Type alias for the Plotly Express constructor signature we use
_PxConstructor = Callable[..., Any]


def resolve_px_constructor(plot_type: str) -> _PxConstructor:
    """
    Resolve a plot type string to the corresponding Plotly Express constructor.

    Supported plot types: 'scatter', 'bar', 'box', 'line', 'histogram', 'area'.
    """
    normalized = (plot_type or "").strip().lower()
    registry: Dict[str, _PxConstructor] = {
        "scatter": px.scatter,
        "bar": px.bar,
        "box": px.box,
        "line": px.line,
        "histogram": px.histogram,
        "area": px.area,
    }
    if normalized not in registry:
        raise ValueError(f"Unsupported plot type: {plot_type}")
    return registry[normalized]


def build_plot_from_df(
    plot_type: str,
    df,
    *,
    x: Optional[str] = None,
    y: Optional[str] = None,
    color: Optional[str] = None,
    error_y: Optional[str] = None,
    orientation: Optional[str] = None,
    **kwargs: Any,
):
    """
    Create a Plotly Express figure using a centralized constructor resolution.

    - For 'histogram', only x is used (y is ignored by px.histogram).
    - For other plot types, x and y are passed through when provided.
    - color and error_y are passed through when provided.
    """
    constructor = resolve_px_constructor(plot_type)

    call_kwargs: Dict[str, Any] = dict(kwargs)
    if color is not None:
        call_kwargs["color"] = color
    # Handle orientation-aware error bars for horizontal bar charts
    if orientation == 'h' and error_y is not None and plot_type.lower() == 'bar':
        call_kwargs["error_x"] = error_y
    elif error_y is not None:
        call_kwargs["error_y"] = error_y
    if orientation is not None:
        call_kwargs["orientation"] = orientation

    if plot_type.lower() == "histogram":
        # Histogram ignores y and only needs x
        if x is None:
            raise ValueError("Histogram requires an 'x' column")
        fig = constructor(df, x=x, **call_kwargs)
        return fig

    # Other plot types
    if x is None or y is None:
        raise ValueError(f"Plot type '{plot_type}' requires both 'x' and 'y' columns")
    fig = constructor(df, x=x, y=y, **call_kwargs)

    # Centralize bar defaults: group bars when a color grouping is present
    if plot_type.lower() == 'bar' and color is not None and 'barmode' not in kwargs:
        try:
            fig.update_layout(barmode='group')
        except Exception:
            pass

    return fig


__all__ = [
    "resolve_px_constructor",
    "build_plot_from_df",
]


