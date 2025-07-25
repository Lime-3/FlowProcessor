"""
Constants and configuration values for flow cytometry processing.
"""

from enum import Enum, auto
from typing import Dict, List, Any

class ProcessingMode(Enum):
    """Processing modes for flow cytometry data."""
    SINGLE_FILE = auto()
    BATCH = auto()
    DIRECTORY = auto()
    TIME_COURSE = auto()

class ExportFormat(Enum):
    """Supported export formats."""
    EXCEL = 'xlsx'
    CSV = 'csv'
    TSV = 'tsv'
    JSON = 'json'
    HDF5 = 'h5'

class VisualizationType(Enum):
    """Types of visualizations supported."""
    BAR_PLOT = 'bar'
    LINE_PLOT = 'line'
    SCATTER_PLOT = 'scatter'
    HEATMAP = 'heatmap'
    BOX_PLOT = 'box'
    VIOLIN_PLOT = 'violin'

class AggregationMethod(Enum):
    """Aggregation methods for data processing."""
    MEAN = 'mean'
    MEDIAN = 'median'
    SUM = 'sum'
    COUNT = 'count'
    STD = 'std'
    MIN = 'min'
    MAX = 'max'

class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = 'strict'
    NORMAL = 'normal'
    RELAXED = 'relaxed'

class Constants(Enum):
    """Application constants."""
    UNKNOWN_TISSUE = "UNK"
    UNKNOWN_WELL = "UNK"
    DEFAULT_TIME = 0.0
    DEFAULT_GROUP = 0
    DEFAULT_ANIMAL = 0
    DEFAULT_REPLICATE = 1

# Default configuration
DEFAULT_CONFIG = {
    'processing_mode': ProcessingMode.SINGLE_FILE,
    'export_format': ExportFormat.EXCEL,
    'validation_level': ValidationLevel.NORMAL,
    'auto_parse_groups': True,
    'time_course_mode': False,
    'max_workers': 4,
    'chunk_size': 1000,
    'memory_limit_gb': 4.0,
}

# Supported file formats
SUPPORTED_INPUT_FORMATS = ['.csv', '.tsv', '.txt', '.xlsx', '.xls']
SUPPORTED_OUTPUT_FORMATS = ['.xlsx', '.csv', '.tsv', '.json', '.h5']

# Column patterns for detection
COLUMN_PATTERNS = {
    'sample_id': r'(?i)(sample.*id|sample.*name|filename|file.*name)',
    'group': r'(?i)(group|treatment|condition)',
    'time': r'(?i)(time|timepoint|hour|day)',
    'replicate': r'(?i)(replicate|rep|duplicate)',
    'well': r'(?i)(well|position|location)',
    'animal': r'(?i)(animal|mouse|subject|patient)',
    'tissue': r'(?i)(tissue|organ|sample.*type)'
}

# Keywords for flow cytometry metrics
KEYWORDS = {
    'Freq. of Parent': 'freq. of parent',
    'Freq. of Total': 'freq. of total',
    'Count': 'count',
    'Median': 'median',
    'Mean': 'mean',
    'Geometric Mean': 'geometric mean',
    'Mode': 'mode',
    'CV': 'cv',
    'MAD': 'mad'
}

# Metric keywords for flow cytometry data
METRIC_KEYWORDS = {
    'frequency': ['freq', 'frequency', '%'],
    'median': ['median', 'med'],
    'mean': ['mean', 'avg', 'average'],
    'count': ['count', 'events', 'cells'],
    'geometric_mean': ['geomean', 'geo_mean', 'geometric'],
    'coefficient_of_variation': ['cv', 'coefficient'],
    'standard_deviation': ['sd', 'std', 'standard'],
    'minimum': ['min', 'minimum'],
    'maximum': ['max', 'maximum']
}

# Error messages
ERROR_MESSAGES = {
    'file_not_found': 'File not found: {filepath}',
    'invalid_format': 'Invalid file format: {format}',
    'missing_columns': 'Missing required columns: {columns}',
    'empty_dataframe': 'DataFrame is empty',
    'parsing_failed': 'Failed to parse: {reason}',
    'processing_failed': 'Processing failed: {reason}',
    'export_failed': 'Export failed: {reason}',
    'visualization_failed': 'Visualization failed: {reason}',
    'validation_failed': 'Validation failed: {reason}',
    'configuration_error': 'Configuration error: {reason}'
}

# Success messages
SUCCESS_MESSAGES = {
    'file_loaded': 'Successfully loaded: {filepath}',
    'processing_complete': 'Processing completed successfully',
    'export_complete': 'Exported to: {filepath}',
    'visualization_saved': 'Visualization saved to: {filepath}',
    'validation_passed': 'Validation passed',
    'batch_complete': 'Batch processing completed: {count} files'
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'flowproc.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        'flowproc': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

# Tissue mappings
TISSUE_MAPPINGS = {
    'SP': 'Spleen',
    'BM': 'Bone Marrow',
    'LN': 'Lymph Node',
    'WB': 'Whole Blood',
    'TH': 'Thymus',
    'PB': 'Peripheral Blood'
} 