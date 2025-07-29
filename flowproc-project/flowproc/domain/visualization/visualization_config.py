"""
Configuration and validation for the visualization system.

This module handles all configuration logic, validation rules,
and parameter management for the visualization domain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import logging

from ...core.constants import KEYWORDS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VisualizationConfig:
    """
    Configuration for visualization generation.
    
    This immutable configuration object contains all parameters
    needed to generate visualizations, with comprehensive validation
    and sensible defaults.
    
    Attributes:
        metric: Specific metric to visualize (None for all metrics)
        width: Plot width in pixels (default: 600)
        height: Plot height in pixels (None for dynamic sizing, default: 300)
        theme: Theme name for styling (default: "default")
        time_course_mode: Whether to create time-course visualizations
        user_replicates: User-defined replicate assignments
        auto_parse_groups: Whether to automatically parse group information
        user_group_labels: Custom labels for groups
        tissue_filter: Filter data to specific tissue
        subpopulation_filter: Filter data to specific subpopulation
        show_individual_points: Whether to show individual data points
        error_bars: Whether to display error bars
        color_palette: Custom color palette for groups
        export_format: Default export format ('html', 'png', 'svg', 'pdf')
        interactive: Whether plots should be interactive
    """
    # Core visualization parameters
    metric: Optional[str] = None
    width: int = 600
    height: Optional[int] = 300
    theme: str = "default"
    
    # Mode and behavior settings
    time_course_mode: bool = False
    auto_parse_groups: bool = True
    show_individual_points: bool = False
    error_bars: bool = True
    interactive: bool = True
    
    # Data filtering and grouping
    user_replicates: Optional[List[int]] = None
    user_group_labels: Optional[List[str]] = None
    tissue_filter: Optional[str] = None
    subpopulation_filter: Optional[str] = None
    
    # Styling options
    color_palette: Optional[List[str]] = None
    export_format: str = "html"
    
    def __post_init__(self) -> None:
        """Validate configuration parameters after initialization."""
        errors = self._validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
    
    def _validate(self) -> List[str]:
        """
        Validate all configuration parameters.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate dimensions
        if self.width <= 0:
            errors.append("Width must be a positive integer")
        
        if self.height is not None and self.height <= 0:
            errors.append("Height must be a positive integer or None for dynamic sizing")
        
        # Validate metric
        if self.metric and self.metric not in KEYWORDS:
            available_metrics = ', '.join(KEYWORDS.keys())
            errors.append(f"Invalid metric '{self.metric}'. Valid options: {available_metrics}")
        
        # Validate theme
        if not isinstance(self.theme, str) or not self.theme.strip():
            errors.append("Theme must be a non-empty string")
        
        # Validate export format
        valid_formats = {'html', 'png', 'svg', 'pdf'}
        if self.export_format not in valid_formats:
            errors.append(f"Invalid export format '{self.export_format}'. Valid options: {', '.join(valid_formats)}")
        
        # Validate user replicates
        if self.user_replicates is not None:
            if not isinstance(self.user_replicates, list):
                errors.append("user_replicates must be a list or None")
            elif not all(isinstance(r, int) and r > 0 for r in self.user_replicates):
                errors.append("All user_replicates must be positive integers")
        
        # Validate user group labels
        if self.user_group_labels is not None:
            if not isinstance(self.user_group_labels, list):
                errors.append("user_group_labels must be a list or None")
            elif not all(isinstance(label, str) for label in self.user_group_labels):
                errors.append("All user_group_labels must be strings")
        
        # Validate color palette
        if self.color_palette is not None:
            if not isinstance(self.color_palette, list):
                errors.append("color_palette must be a list or None")
            elif not all(isinstance(color, str) for color in self.color_palette):
                errors.append("All colors in color_palette must be strings")
        
        return errors
    
    @classmethod
    def create_default(cls) -> VisualizationConfig:
        """
        Create a default configuration.
        
        Returns:
            Default VisualizationConfig instance
        """
        return cls()
    
    @classmethod
    def create_time_course(
        cls,
        metric: Optional[str] = None,
        width: int = 1000,
        height: int = 400,
        **kwargs
    ) -> VisualizationConfig:
        """
        Create a configuration optimized for time-course visualizations.
        
        Args:
            metric: Specific metric to visualize
            width: Plot width (default: 1000 for better time-course viewing)
            height: Plot height (default: 400 for better time-course viewing)
            **kwargs: Additional configuration parameters
        
        Returns:
            VisualizationConfig optimized for time-course data
        """
        return cls(
            metric=metric,
            width=width,
            height=height,
            time_course_mode=True,
            show_individual_points=True,
            **kwargs
        )
    
    @classmethod
    def create_publication_ready(
        cls,
        metric: Optional[str] = None,
        width: int = 800,
        height: int = 600,
        **kwargs
    ) -> VisualizationConfig:
        """
        Create a configuration for publication-ready figures.
        
        Args:
            metric: Specific metric to visualize
            width: Plot width (default: 800)
            height: Plot height (default: 600)
            **kwargs: Additional configuration parameters
        
        Returns:
            VisualizationConfig optimized for publication
        """
        return cls(
            metric=metric,
            width=width,
            height=height,
            theme="publication",
            show_individual_points=False,
            error_bars=True,
            interactive=False,
            export_format="svg",
            **kwargs
        )
    
    def with_updates(self, **kwargs) -> VisualizationConfig:
        """
        Create a new configuration with updated parameters.
        
        Args:
            **kwargs: Parameters to update
        
        Returns:
            New VisualizationConfig with updated parameters
        """
        # Get current configuration as dict
        current_config = {
            'metric': self.metric,
            'width': self.width,
            'height': self.height,
            'theme': self.theme,
            'time_course_mode': self.time_course_mode,
            'auto_parse_groups': self.auto_parse_groups,
            'show_individual_points': self.show_individual_points,
            'error_bars': self.error_bars,
            'interactive': self.interactive,
            'user_replicates': self.user_replicates,
            'user_group_labels': self.user_group_labels,
            'tissue_filter': self.tissue_filter,
            'subpopulation_filter': self.subpopulation_filter,
            'color_palette': self.color_palette,
            'export_format': self.export_format,
        }
        
        # Update with new values
        current_config.update(kwargs)
        
        return VisualizationConfig(**current_config)
    
    def get_display_settings(self) -> Dict[str, Any]:
        """
        Get settings relevant for display.
        
        Returns:
            Dictionary of display-related settings
        """
        return {
            'width': self.width,
            'height': self.height,
            'theme': self.theme,
            'interactive': self.interactive,
            'show_individual_points': self.show_individual_points,
            'error_bars': self.error_bars,
        }
    
    def get_data_settings(self) -> Dict[str, Any]:
        """
        Get settings relevant for data processing.
        
        Returns:
            Dictionary of data processing settings
        """
        return {
            'metric': self.metric,
            'time_course_mode': self.time_course_mode,
            'auto_parse_groups': self.auto_parse_groups,
            'user_replicates': self.user_replicates,
            'user_group_labels': self.user_group_labels,
            'tissue_filter': self.tissue_filter,
            'subpopulation_filter': self.subpopulation_filter,
        }
    
    def __str__(self) -> str:
        """String representation of the configuration."""
        settings = []
        if self.metric:
            settings.append(f"metric={self.metric}")
        if self.time_course_mode:
            settings.append("time_course=True")
        if self.tissue_filter:
            settings.append(f"tissue={self.tissue_filter}")
        if self.subpopulation_filter:
            settings.append(f"subpop={self.subpopulation_filter}")
        
        settings_str = ", ".join(settings) if settings else "default"
        return f"VisualizationConfig({settings_str})"


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    
    This mutable model contains the results of validating
    configuration or data, including any errors and warnings.
    """
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error to the validation result."""
        self.errors.append(error)
        self.valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_summary(self) -> str:
        """Get a summary of the validation result."""
        if self.valid and not self.has_warnings():
            return "Validation passed"
        
        parts = []
        if self.has_errors():
            parts.append(f"{len(self.errors)} error(s)")
        if self.has_warnings():
            parts.append(f"{len(self.warnings)} warning(s)")
        
        return f"Validation failed: {', '.join(parts)}"


