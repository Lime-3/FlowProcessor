"""
Data aggregation components for flow cytometry data processing.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from ...core.exceptions import ProcessingError
from .vectorized_aggregator import VectorizedAggregator, AggregationConfig, AggregationResult

logger = logging.getLogger(__name__)


@dataclass
class AggregationStats:
    """Statistics for aggregation operations."""
    total_groups: int = 0
    total_metrics: int = 0
    total_samples: int = 0
    groups_processed: int = 0
    metrics_processed: int = 0
    failed_groups: List[str] = field(default_factory=list)
    failed_metrics: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    memory_usage: float = 0.0


class DataAggregator:
    """Base class for data aggregation strategies."""
    
    def aggregate(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """Aggregate data frame."""
        raise NotImplementedError("Subclasses must implement aggregate method") 