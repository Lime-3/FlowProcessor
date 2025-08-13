"""
Compatibility shim for Visualization dialog expected by tests.

Exposes `VisualizationDisplayDialog` as an alias of the newer
`VisualizationDialog` so legacy imports continue to work.
"""

from .visualization_dialog import VisualizationDialog


class VisualizationDisplayDialog(VisualizationDialog):
    pass


