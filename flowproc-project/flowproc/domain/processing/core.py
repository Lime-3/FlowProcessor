"""
Core processing architecture with clear separation of concerns.

This module defines the foundational processing components that eliminate
duplication across the three processing classes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol
import pandas as pd
from dataclasses import dataclass
from enum import Enum

from ...core.exceptions import ProcessingError


class ProcessingMode(Enum):
    """Defines different processing modes."""
    GENERIC = "generic"
    VISUALIZATION = "visualization"
    WORKFLOW = "workflow"


@dataclass
class ProcessingConfig:
    """Unified configuration for all processing operations."""
    mode: ProcessingMode
    group_by: List[str] = None
    aggregation_methods: List[str] = None
    transform_options: Dict[str, Any] = None
    filter_options: Dict[str, Any] = None
    visualization_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.group_by is None:
            self.group_by = []
        if self.aggregation_methods is None:
            self.aggregation_methods = ['mean']
        if self.transform_options is None:
            self.transform_options = {}
        if self.filter_options is None:
            self.filter_options = {}
        if self.visualization_options is None:
            self.visualization_options = {}


class DataProcessor(Protocol):
    """Protocol defining the interface for data processors."""
    
    def process(self, df: pd.DataFrame, config: ProcessingConfig) -> pd.DataFrame:
        """Process data according to configuration."""
        ...


class ProcessingStrategy(ABC):
    """Abstract base class for processing strategies."""
    
    @abstractmethod
    def can_handle(self, config: ProcessingConfig) -> bool:
        """Check if this strategy can handle the given configuration."""
        pass
    
    @abstractmethod
    def process(self, df: pd.DataFrame, config: ProcessingConfig) -> pd.DataFrame:
        """Process data using this strategy."""
        pass


class GenericProcessingStrategy(ProcessingStrategy):
    """Handles generic data processing operations."""
    
    def __init__(self):
        from .transformers import DataTransformer
        self.aggregator = None  # Will be initialized when needed
        self.transformer = DataTransformer()
    
    def can_handle(self, config: ProcessingConfig) -> bool:
        return config.mode == ProcessingMode.GENERIC
    
    def process(self, df: pd.DataFrame, config: ProcessingConfig) -> pd.DataFrame:
        """Apply generic transformations and aggregations."""
        result_df = df.copy()
        
        # Apply transformations
        if config.transform_options:
            result_df = self._apply_transformations(result_df, config.transform_options)
        
        # Apply aggregations
        if config.group_by and config.aggregation_methods:
            result_df = self._apply_aggregations(result_df, config.group_by, config.aggregation_methods)
        
        return result_df
    
    def _apply_transformations(self, df: pd.DataFrame, options: Dict[str, Any]) -> pd.DataFrame:
        """Apply data transformations."""
        return self.transformer.transform(df, options)
    
    def _apply_aggregations(self, df: pd.DataFrame, group_by: List[str], methods: List[str]) -> pd.DataFrame:
        """Apply data aggregations."""
        # Initialize aggregator if not already done
        if self.aggregator is None:
            from ..aggregation import AggregationService
            # Use the first column as sid_col for now - this should be configurable
            sid_col = df.columns[0] if len(df.columns) > 0 else 'SampleID'
            self.aggregator = AggregationService(df, sid_col)
        
        # Use the unified aggregation service
        return self.aggregator.export_aggregate(df, group_by, methods)


class VisualizationProcessingStrategy(ProcessingStrategy):
    """Handles visualization-specific processing."""
    
    def can_handle(self, config: ProcessingConfig) -> bool:
        return config.mode == ProcessingMode.VISUALIZATION
    
    def process(self, df: pd.DataFrame, config: ProcessingConfig) -> pd.DataFrame:
        """Apply visualization-specific processing."""
        result_df = df.copy()
        
        # Apply visualization-specific filters
        if config.filter_options:
            result_df = self._apply_visualization_filters(result_df, config.filter_options)
        
        # Apply visualization-specific transformations
        if config.visualization_options:
            result_df = self._apply_visualization_transformations(result_df, config.visualization_options)
        
        return result_df
    
    def _apply_visualization_filters(self, df: pd.DataFrame, filter_options: Dict[str, Any]) -> pd.DataFrame:
        """Apply visualization-specific filters."""
        result_df = df.copy()
        
        # Apply tissue filter
        if filter_options.get('tissue_filter') and 'Tissue' in result_df.columns:
            tissue_filter = filter_options['tissue_filter']
            result_df = result_df[result_df['Tissue'] == tissue_filter]
        
        # Apply subpopulation filter (basic implementation)
        if filter_options.get('subpopulation_filter'):
            # This would be implemented based on specific requirements
            pass
        
        return result_df
    
    def _apply_visualization_transformations(self, df: pd.DataFrame, viz_options: Dict[str, Any]) -> pd.DataFrame:
        """Apply visualization-specific transformations."""
        result_df = df.copy()
        
        # Apply time-course mode transformations
        if viz_options.get('time_course_mode'):
            # Ensure time column is properly formatted
            if 'Time' in result_df.columns:
                result_df['Time'] = pd.to_numeric(result_df['Time'], errors='coerce')
        
        # Apply metric-specific transformations
        if viz_options.get('metric'):
            # This would apply metric-specific processing
            pass
        
        return result_df


class WorkflowProcessingStrategy(ProcessingStrategy):
    """Handles workflow orchestration processing."""
    
    def __init__(self):
        from .transformers import DataTransformer
        self.aggregator = None  # Will be initialized when needed
        self.transformer = DataTransformer()
    
    def can_handle(self, config: ProcessingConfig) -> bool:
        return config.mode == ProcessingMode.WORKFLOW
    
    def process(self, df: pd.DataFrame, config: ProcessingConfig) -> pd.DataFrame:
        """Apply workflow-specific processing."""
        result_df = df.copy()
        
        # Step 1: Apply transformations
        if config.transform_options:
            result_df = self._apply_transformations(result_df, config.transform_options)
        
        # Step 2: Apply aggregations
        if config.group_by and config.aggregation_methods:
            result_df = self._apply_aggregations(result_df, config.group_by, config.aggregation_methods)
        
        # Step 3: Apply workflow-specific processing
        if config.visualization_options:
            result_df = self._apply_workflow_processing(result_df, config.visualization_options)
        
        return result_df
    
    def _apply_transformations(self, df: pd.DataFrame, options: Dict[str, Any]) -> pd.DataFrame:
        """Apply data transformations."""
        return self.transformer.transform(df, options)
    
    def _apply_aggregations(self, df: pd.DataFrame, group_by: List[str], methods: List[str]) -> pd.DataFrame:
        """Apply data aggregations."""
        # Initialize aggregator if not already done
        if self.aggregator is None:
            from ..aggregation import AggregationService
            # Use the first column as sid_col for now - this should be configurable
            sid_col = df.columns[0] if len(df.columns) > 0 else 'SampleID'
            self.aggregator = AggregationService(df, sid_col)
        
        # Use the unified aggregation service
        return self.aggregator.export_aggregate(df, group_by, methods)
    
    def _apply_workflow_processing(self, df: pd.DataFrame, workflow_options: Dict[str, Any]) -> pd.DataFrame:
        """Apply workflow-specific processing."""
        result_df = df.copy()
        
        # Apply any workflow-specific transformations
        # This could include data validation, quality checks, etc.
        
        return result_df


class UnifiedProcessingService:
    """
    Unified processing service that eliminates duplication.
    
    This service acts as the single point of entry for all data processing,
    delegating to appropriate strategies based on the processing mode.
    """
    
    def __init__(self):
        self.strategies: List[ProcessingStrategy] = [
            GenericProcessingStrategy(),
            VisualizationProcessingStrategy(),
            WorkflowProcessingStrategy()
        ]
    
    def process_data(self, df: pd.DataFrame, config: ProcessingConfig) -> pd.DataFrame:
        """Process data using the appropriate strategy."""
        try:
            # Find the appropriate strategy
            strategy = self._get_strategy(config)
            if not strategy:
                raise ProcessingError(f"No strategy found for mode: {config.mode}")
            
            return strategy.process(df, config)
            
        except Exception as e:
            raise ProcessingError(f"Processing failed: {str(e)}") from e
    
    def _get_strategy(self, config: ProcessingConfig) -> Optional[ProcessingStrategy]:
        """Get the appropriate strategy for the configuration."""
        for strategy in self.strategies:
            if strategy.can_handle(config):
                return strategy
        return None
    
    def validate_config(self, config: ProcessingConfig) -> Dict[str, Any]:
        """Validate processing configuration."""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Basic validation
        if not isinstance(config.mode, ProcessingMode):
            validation['errors'].append("Invalid processing mode")
            validation['valid'] = False
        
        # Strategy-specific validation
        strategy = self._get_strategy(config)
        if strategy:
            # Delegate to strategy for specific validation
            pass
        
        return validation 