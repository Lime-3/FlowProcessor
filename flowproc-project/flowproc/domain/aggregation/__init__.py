"""
Aggregation domain module for flow cytometry data processing.

This module provides:
- Core statistical functions (simple, focused)
- Unified aggregation service (complex, feature-rich)
- Consistent interfaces for different aggregation needs
"""

# Core statistical functions (simple, focused)
from .core import (
    group_stats,
    group_stats_multi,
    timecourse_group_stats,
    timecourse_group_stats_multi,
    generic_aggregate
)

# Unified aggregation service (complex, feature-rich)
from .service import (
    AggregationService,
    AggregationConfig,
    AggregationResult,
    create_aggregation_service,
    simple_group_stats,
    multi_group_stats
)

__all__ = [
    # Core functions
    'group_stats',
    'group_stats_multi', 
    'timecourse_group_stats',
    'timecourse_group_stats_multi',
    'generic_aggregate',
    
    # Unified service
    'AggregationService',
    'AggregationConfig',
    'AggregationResult',
    'create_aggregation_service',
    'simple_group_stats',
    'multi_group_stats'
]


