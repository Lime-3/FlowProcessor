"""
Thin visualization facade retained for test stubs.

Modern code should use functions in `flowproc.domain.visualization.flow_cytometry_visualizer`
directly. This module exists to provide a stable import target for tests
that patch `flowproc.domain.visualization.facade.visualize_data`.
"""

from __future__ import annotations

from typing import Any, Optional


def visualize_data(*args: Any, **kwargs: Any) -> Optional[Any]:
    """No-op visualization entry point used by tests when patched.

    Returns None by default. Real visualization should use
    `flowproc.domain.visualization.flow_cytometry_visualizer.plot` or the
    timecourse helpers in `time_plots`.
    """
    return None


__all__ = ["visualize_data"]


