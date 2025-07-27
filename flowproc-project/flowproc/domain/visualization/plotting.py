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
import re

logger = logging.getLogger(__name__)

PLOT_STYLE = {
    "bargap": 0.2,
    "bargroupgap": 0.3,
    "font_family": "Arial",
    "font_size": 11,  # User requirement: label font should be 11pt
    "title_font_size": 14,  # User requirement: graph title should be 14pt bold
    "xaxis_tickfont_size": 11,  # User requirement: label font should be 11pt
    "yaxis_tickfont_size": 11,  # User requirement: label font should be 11pt
    "xaxis_linewidth": 0.75,
    "yaxis_linewidth": 0.75,
    "xaxis_tickwidth": 0.5,
    "yaxis_tickwidth": 0.5,
    "xaxis_ticklen": 4,
    "yaxis_ticklen": 4,
    "yaxis_range": [0, None],
    "legend": {
        "title": None,
        "font_size": 11,  # User requirement: label font should be 11pt
        "orientation": "v",
        "yanchor": "middle",
        "xanchor": "left",
        "x": 1.01,  # Slightly closer to graph
        "y": 0.5,   # Center vertically
        "borderwidth": 0,
        "itemwidth": 30,
        "itemsizing": "constant",
        "tracegroupgap": 6,  # Reduced spacing
        "entrywidth": 30,
        "entrywidthmode": "pixels",
        "itemclick": "toggle",
        "itemdoubleclick": "toggleothers",
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

def calculate_layout_for_long_labels(labels: list[str], legend_items: int = 0, title: str = "", legend_labels: list[str] = None, base_width: int = 600, base_height: int = 300) -> dict:
    """
    Calculate optimal layout settings to prevent label overlap while maintaining aspect ratio.
    
    Args:
        labels: List of x-axis labels
        legend_items: Number of legend items (for horizontal legend)
        title: Chart title to consider for spacing
        legend_labels: List of legend labels to consider for width calculations
        base_width: Base width of the graph to calculate dynamic width
        base_height: Base height of the graph to calculate dynamic height
        
    Returns:
        Dictionary with layout adjustments
    """
    if not labels:
        return {}
    
    # Calculate the maximum label length
    max_label_length = max(len(str(label)) for label in labels)
    
    # Calculate legend label lengths if provided
    max_legend_label_length = 0
    if legend_labels:
        max_legend_label_length = max(len(str(label)) for label in legend_labels)
    
    # Calculate title height (rough estimate)
    title_height = len(title) * 0.8 if title else 0
    
    # Base settings with dynamic calculations
    layout_adjustments = {}
    
    # Calculate scaling factor based on label length to maintain aspect ratio
    # Use a reference length (e.g., 10 characters) as the baseline for integer-like labels
    reference_label_length = 10
    scaling_factor = max(1.0, max_label_length / reference_label_length)
    
    # Apply maximum scaling limits for 15-inch screen comfort
    # Target: plots should fit comfortably within ~1/4 of a 15-inch screen
    # 15-inch screen at 96 DPI ≈ 1440x900 pixels, so 1/4 ≈ 1200x800 max
    max_width = 1200
    max_height = 800
    
    # Calculate maximum allowed scaling factor based on screen constraints
    max_width_scaling = max_width / base_width
    max_height_scaling = max_height / base_height
    max_allowed_scaling = min(max_width_scaling, max_height_scaling)
    
    # Apply the scaling limit
    scaling_factor = min(scaling_factor, max_allowed_scaling)
    
    # Apply scaling factor to maintain aspect ratio
    # Scale both width and height proportionally
    dynamic_width = int(base_width * scaling_factor)
    dynamic_height = int(base_height * scaling_factor)
    
    # Calculate dynamic spacing based on content
    # Base spacing for labels
    label_spacing = max(20, max_label_length * 2.5)  # Minimum 20px, scales with label length
    
    # Calculate legend height (rough estimate)
    legend_height = 30  # Base legend height
    if legend_items > 4:
        legend_height += (legend_items - 4) * 5  # Add space for more items
    
    # Calculate total bottom space needed (reduced since legend is now on the right)
    total_bottom_space = label_spacing + 20  # 20px buffer, no legend space needed
    
    # Dynamic legend positioning for right-side legend
    # Calculate legend width needed
    legend_width = 0
    if max_legend_label_length > 0:
        # Estimate space needed for legend labels
        # Each legend item needs space for color box + label + spacing
        legend_item_width = max_legend_label_length * 8  # 8px per character for vertical legend
        legend_width = legend_item_width + 40  # Add padding
    
    # Adjust legend position based on label length and legend items
    if max_label_length > 30:
        tick_angle = -45
    elif max_label_length > 20:
        tick_angle = -30
    elif max_label_length > 15:
        tick_angle = -15
    else:
        tick_angle = 0
    
    # Calculate optimal item width for vertical legend
    item_width = 30  # Fixed width for color boxes in vertical legend (minimum allowed)
    
    # Calculate right margin for legend space
    right_margin = 30  # Slightly more margin for better spacing
    
    # Ensure minimum spacing from title
    title_standoff = max(10, title_height + 5)
    
    layout_adjustments.update({
        "width": dynamic_width,
        "height": dynamic_height,
        "margin": {"l": 50, "r": right_margin, "t": 50, "b": int(total_bottom_space)},
        "legend": {
            "font_size": 11,  # User requirement: label font should be 11pt
            "orientation": "v",  # Vertical orientation
            "yanchor": "middle",
            "xanchor": "left",
            "x": 1.01,  # Slightly closer to graph (was 1.02)
            "y": 0.5,   # Center vertically
            "borderwidth": 0,
            "itemwidth": item_width,
            "itemsizing": "constant",
            "tracegroupgap": 6,  # Reduced spacing for tighter layout
            "entrywidth": item_width,  # Control entry width
            "entrywidthmode": "pixels",  # Use pixel mode for precise control
            "itemclick": "toggle",
            "itemdoubleclick": "toggleothers",
        },
        "xaxis_title_standoff": title_standoff,
        "xaxis_tickangle": tick_angle,
    })
    
    return layout_adjustments

def apply_plot_style(fig: go.Figure, x_title: str, y_title: str, width: int, height: int) -> None:
    """Apply consistent styling to a Plotly figure."""
    # Apply base styling (without theme)
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        width=width,
        height=height,
        **PLOT_STYLE
    )
    
    # Apply bold styling for axis labels (user requirement: axis labels should be bold 12pt font)
    fig.update_xaxes(title_font=dict(size=12, color='black'))
    fig.update_yaxes(title_font=dict(size=12, color='black'))
    
    # Apply bold styling for title (user requirement: graph title should be centered above graph, 14pt bold)
    current_title = fig.layout.title.text if hasattr(fig.layout, 'title') and fig.layout.title else ""
    fig.update_layout(
        title=dict(
            text=current_title,
            font=dict(size=14, color='black'),
            x=0.5,  # Center the title
            xanchor='center'
        )
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
    
    # Create a copy of the dataframe to avoid modifying the original
    plot_df = agg_df.copy()
    
    # Extract integer labels from Group_Label for display
    def extract_group_number(label):
        """Extract the integer part from group labels like 'Group 1' -> '1'"""
        if pd.isna(label):
            return label
        label_str = str(label)
        # Try to extract number from "Group X" format
        if 'Group' in label_str:
            match = re.search(r'Group\s*(\d+)', label_str, re.IGNORECASE)
            if match:
                return match.group(1)
        # If no "Group" prefix, try to extract any number
        numbers = re.findall(r'\d+', label_str)
        if numbers:
            return numbers[0]
        # Fallback to original label
        return label_str
    
    # Create integer labels for x-axis display
    plot_df['Group_Number'] = plot_df[x_axis].apply(extract_group_number)
    
    # Convert to integers for proper numerical sorting, then back to strings for display
    def convert_to_int_for_sorting(label):
        """Convert label to integer for sorting, fallback to string if not numeric"""
        if pd.isna(label):
            return 0  # Put NaN values at the beginning
        try:
            return int(label)
        except (ValueError, TypeError):
            # If it's not a number, use a large number to put it at the end
            return 999999
    
    # Add a sorting column
    plot_df['Sort_Order'] = plot_df['Group_Number'].apply(convert_to_int_for_sorting)
    
    # Sort the dataframe by the numerical order
    plot_df = plot_df.sort_values('Sort_Order')
    
    # Use Group_Number for x-axis if we have tissue information
    if 'Tissue' in plot_df.columns and plot_df['Tissue'].nunique() > 1:
        # Filter out UNK tissues when creating labels
        plot_df['X_Label'] = plot_df.apply(
            lambda row: f"{row['Group_Number']} ({row['Tissue']})" if row['Tissue'] != 'UNK' else str(row['Group_Number']), 
            axis=1
        )
        x_axis = 'X_Label'
    else:
        x_axis = 'Group_Number'

    fig = px.bar(
        plot_df,
        x=x_axis,
        y='Mean',
        error_y='Std',
        color=color,
        title=metric_name,
        barmode='group',
        color_discrete_sequence=px.colors.qualitative.Dark24
    )
    
    # Set error bar styling directly after creation
    fig.update_traces(
        error_y=dict(thickness=0.5, width=0.75),  # Endcaps 50% wider than main line
        selector=dict(type='bar')
    )
    
    # Calculate optimal layout based on label lengths
    labels = plot_df[x_axis].unique().tolist()
    legend_items = len(plot_df[color].unique()) if color in plot_df.columns else 0
    legend_labels = plot_df[color].unique().tolist() if color in plot_df.columns else []
    layout_adjustments = calculate_layout_for_long_labels(labels, legend_items, metric_name, legend_labels, width, height)
    
    # Apply base styling with dynamic width and height
    dynamic_width = layout_adjustments.get("width", width)
    dynamic_height = layout_adjustments.get("height", height)
    apply_plot_style(fig, 'Group', metric_name, dynamic_width, dynamic_height)
    
    # Apply dynamic layout adjustments
    if layout_adjustments:
        fig.update_layout(
            margin=layout_adjustments["margin"],
            legend=layout_adjustments["legend"]
        )
        fig.update_xaxes(
            title_standoff=layout_adjustments["xaxis_title_standoff"],
            tickangle=layout_adjustments["xaxis_tickangle"]
        )
    else:
        # Fallback to improved default settings with right-side legend
        fig.update_layout(
            legend=dict(
                font_size=11,  # User requirement: label font should be 11pt
                orientation="v",
                yanchor="middle",
                xanchor="left",
                x=1.01,  # Slightly closer to graph
                y=0.5,
                borderwidth=0,
                itemwidth=30,
                itemsizing="constant",
                tracegroupgap=6,  # Reduced spacing
                entrywidth=30,
                entrywidthmode="pixels",
                itemclick="toggle",
                itemdoubleclick="toggleothers"
            ),
            margin=dict(b=50, r=30),  # Slightly more right margin
            width=width + 150  # Reduced extra width for legend space
        )
        fig.update_xaxes(title_standoff=15)
    
    # Apply final styling after all other updates
    fig.update_traces(
        marker_line_width=0.5,  # ~1/2 pt black border around each bar
        marker_line_color='black',
        width=0.2,
        error_y=dict(thickness=0.5, width=0.75),  # Endcaps 50% wider than main line
        selector=dict(type='bar')
    )
    
    # Update legend to match bar border styling
    fig.update_layout(
        legend=dict(
            bordercolor='black',
            borderwidth=0.5,  # Match the bar border width
            bgcolor='rgba(255,255,255,0.8)',  # Semi-transparent white background
        )
    )
    
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
        vertical_spacing=0.02,  # Reduced spacing to prevent vertical compression
        subplot_titles=[f"{metric_name} - {subpop}" for subpop in unique_subpops]
    )

    tissues_detected: bool = 'Tissue' in agg_df.columns and agg_df['Tissue'].nunique() > 1
    
    # Extract integer labels for legend display and sorting
    def extract_group_number(label):
        """Extract the integer part from group labels like 'Group 1' -> '1'"""
        if pd.isna(label):
            return label
        label_str = str(label)
        # Try to extract number from "Group X" format
        if 'Group' in label_str:
            match = re.search(r'Group\s*(\d+)', label_str, re.IGNORECASE)
            if match:
                return match.group(1)
        # If no "Group" prefix, try to extract any number
        numbers = re.findall(r'\d+', label_str)
        if numbers:
            return numbers[0]
        # Fallback to original label
        return label_str
    
    # Get unique groups and sort them numerically
    all_groups = agg_df['Group_Label'].unique()
    
    # Create a list of tuples (original_group, extracted_number) for sorting
    group_number_pairs = []
    for group in all_groups:
        group_number = extract_group_number(group)
        try:
            # Try to convert to int for numerical sorting
            sort_key = int(group_number)
        except (ValueError, TypeError):
            # If not a number, use a large number to put it at the end
            sort_key = 999999
        group_number_pairs.append((group, group_number, sort_key))
    
    # Sort by the numerical key
    group_number_pairs.sort(key=lambda x: x[2])
    
    # Extract the sorted groups and their display numbers
    unique_groups = [pair[0] for pair in group_number_pairs]
    group_display_numbers = [pair[1] for pair in group_number_pairs]
    
    color_sequence = px.colors.qualitative.Dark24
    group_color_map: dict[str, str] = {group: color_sequence[i % len(color_sequence)] for i, group in enumerate(unique_groups)}

    for row, subpop in enumerate(unique_subpops, start=1):
        sub_df: pd.DataFrame = agg_df[agg_df['Subpopulation'] == subpop]
        for i, group in enumerate(unique_groups):
            group_df: pd.DataFrame = sub_df[sub_df['Group_Label'] == group].sort_values('Time')
            if group_df.empty:
                continue
            tissue: str = group_df['Tissue'].iloc[0] if tissues_detected and not group_df.empty else ''
            # Use integer label for display
            group_number = group_display_numbers[i]
            # Don't include UNK tissue in the name
            name: str = f"{group_number} ({tissue})" if tissue and tissue != 'UNK' else str(group_number)
            fig.add_trace(
                go.Scatter(
                    x=group_df['Time'],
                    y=group_df['Mean'],
                    error_y=dict(type='data', array=group_df['Std'], visible=True, thickness=0.5, width=0.75),  # Endcaps 50% wider than main line
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
    apply_plot_style(fig, 'Time', metric_name, width, updated_height)
    
    # Add legend improvements for line plots
    fig.update_layout(
        legend=dict(
            bordercolor='black',
            borderwidth=0.5,  # Match the line border width
            bgcolor='rgba(255,255,255,0.8)',  # Semi-transparent white background
        )
    )
    
    # Set title and ticks for each subplot to ensure visibility
    for row in range(1, num_subpops + 1):
        fig.update_xaxes(title_text='Time', title_standoff=0, showticklabels=True, autorange=True, row=row, col=1)
    return fig