# flowproc
A tool for processing flow cytometry CSV files into Excel format.

## Features

- Process FlowJo CSV exports into organized Excel workbooks
- Support for time-course studies
- Automatic tissue detection and parsing
- Manual or automatic group/replicate configuration
- GUI and command-line interfaces

## Installation

```bash
pip install -e .
```

## Usage

### GUI Mode
```bash
python -m flowproc.gui
```

### Command Line Mode
```bash
python -m flowproc.cli --input-dir /path/to/csv/files --output-dir /path/to/output
```

## Logging

The application automatically creates a `logs/` directory in the current working directory and writes log files to `logs/processing.log`. This directory is created automatically if it doesn't exist, making the tool suitable for distribution.

### Log File Location
- **Default**: `./logs/processing.log` (relative to current working directory)
- **Created automatically**: The `logs/` directory is created if it doesn't exist
- **Distribution ready**: Uses relative paths, no hardcoded absolute paths

## Supported FlowJo Metrics

The tool recognizes and processes the following FlowJo table export metrics:
- Frequency of Parent
- Frequency of Live  
- Median
- Mean
- Count
- Geometric Mean (GeoMean)
- Coefficient of Variation (CV)
- Standard Deviation (SD)
- Minimum (Min)
- Maximum (Max)
- Sum
- Mode
- Range
