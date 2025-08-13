from dataclasses import dataclass
from typing import Optional, List

from flowproc.domain.visualization.plot_config import DEFAULT_WIDTH, DEFAULT_HEIGHT


@dataclass
class VisualizationOptions:
    """Container for visualization options used by the visualization dialog.

    This data structure intentionally lives outside the dialog for better
    separation of concerns and reusability.
    """
    plot_type: str = "bar"
    y_axis: Optional[str] = None
    time_course_mode: bool = False
    theme: str = "plotly"
    width: int = DEFAULT_WIDTH + 300
    height: int = DEFAULT_HEIGHT + 100
    show_individual_points: bool = True
    error_bars: bool = True
    interactive: bool = True
    # Filter options
    selected_tissues: Optional[List[str]] = None
    selected_times: Optional[List[float]] = None
    selected_population: Optional[str] = None


