# flowproc/config.py
from typing import List

USER_GROUPS: List[int] = []
USER_REPLICATES: List[int] = []
AUTO_PARSE_GROUPS = True
USER_GROUP_LABELS: List[str] = []

def parse_range_or_list(input_str: str) -> List[int]:
    """Parse a string of numbers or ranges (e.g., '1,2,3' or '1-3') into a list of integers."""
    try:
        result = []
        parts = input_str.replace(' ', '').split(',')
        for part in parts:
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start <= end:
                    result.extend(range(start, end + 1))
                else:
                    raise ValueError("Invalid range: start must be less than or equal to end")
            else:
                result.append(int(part))
        return sorted(set(result))  # Remove duplicates and sort
    except ValueError as e:
        raise ValueError(f"Invalid input: {e}")