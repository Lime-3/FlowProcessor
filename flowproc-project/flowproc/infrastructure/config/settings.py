"""
Configuration settings management for flow cytometry processing.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import yaml
from pydantic import BaseModel, Field, field_validator, ConfigDict

from ...core.exceptions import ConfigurationError
from ...core.protocols import ConfigurationManager


class ApplicationSettings(BaseModel):
    """Application-wide settings."""
    model_config = ConfigDict(extra='forbid')
    
    app_name: str = "FlowProc"
    version: str = "2.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    max_file_size_mb: float = Field(default=100.0, gt=0)
    temp_dir: Optional[Path] = None
    cache_enabled: bool = True
    cache_size_mb: float = Field(default=500.0, gt=0)


class ProcessingSettings(BaseModel):
    """Settings for data processing."""
    model_config = ConfigDict(extra='forbid')
    
    auto_detect_columns: bool = True
    validate_input: bool = True
    parallel_processing: bool = True
    chunk_size: int = Field(default=1000, ge=100)
    max_workers: int = Field(default=4, ge=1)
    memory_limit_gb: float = Field(default=4.0, gt=0)
    timeout_seconds: int = Field(default=300, ge=10)


class VisualizationSettings(BaseModel):
    """Settings for visualization."""
    model_config = ConfigDict(extra='forbid')
    
    default_theme: str = "plotly"
    default_width: int = Field(default=800, ge=400)
    default_height: int = Field(default=600, ge=300)
    dpi: int = Field(default=100, ge=72, le=300)
    save_format: str = "png"
    interactive: bool = True
    
    @field_validator('default_theme')
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme name."""
        valid_themes = ['plotly', 'plotly_white', 'plotly_dark', 'ggplot2', 'seaborn', 'simple_white']
        if v not in valid_themes:
            raise ValueError(f"Theme must be one of {valid_themes}")
        return v


class ExportSettings(BaseModel):
    """Settings for data export."""
    model_config = ConfigDict(extra='forbid')
    
    default_format: str = "xlsx"
    include_metadata: bool = True
    compress_output: bool = False
    auto_adjust_columns: bool = True
    decimal_places: int = Field(default=2, ge=0, le=10)
    sheet_name_template: str = "{metric}"


class Settings(BaseModel):
    """Main settings container."""
    model_config = ConfigDict(extra='forbid')
    
    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    visualization: VisualizationSettings = Field(default_factory=VisualizationSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)
    
    @classmethod
    def from_file(cls, file_path: Path) -> "Settings":
        """Load settings from file."""
        if not file_path.exists():
            raise ConfigurationError(f"Settings file not found: {file_path}")
            
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
            elif file_path.suffix in ['.yaml', '.yml']:
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
            else:
                raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
                
            return cls(**data)
        except Exception as e:
            raise ConfigurationError(f"Failed to load settings: {str(e)}") from e
    
    def save(self, file_path: Path) -> None:
        """Save settings to file."""
        try:
            data = self.model_dump()
            
            if file_path.suffix == '.json':
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            elif file_path.suffix in ['.yaml', '.yml']:
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:
                raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
                
        except Exception as e:
            raise ConfigurationError(f"Failed to save settings: {str(e)}") from e


class FileConfigManager(ConfigurationManager):
    """File-based configuration manager."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize with optional config file."""
        self._settings = Settings()
        
        if config_file and config_file.exists():
            self._settings = Settings.from_file(config_file)
            
        self._config_file = config_file
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        parts = key.split('.')
        value = self._settings
        
        try:
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return default
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key."""
        parts = key.split('.')
        
        if not parts:
            raise ConfigurationError("Invalid configuration key")
            
        # Navigate to the parent object
        obj = self._settings
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                raise ConfigurationError(f"Invalid configuration path: {key}")
                
        # Set the value
        if hasattr(obj, parts[-1]):
            setattr(obj, parts[-1], value)
        else:
            raise ConfigurationError(f"Invalid configuration key: {key}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return self._settings.model_dump()
    
    def reload(self) -> None:
        """Reload configuration from file."""
        if self._config_file and self._config_file.exists():
            self._settings = Settings.from_file(self._config_file)
    
    def save(self) -> None:
        """Save current configuration to file."""
        if self._config_file:
            self._settings.save(self._config_file)