"""
Data processing module for flow cytometry data.
"""

import gc
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Callable
from contextlib import contextmanager
import pandas as pd
import numpy as np
import psutil

from ...core.exceptions import ProcessingError
from ...core.models import ProcessingConfig

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage during processing."""
    
    def __init__(self, limit_mb: int = 2048):
        """
        Initialize memory monitor.
        
        Args:
            limit_mb: Memory limit in megabytes
        """
        self.limit_mb = limit_mb
        self.process = psutil.Process()
        
    def check_memory(self) -> float:
        """
        Check current memory usage.
        
        Returns:
            Memory usage in MB
            
        Raises:
            MemoryError: If memory limit exceeded
        """
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        
        if memory_mb > self.limit_mb:
            gc.collect()  # Try to free memory
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.limit_mb:
                raise MemoryError(
                    f"Memory usage ({memory_mb:.0f}MB) exceeds limit ({self.limit_mb}MB)"
                )
                
        return memory_mb
    
    @contextmanager
    def monitor(self, operation: str):
        """Context manager for monitoring an operation."""
        start_memory = self.check_memory()
        logger.debug(f"{operation}: Starting (memory: {start_memory:.0f}MB)")
        
        try:
            yield
        finally:
            end_memory = self.check_memory()
            delta = end_memory - start_memory
            logger.debug(
                f"{operation}: Completed (memory: {end_memory:.0f}MB, "
                f"delta: {delta:+.0f}MB)"
            )


class ChunkedDataProcessor:
    """Process large datasets in chunks to manage memory."""
    
    def __init__(self, config: ProcessingConfig):
        """Initialize with processing configuration."""
        self.config = config
        self.memory_monitor = MemoryMonitor(config.memory_limit_mb)
        
    def process_dataframe_chunks(
        self,
        df: pd.DataFrame,
        process_func: Callable[[pd.DataFrame], pd.DataFrame],
        chunk_column: str = 'Group'
    ) -> pd.DataFrame:
        """
        Process DataFrame in chunks based on a column.
        
        Args:
            df: Input DataFrame
            process_func: Function to apply to each chunk
            chunk_column: Column to use for chunking
            
        Returns:
            Processed DataFrame
        """
        if len(df) <= self.config.chunk_size:
            # Small enough to process at once
            return process_func(df)
            
        # Process in chunks
        unique_values = df[chunk_column].unique()
        results: List[pd.DataFrame] = []
        
        with self.memory_monitor.monitor("Chunked processing"):
            for value in unique_values:
                chunk = df[df[chunk_column] == value]
                
                with self.memory_monitor.monitor(f"Processing {chunk_column}={value}"):
                    result = process_func(chunk)
                    results.append(result)
                    
                # Clean up chunk
                del chunk
                
                # Check memory periodically
                if len(results) % 10 == 0:
                    self.memory_monitor.check_memory()
                    
        # Combine results
        return pd.concat(results, ignore_index=True)
        
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage.
        
        Args:
            df: DataFrame to optimize
            
        Returns:
            Optimized DataFrame
        """
        start_mem = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        # Optimize numeric columns
        for col in df.select_dtypes(include=['int64']).columns:
            try:
                df[col] = pd.to_numeric(df[col], downcast='integer')
            except (ValueError, TypeError):
                pass
                
        for col in df.select_dtypes(include=['float64']).columns:
            try:
                df[col] = pd.to_numeric(df[col], downcast='float')
            except (ValueError, TypeError):
                pass
            
        # Convert string columns to category if beneficial
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique
                df[col] = df[col].astype('category')
                
        end_mem = df.memory_usage(deep=True).sum() / 1024 / 1024
        reduction = (start_mem - end_mem) / start_mem * 100
        
        logger.info(
            f"Memory optimization: {start_mem:.1f}MB → {end_mem:.1f}MB "
            f"({reduction:.1f}% reduction)"
        )
        
        return df