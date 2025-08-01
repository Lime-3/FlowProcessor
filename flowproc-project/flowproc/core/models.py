"""
Core data models for flow cytometry processing.
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

from .constants import ProcessingMode, ExportFormat, VisualizationType, ValidationLevel


class ProcessingOptions(BaseModel):
    """Options for data processing."""
    model_config = ConfigDict(extra='forbid')
    
    mode: ProcessingMode = ProcessingMode.SINGLE_FILE
    time_course: bool = False
    auto_detect_columns: bool = True
    validate_data: bool = True
    aggregation_methods: List[str] = Field(default_factory=lambda: ['mean'])
    chunk_size: int = Field(default=1000, ge=100)
    max_workers: int = Field(default=4, ge=1)
    memory_limit_gb: float = Field(default=4.0, gt=0)


class ExportOptions(BaseModel):
    """Options for data export."""
    model_config = ConfigDict(extra='forbid')
    
    format: ExportFormat = ExportFormat.EXCEL
    include_index: bool = False
    include_headers: bool = True
    auto_adjust_columns: bool = True
    sheet_name: Optional[str] = None
    decimal_places: int = Field(default=2, ge=0, le=10)


class VisualizationOptions(BaseModel):
    """Options for data visualization."""
    model_config = ConfigDict(extra='forbid')
    
    plot_type: VisualizationType = VisualizationType.LINE_PLOT
    theme: str = 'plotly'
    width: int = Field(default=600, ge=300)  # Wide default width for better timecourse aspect ratio
    height: int = Field(default=300, ge=300)  # Short height for better timecourse visualization
    dpi: int = Field(default=600, ge=72, le=1200)
    show_legend: bool = True
    show_grid: bool = True
    
    @field_validator('theme')
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme name."""
        valid_themes = ['plotly', 'plotly_white', 'plotly_dark', 'ggplot2', 'seaborn', 'simple_white']
        if v not in valid_themes:
            raise ValueError(f"Theme must be one of {valid_themes}")
        return v


class ProcessingConfig(BaseModel):
    """Main configuration for processing flow cytometry data."""
    model_config = ConfigDict(extra='forbid')
    
    input_paths: List[Path] = Field(..., min_length=1)
    output_dir: Path
    processing_options: ProcessingOptions = Field(default_factory=ProcessingOptions)
    export_options: ExportOptions = Field(default_factory=ExportOptions)
    visualization_options: Optional[VisualizationOptions] = None
    
    @field_validator('input_paths')
    @classmethod
    def validate_input_paths(cls, v: List[Path]) -> List[Path]:
        """Validate that all input paths exist."""
        for path in v:
            if not path.exists():
                raise ValueError(f"Input path does not exist: {path}")
        return v
    
    @field_validator('output_dir')
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Create output directory if it doesn't exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class VisualizationConfig(BaseModel):
    """Configuration for data visualization."""
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
                    "example": {
            "plot_type": "bar",
            "width": 500,
            "height": 300,
            "title": "Flow Cytometry Results"
        }
        }
    )
    
    plot_type: str = Field(default='line', pattern='^(bar|line|scatter|box|violin)$')
    width: int = Field(default=600, ge=300, le=3000)  # Wide default width for better timecourse aspect ratio
    height: int = Field(default=300, ge=300, le=1500)  # Short height for better timecourse visualization
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    theme: str = Field(default='plotly')
    show_legend: bool = True
    show_grid: bool = True
    color_palette: Optional[List[str]] = None


class ProcessingResult(BaseModel):
    """Result of data processing operation."""
    model_config = ConfigDict(extra='allow')
    
    success: bool
    file_path: Optional[Path] = None
    records_processed: int = 0
    processing_time: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of data validation."""
    model_config = ConfigDict(extra='forbid')
    
    is_valid: bool
    validation_level: ValidationLevel
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class DatasetInfo(BaseModel):
    """Information about a dataset."""
    model_config = ConfigDict(extra='allow')
    
    name: str
    path: Path
    size_bytes: int
    row_count: int
    column_count: int
    column_names: List[str]
    data_types: Dict[str, str]
    creation_time: datetime
    modification_time: datetime
    processing_history: List[Dict[str, Any]] = Field(default_factory=list)