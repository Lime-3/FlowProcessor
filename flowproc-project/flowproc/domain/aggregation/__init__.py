"""Centralized data aggregation utilities.

Provides a single source of truth for common aggregation patterns
used across visualization and export layers.
"""

from .core import (
    group_stats,
    group_stats_multi,
    timecourse_group_stats,
    timecourse_group_stats_multi,
    generic_aggregate,
)

__all__ = [
    "group_stats",
    "group_stats_multi",
    "timecourse_group_stats",
    "timecourse_group_stats_multi",
    "generic_aggregate",
]