class ConfigurationValidator:
    """
    Validator for visualization configurations and parameters.
    
    This class provides comprehensive validation logic for all
    aspects of the visualization system configuration.
    """
    
    @staticmethod
    def validate_config(config: VisualizationConfig) -> ValidationResult:
        """
        Validate a visualization configuration.
        
        Args:
            config: Configuration to validate
        
        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(valid=True)
        
        try:
            # The configuration validation is already done in __post_init__
            # So if we reach here, it's valid
            pass
        except ValueError as e:
            result.add_error(str(e))
        
        # Additional semantic validations
        if config.time_course_mode and config.metric is None:
            result.add_warning(
                "Time course mode without specific metric may create many subplots"
            )
        
        if config.width > 2000 or (config.height and config.height > 1500):
            result.add_warning(
                "Very large plot dimensions may cause performance issues"
            )
        
        return result
    
    @staticmethod
    def validate_file_path(file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate a file path for visualization input.
        
        Args:
            file_path: Path to validate
        
        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(valid=True)
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                result.add_error(f"File does not exist: {file_path}")
                return result
            
            if not path.is_file():
                result.add_error(f"Path is not a file: {file_path}")
                return result
            
            if path.suffix.lower() not in {'.csv', '.xlsx', '.xls'}:
                result.add_warning(
                    f"Unexpected file extension: {path.suffix}. "
                    "Expected .csv, .xlsx, or .xls"
                )
            
            # Check file size (warn if very large)
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 100:
                result.add_warning(
                    f"Large file size ({size_mb:.1f} MB) may cause performance issues"
                )
            
        except Exception as e:
            result.add_error(f"Error validating file path: {str(e)}")
        
        return result
    
    @staticmethod
    def suggest_config_for_data(
        data_shape: tuple,
        has_time_data: bool,
        num_groups: int,
        num_tissues: int
    ) -> VisualizationConfig:
        """
        Suggest an optimal configuration based on data characteristics.
        
        Args:
            data_shape: Shape of the data (rows, columns)
            has_time_data: Whether the data contains time information
            num_groups: Number of groups in the data
            num_tissues: Number of tissues in the data
        
        Returns:
            Suggested VisualizationConfig
        """
        rows, cols = data_shape
        
        # Base configuration
        config_params = {}
        
        # Adjust for time course data
        if has_time_data:
            config_params.update({
                'time_course_mode': True,
                'width': 1200,  # Wider for time course
                'height': 600 if num_tissues > 1 else 400,
                'show_individual_points': True,
            })
        
        # Adjust for large datasets
        if rows > 10000:
            config_params.update({
                'show_individual_points': False,  # Performance optimization
            })
        
        # Adjust for many groups
        if num_groups > 6:
            config_params.update({
                'width': max(800, num_groups * 100),  # Wider for many groups
            })
        
        # Adjust for multiple tissues
        if num_tissues > 2:
            config_params.update({
                'height': max(600, num_tissues * 200),  # Taller for subplots
            })
        
        return VisualizationConfig(**config_params)


# Predefined configuration presets
class ConfigPresets:
    """Predefined configuration presets for common use cases."""
    
    @staticmethod
    def quick_exploration() -> VisualizationConfig:
        """Configuration for quick data exploration."""
        return VisualizationConfig(
            width=600,
            height=400,
            theme="default",
            show_individual_points=True,
            interactive=True
        )
    
    @staticmethod
    def publication_figure() -> VisualizationConfig:
        """Configuration for publication-ready figures."""
        return VisualizationConfig(
            width=800,
            height=600,
            theme="publication",
            show_individual_points=False,
            error_bars=True,
            interactive=False,
            export_format="svg"
        )
    
    @staticmethod
    def presentation_slide() -> VisualizationConfig:
        """Configuration for presentation slides."""
        return VisualizationConfig(
            width=1200,
            height=800,
            theme="presentation",
            show_individual_points=False,
            error_bars=True,
            interactive=False
        )
    
    @staticmethod
    def time_course_analysis() -> VisualizationConfig:
        """Configuration for time course analysis."""
        return VisualizationConfig(
            width=1400,
            height=600,
            theme="scientific",
            time_course_mode=True,
            show_individual_points=True,
            error_bars=True,
            interactive=True
        )
    
    @staticmethod
    def high_throughput_screening() -> VisualizationConfig:
        """Configuration for high-throughput screening data."""
        return VisualizationConfig(
            width=1000,
            height=800,
            theme="minimal",
            show_individual_points=False,  # Performance optimization
            error_bars=False,  # Cleaner look for many conditions
            interactive=True
        )
