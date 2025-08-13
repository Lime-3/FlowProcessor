"""
Backward-compat shim for legacy tests expecting VisualizationOptions in
visualization_options_dialog.
"""

from .visualization_options import VisualizationOptions  # re-export

__all__ = ["VisualizationOptions"]


