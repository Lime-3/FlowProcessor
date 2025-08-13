"""
Backward-compat shim for legacy tests expecting VisualizationDisplayDialog.

Maps to the modern VisualizationDialog while providing legacy attribute and
method aliases used by tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .visualization_dialog import VisualizationDialog


class VisualizationDisplayDialog(VisualizationDialog):
    """
    Compatibility wrapper over VisualizationDialog.

    - Exposes legacy attribute name 'plot_by_times_checkbox' -> 'time_course_checkbox'
    - Exposes legacy method '_get_current_options' -> 'get_current_options'
    """

    # Legacy alias for tests
    @property
    def plot_by_times_checkbox(self):  # type: ignore[override]
        return getattr(self, 'time_course_checkbox', None)

    # Legacy alias for tests
    def _get_current_options(self):
        return self.get_current_options()


