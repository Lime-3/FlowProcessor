import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Union
import sys
import os
import hashlib
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from flowproc.logging_config import setup_logging
from flowproc.config import USER_GROUP_LABELS
from flowproc.parsing import load_and_parse_df, extract_tissue
from flowproc.transform import map_replicates
from flowproc.writer import KEYWORDS
from flowproc.plotting import create_bar_plot, create_line_plot, apply_plot_style, PLOT_STYLE
from flowproc.vectorized_aggregator import VectorizedAggregator, AggregationConfig

logger = logging.getLogger(__name__)


def process_data(
    df: pd.DataFrame,
    sid_col: str,
    metric: Optional[str],
    time_course_mode: bool,
    user_replicates: Optional[List[int]],
    auto_parse_groups: bool,
    user_group_labels: Optional[List[str]]
) -> List[List[pd.DataFrame]]:
    """
    Process DataFrame for plotting using vectorized operations.
    
    Args:
        df: Input DataFrame
        sid_col: Sample ID column name
        metric: Specific metric to process (None for all)
        time_course_mode: Whether to use time-course mode
        user_replicates: User-defined replicates
        auto_parse_groups: Whether to auto-parse groups
        user_group_labels: User-defined group labels
        
    Returns:
        List of lists of DataFrames (per metric, per tissue)
    """
    if df.empty:
        logger.error("DataFrame is empty")
        raise ValueError("No data in CSV")
    
    # Derive user groups if not auto-parsing
    user_groups = None
    if not auto_parse_groups:
        user_groups = sorted(df["Group"].dropna().unique().astype(int))
    
    # Map replicates
    df, replicate_count = map_replicates(
        df, 
        auto_parse=auto_parse_groups, 
        user_replicates=user_replicates,
        user_groups=user_groups
    )
    
    if replicate_count == 0:
        logger.error("No replicates detected")
        raise ValueError("No replicates found")
    
    # Initialize vectorized aggregator
    aggregator = VectorizedAggregator(df, sid_col)
    
    # Determine metrics to process
    if metric:
        metrics = [m for m in KEYWORDS.keys() if m.lower() == metric.lower()]
        if not metrics:
            logger.error(f"Invalid metric '{metric}'; available: {list(KEYWORDS.keys())}")
            raise ValueError(f"Invalid metric '{metric}'")
    else:
        metrics = list(KEYWORDS.keys())
    
    # Get configuration
    groups = sorted(df["Group"].dropna().unique().astype(int))
    times = sorted(t for t in df["Time"].unique() if pd.notna(t)) if "Time" in df.columns and df["Time"].notna().any() else [None]
    tissues_detected = df[sid_col].apply(extract_tissue).nunique() > 1
    
    # Create group labels mapping
    if user_group_labels and len(user_group_labels) >= len(groups):
        group_map = {groups[i]: user_group_labels[i] for i in range(len(groups))}
    elif USER_GROUP_LABELS and len(USER_GROUP_LABELS) >= len(groups):
        group_map = {groups[i]: USER_GROUP_LABELS[i] for i in range(len(groups))}
    else:
        group_map = {g: f"Group {g}" for g in groups}
    
    # Create aggregation config
    config = AggregationConfig(
        groups=groups,
        times=times,
        tissues_detected=tissues_detected,
        group_map=group_map,
        sid_col=sid_col,
        time_course_mode=time_course_mode
    )
    
    # Aggregate data using vectorized operations
    aggregated_lists = []
    
    for metric_name in metrics:
        key_substring = KEYWORDS.get(metric_name, metric_name.lower())
        
        # Find matching columns
        raw_cols = [
            c for c in df.columns 
            if key_substring in c.lower() 
            and c not in {sid_col, "Well", "Group", "Animal", "Time", "Replicate", "Tissue"}
            and not df[c].isna().all()
        ]
        
        if not raw_cols:
            logger.info(f"No data for '{metric_name}'")
            continue
        
        # Use vectorized aggregation
        agg_dfs = aggregator.aggregate_metric(metric_name, raw_cols, config)
        
        if agg_dfs:
            aggregated_lists.append(agg_dfs)
    
    return aggregated_lists


