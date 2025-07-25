"""
Pure Plotly building blocks. Keeps all plotting concerns out of GUI and I/O.
"""
from __future__ import annotations
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Literal
import logging

logger = logging.getLogger(__name__)

PLOT_STYLE = {
    "bargap": 0.2,
    "bargroupgap": 0.3,
    "font_family": "Arial",
    "font_size": 10,
    "title_font_size": 12,
    "xaxis_tickfont_size": 8,
    "yaxis_tickfont_size": 8,
    "xaxis_linewidth": 0.75,
    "yaxis_linewidth": 0.75,
    "xaxis_tickwidth": 0.5,
    "yaxis_tickwidth": 0.5,
    "xaxis_ticklen": 4,
    "yaxis_ticklen": 4,
    "yaxis_range": [0, None],
    "legend": {
        "title": None,
        "font_size": 8,
        "orientation": "h",
        "yanchor": "top",
        "y": -0.025,  # User's change: Moved closer to last graph
        "xanchor": "center",
        "x": 0.5,
        "borderwidth": 0,
        "itemwidth": 150,
        "itemsizing": "constant",
    },
    "showlegend": True,
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "#0F0F0F",
    "xaxis_showgrid": True,
    "yaxis_showgrid": True,
    "xaxis_gridwidth": 0.5,
    "yaxis_gridwidth": 0.5,
    "margin": {"l": 50, "r": 50, "t": 50, "b": 50},  # User's change: Reduced bottom margin
    "modebar": {"orientation": "h"},
}

def apply_plot_style(fig: go.Figure, x_title: str, y_title: str, theme: str, width: int, height: int) -> None:
    """Apply consistent styling to a Plotly figure."""
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        template=theme,
        width=width,
        height=height,
        **PLOT_STYLE
    )

def create_bar_plot(
    agg_df: pd.DataFrame,
    metric_name: str,
    width: int,
    height: int,
    theme: str
) -> go.Figure:
    """Create a bar plot from aggregated data, showing multiple subpopulations."""
    x_axis = 'Group_Label'
    color = 'Subpopulation'
    if 'Tissue' in agg_df.columns and agg_df['Tissue'].nunique() > 1:
        agg_df['X_Label'] = agg_df[x_axis].astype(str) + ' (' + agg_df['Tissue'] + ')'
        x_axis = 'X_Label'

    fig = px.bar(
        agg_df,
        x=x_axis,
        y='Mean',
        error_y='Std',
        color=color,
        title=metric_name,
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    apply_plot_style(fig, x_axis, metric_name, theme, width, height)
    fig.update_layout(legend=dict(y=-0.2))  # Lower legend for bar plots to avoid overlap
    fig.update_layout(margin=dict(b=80))  # Increased bottom margin for bar plots
    fig.update_xaxes(title_standoff=10)  # Slight standoff for bar plots
    fig.update_traces(marker_line_width=0.5, marker_line_color='black', error_y=dict(thickness=0.75, width=5), width=0.2)
    return fig

def create_line_plot(
    agg_df: pd.DataFrame,
    metric_name: str,
    width: int,
    height: int,
    theme: str
) -> go.Figure:
    """Create a line plot for time-course data, faceted by subpopulation with consistent group colors."""
    unique_subpops: list[str] = sorted(agg_df['Subpopulation'].unique())
    num_subpops: int = len(unique_subpops)
    fig = make_subplots(
        rows=num_subpops,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,  # User's change: Balanced spacing for larger heights
        subplot_titles=[f"{metric_name} - {subpop}" for subpop in unique_subpops]
    )

    tissues_detected: bool = 'Tissue' in agg_df.columns and agg_df['Tissue'].nunique() > 1
    unique_groups: list[str] = sorted(agg_df['Group_Label'].unique())
    color_sequence = px.colors.qualitative.Dark24
    group_color_map: dict[str, str] = {group: color_sequence[i % len(color_sequence)] for i, group in enumerate(unique_groups)}

    for row, subpop in enumerate(unique_subpops, start=1):
        sub_df: pd.DataFrame = agg_df[agg_df['Subpopulation'] == subpop]
        for group in unique_groups:
            group_df: pd.DataFrame = sub_df[sub_df['Group_Label'] == group].sort_values('Time')
            if group_df.empty:
                continue
            tissue: str = group_df['Tissue'].iloc[0] if tissues_detected and not group_df.empty else ''
            name: str = f"{group} ({tissue})" if tissue else group
            fig.add_trace(
                go.Scatter(
                    x=group_df['Time'],
                    y=group_df['Mean'],
                    error_y=dict(type='data', array=group_df['Std'], visible=True),
                    mode='lines+markers',
                    name=name,
                    legendgroup=group,
                    line=dict(color=group_color_map[group]),
                    showlegend=(row == 1)
                ),
                row=row,
                col=1
            )

    updated_height: int = height * num_subpops  # Larger height for each graph
    fig.update_layout(
        title=metric_name,
        template=theme,
        height=updated_height
    )
    apply_plot_style(fig, 'Time', metric_name, theme, width, updated_height)
    # Set title and ticks for each subplot to ensure visibility
    for row in range(1, num_subpops + 1):
        fig.update_xaxes(title_text='Time', title_standoff=0, showticklabels=True, autorange=True, row=row, col=1)
    return fig