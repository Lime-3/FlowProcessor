"""Visualization theme registry and helpers.

Provides a small set of named themes used by tests.
"""

from __future__ import annotations

from typing import Dict, List

import plotly.io as pio
import plotly.graph_objects as go


class VisualizationThemes:
    """Expose a curated set of themes and apply them to figures."""

    _TEMPLATE_MAP: Dict[str, str] = {
        "default": "plotly",
        "scientific": "plotly_white",
        "dark": "plotly_dark",
        "minimal": "simple_white",
        "colorful": "seaborn",
        "publication": "ggplot2",
    }

    def get_available_themes(self) -> List[str]:
        return list(self._TEMPLATE_MAP.keys())

    def apply_theme(self, fig: go.Figure, theme: str) -> go.Figure:
        if theme not in self._TEMPLATE_MAP:
            raise ValueError(f"Unknown theme: {theme}")
        template_name = self._TEMPLATE_MAP[theme]
        # Ensure template exists; fall back to 'plotly' if missing
        if template_name not in pio.templates:
            template_name = "plotly"
        fig.update_layout(template=pio.templates[template_name])
        return fig


