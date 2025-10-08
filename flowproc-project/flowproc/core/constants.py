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

class DataType(Enum):
    """Types of data that can be processed."""
    FLOW_CYTOMETRY = 'flow'
    GENERIC_LAB = 'lab'  # Clinical chemistry, CBC, etc.

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
    'Freq. of Live': 'freq. of live',
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
    'PB': 'Peripheral Blood',
    'TH': 'Thymus',
    'LI': 'Liver',
    'KI': 'Kidney',
    'LU': 'Lung',
    'BR': 'Brain',
    'HE': 'Heart',
    'ST': 'Stomach',
    'IN': 'Intestine',
    'SK': 'Skin',
    'MU': 'Muscle',
    'FA': 'Fat',
    'UNK': 'Unknown'
}

def is_pure_metric_column(col_name: str, metric_keyword: str) -> bool:
    """
    Determine if a column is a pure metric (not a subpopulation).
    
    Args:
        col_name: Column name to check
        metric_keyword: The metric keyword found in the column
        
    Returns:
        True if this is a pure metric column, False if it's a subpopulation
    """
    col_lower = col_name.lower()
    
    # Pure metric columns typically:
    # 1. Start with the metric keyword
    # 2. Don't contain subpopulation indicators like "CD4+", "CD8+", "B Cells", etc.
    # 3. Don't contain separators like " | " that indicate subpopulations
    
    # Check if column starts with the metric keyword (pure metric)
    if col_lower.startswith(metric_keyword.lower()):
        return True
    
    # Check if column contains separators that indicate subpopulations
    subpopulation_separators = [' | ', ' |', '| ', ' - ', ' -', '- ']
    for separator in subpopulation_separators:
        if separator in col_name:
            return False
    
    # Check if column contains path separators (like "Live/CD4+/GFP+")
    if '/' in col_name:
        return False
    
    # Check if column contains subpopulation indicators that are NOT part of a valid metric
    # Only filter out if the subpopulation indicator is NOT preceded by a metric keyword
    subpopulation_indicators = [
        'cd4+', 'cd8+', 'cd3+', 'cd19+', 'cd11b+', 'cd11c+', 'f4/80+', 'ly6g+', 'ly6c+',
        'b cells', 't cells', 'nk cells', 'monocytes', 'neutrophils', 'macrophages',
        'dendritic cells', 'regulatory t cells', 'th1', 'th2', 'th17', 'treg',
        'memory', 'naive', 'effector', 'central', 'peripheral'
    ]
    
    # Only filter out if the column contains a subpopulation indicator AND doesn't start with a metric keyword
    for indicator in subpopulation_indicators:
        if indicator in col_lower and not col_lower.startswith(metric_keyword.lower()):
            return False
    
    # If none of the above conditions are met, it's likely a pure metric
    return True 