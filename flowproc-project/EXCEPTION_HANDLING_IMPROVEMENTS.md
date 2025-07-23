# Exception Handling and Type Validation Improvements

This document summarizes the improvements made to FlowProcessor's exception handling and type validation.

## Key Improvements

### 1. Custom Exception Class
- Added `ProcessingError` exception class for better error categorization
- Located in `flowproc/visualize.py` alongside existing custom exceptions
- Used throughout the codebase for processing-related errors

### 2. Specific Exception Handling for CSV Reading

**Before:**
```python
try:
    df = pd.read_csv(filename)
except:  # Too broad - hides real issues
    pass
```

**After:**
```python
try:
    df = pd.read_csv(input_file, skipinitialspace=True, engine='python')
    # ... processing logic ...
except (FileNotFoundError, pd.errors.EmptyDataError) as e:
    logger.error(f"Failed to load {input_file}: {e}")
    raise ProcessingError(f"Invalid input file: {e}")
except pd.errors.ParserError as e:
    logger.error(f"CSV parsing error: {e}")
    raise ProcessingError(f"Failed to parse CSV: {e}")
```

### 3. Type Validation for Scientific Data

**Added type validation to key functions:**

```python
def validate_parsed_data(df: pd.DataFrame, sid_col: str) -> None:
    """Validate parsed DataFrame."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected DataFrame, got {type(df)}")
    # ... rest of validation ...
```

**Functions with added type validation:**
- `validate_parsed_data()` in `parsing.py` and `data_io.py`
- `_extract_metadata()` in `visualize.py`
- `_combine_dataframes()` in `visualize.py`
- `optimize_dataframe()` in `vectorized_aggregator.py`

### 4. Improved Broad Exception Handling

**Replaced broad exception catching with specific exceptions:**

**Before:**
```python
except Exception as e:
    logger.warning(f"Failed to parse sample ID '{sample_id}': {e}")
    return None, None, None, None
```

**After:**
```python
except (ValueError, AttributeError, IndexError) as e:
    logger.warning(f"Failed to parse sample ID '{sample_id}': {e}")
    return None, None, None, None
```

**Key areas improved:**
- Sample ID parsing in `data_io.py`
- Tissue extraction in `data_io.py`  
- Replicate mapping in `visualize.py`
- File processing in `writer.py`
- Async processing in `gui/async_processor.py`

## Benefits

1. **Better Error Diagnosis**: Specific exceptions make it easier to identify the root cause of issues
2. **Type Safety**: Type validation catches DataFrame type mismatches early
3. **Improved Logging**: More informative error messages with specific exception types
4. **Maintainability**: Clearer exception handling makes code easier to maintain and debug
5. **User Experience**: Better error messages help users understand what went wrong

## Files Modified

- `flowproc/visualize.py` - Added ProcessingError class
- `flowproc/parsing.py` - Improved CSV reading exception handling, added type validation
- `flowproc/data_io.py` - Added type validation, specific exception handling
- `flowproc/vectorized_aggregator.py` - Added type validation
- `flowproc/writer.py` - Improved file operation exception handling
- `flowproc/gui/async_processor.py` - More specific worker thread exception handling

## Example Usage

The improved exception handling provides clearer error messages:

```python
from flowproc.parsing import load_and_parse_df
from flowproc.visualize import ProcessingError

try:
    df, sid_col = load_and_parse_df(csv_path)
except ProcessingError as e:
    print(f"Processing failed: {e}")
    # Handle processing-specific errors
except FileNotFoundError as e:
    print(f"File not found: {e}")
    # Handle file system errors  
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle unexpected errors
``` 