def visualize_data(
    csv_path: str,
    output_html: Union[str, Path],
    metric: Optional[str] = None,
    width: int = 800,
    height: int = 600,
    theme: str = "plotly_dark",
    time_course_mode: bool = False,
    user_replicates: Optional[List[int]] = None,
    auto_parse_groups: bool = True,
    user_group_labels: Optional[List[str]] = None
) -> go.Figure:
    """
    Generate interactive plots using vectorized data processing.
    
    Args:
        csv_path: Path to input CSV file
        output_html: Path for output HTML file
        metric: Specific metric to visualize (None for all)
        width: Plot width in pixels
        height: Plot height in pixels
        theme: Plotly theme name
        time_course_mode: Whether to use time-course visualization
        user_replicates: User-defined replicates
        auto_parse_groups: Whether to auto-parse groups
        user_group_labels: User-defined group labels
        
    Returns:
        Plotly Figure object
    """
    try:
        setup_logging(filemode='a')
        logger.debug(f"Starting visualization for {csv_path}, metric={metric}")
        print(f"Starting visualization for {csv_path} with metric={metric}", file=sys.stderr)
        
        # Convert paths
        csv_path = Path(csv_path)
        output_html = Path(output_html) if isinstance(output_html, str) else output_html
        
        # Validate inputs
        if not csv_path.exists():
            raise ValueError(f"CSV file does not exist: {csv_path}")
        if not output_html.parent.exists():
            output_html.parent.mkdir(parents=True, exist_ok=True)
            
        # Load and parse data
        df, sid_col = load_and_parse_df(csv_path)
        
        # Check for time data
        times = sorted(t for t in df["Time"].unique() if pd.notna(t)) if "Time" in df.columns and df["Time"].notna().any() else [None]
        is_timecourse = len(times) > 1 or (len(times) == 1 and times[0] is not None)
        
        if time_course_mode and not is_timecourse:
            logger.warning("No time data for time-course; falling back to standard mode")
            time_course_mode = False
            
        # Process data using vectorized operations
        aggregated_lists = process_data(
            df, sid_col, metric, time_course_mode, 
            user_replicates, auto_parse_groups, user_group_labels
        )
        
        # Create figure - initialize once before loop for time course mode
        fig = None
        
        for agg_list in aggregated_lists:
            if not agg_list:
                continue
                
            metric_name = agg_list[0]["Metric"].iloc[0]
            
            # Combine tissue data if multiple
            combined_agg = pd.concat(agg_list) if len(agg_list) > 1 else agg_list[0]
            tissues_detected = combined_agg['Tissue'].nunique() > 1 if 'Tissue' in combined_agg else False
            
            if time_course_mode:
                # Time course visualization
                unique_subpops = sorted(combined_agg['Subpopulation'].unique())
                unique_tissues = sorted(combined_agg['Tissue'].unique())
                num_rows = len(unique_subpops) * len(unique_tissues)
                
                # Create subplots (only create if not already created)
                if fig is None:
                    fig = make_subplots(
                    rows=num_rows, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.05,
                    subplot_titles=[
                        f"{metric_name} - {subpop}{f' ({tissue})' if tissue != 'Unknown_tissue' else ''}" 
                        for tissue in unique_tissues 
                        for subpop in unique_subpops
                    ]
                )
                
                # Color mapping
                color_sequence = px.colors.qualitative.Dark24
                group_color_map = {
                    group: color_sequence[i % len(color_sequence)] 
                    for i, group in enumerate(sorted(combined_agg['Group_Label'].unique()))
                }
                
                # Add traces
                row_idx = 1
                for tissue in unique_tissues:
                    for subpop in unique_subpops:
                        sub_df = combined_agg[
                            (combined_agg['Subpopulation'] == subpop) & 
                            (combined_agg['Tissue'] == tissue)
                        ]
                        
                        for group in sorted(sub_df['Group_Label'].unique()):
                            group_df = sub_df[sub_df['Group_Label'] == group].sort_values('Time')
                            
                            if not group_df.empty:
                                fig.add_trace(
                                    go.Scatter(
                                        x=group_df['Time'],
                                        y=group_df['Mean'],
                                        error_y=dict(
                                            type='data', 
                                            array=group_df['Std'], 
                                            visible=True
                                        ),
                                        mode='lines+markers',
                                        name=f"{group}{f' ({tissue})' if tissue != 'Unknown_tissue' else ''}",
                                        legendgroup=group,
                                        line=dict(color=group_color_map[group]),
                                        showlegend=(row_idx == 1)
                                    ),
                                    row=row_idx, col=1
                                )
                        row_idx += 1
                
                # Update layout
                updated_height = height * num_rows
                apply_plot_style(fig, 'Time', metric_name, theme, width, updated_height)
                
                # Update x-axes
                for row in range(1, num_rows + 1):
                    fig.update_xaxes(
                        title_text='Time', 
                        title_standoff=0, 
                        showticklabels=True, 
                        autorange=True, 
                        row=row, col=1
                    )
            else:
                # Bar plot visualization (create new figure for standard mode)
                fig = px.bar(
                    combined_agg,
                    x='Group_Label',
                    y='Mean',
                    error_y='Std',
                    color='Subpopulation',
                    facet_col='Tissue' if tissues_detected else None,
                    title=metric_name,
                    barmode='group',
                    color_discrete_sequence=px.colors.qualitative.Dark24
                )
                
                # Apply styling
                apply_plot_style(fig, 'Group_Label', metric_name, theme, width, height)
                fig.update_layout(
                    legend=dict(y=-0.2), 
                    margin=dict(b=80)
                )
                fig.update_xaxes(title_standoff=10)
                fig.update_traces(
                    marker_line_width=0.5, 
                    marker_line_color='black', 
                    error_y=dict(thickness=0.75, width=5), 
                    width=0.2
                )
        
        # Create empty figure if none was created
        if fig is None:
            fig = go.Figure()
            fig.add_annotation(
                text="No data to visualize",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
        
        # Save HTML
        fig.write_html(str(output_html), include_plotlyjs=True)
        
        if output_html.exists():
            size = output_html.stat().st_size
            md5 = hashlib.md5(output_html.read_bytes()).hexdigest()
            logger.info(f"Saved '{output_html}' ({size} bytes, md5 {md5})")
            
        return fig
        
    except (FileNotFoundError, ValueError, pd.errors.ParserError, OSError) as e:
        logger.error(f"Visualization failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise RuntimeError(f"Visualization failed: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate plots from CSV")
    parser.add_argument("--csv", required=True, help="Input CSV path")
    parser.add_argument("--output-html", required=True, help="Output HTML path")
    parser.add_argument("--metric", default=None, help="Metric to visualize")
    parser.add_argument("--width", type=int, default=800, help="Plot width")
    parser.add_argument("--height", type=int, default=600, help="Plot height")
    parser.add_argument("--theme", default="plotly_dark", help="Plotly theme")
    parser.add_argument("--time-course", action="store_true", help="Time-course mode")
    
    args = parser.parse_args()
    
    visualize_data(
        csv_path=args.csv,
        output_html=args.output_html,
        metric=args.metric,
        width=args.width,
        height=args.height,
        theme=args.theme,
        time_course_mode=args.time_course
    )