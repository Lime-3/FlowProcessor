# flowproc/config.py
from typing import List

class Config:
    """Configuration class for FlowProcessor."""
    def __init__(self):
        self.output_dir = "output"
        self.default_csv_path = ""

# Configuration variables
USER_GROUPS: List[int] = [1, 2]  # Default groups
USER_REPLICATES: List[int] = [1, 2, 3]  # Default replicates
AUTO_PARSE_GROUPS = True
USER_GROUP_LABELS: List[str] = ["Group A", "Group B"]  # Default labels

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

# Ensure these are available at module level
__all__ = ['Config', 'USER_GROUPS', 'USER_REPLICATES', 'AUTO_PARSE_GROUPS', 'USER_GROUP_LABELS']