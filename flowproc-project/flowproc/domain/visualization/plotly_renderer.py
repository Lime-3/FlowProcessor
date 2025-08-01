"""
Plotly-specific rendering functionality for flow cytometry visualizations.
"""

from typing import Dict, Any, Optional, List
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class PlotlyRenderer:
    """Handles Plotly-specific rendering operations."""
    
    def __init__(self):
        """Initialize the renderer."""
        self.default_layout = {
            'template': 'plotly_white',
            'font': {'family': 'Arial, sans-serif', 'size': 12},
            'margin': {'l': 50, 'r': 50, 't': 50, 'b': 80},
            'showlegend': True,
            'legend': {
                'orientation': 'h', 
                'yanchor': 'top', 
                'y': -0.25, 
                'xanchor': 'center', 
                'x': 0.5,
                'itemwidth': 150,
                'tracegroupgap': 4,
                'entrywidth': 150,
                'entrywidthmode': 'pixels'
            }
        }
    
    def render_scatter(self, df: pd.DataFrame, x_col: str, y_col: str, 
                      color_col: Optional[str] = None, size_col: Optional[str] = None,
                      title: str = "", **kwargs) -> go.Figure:
        """Render a scatter plot."""
        fig = px.scatter(
            df, x=x_col, y=y_col, color=color_col, size=size_col,
            title=title, **kwargs
        )
        
        # Apply default layout
        fig.update_layout(**self.default_layout)
        
        return fig
    
    def render_bar(self, df: pd.DataFrame, x_col: str, y_col: str,
                  color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a bar plot."""
        fig = px.bar(
            df, x=x_col, y=y_col, color=color_col,
            title=title, **kwargs
        )
        
        # Calculate optimal layout based on label lengths
        labels = df[x_col].unique().tolist() if x_col in df.columns else []
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        legend_labels = df[color_col].unique().tolist() if color_col and color_col in df.columns else []
        
        # Import the layout calculation function
        from .plotting import calculate_layout_for_long_labels
        # Use consistent default dimensions
        default_width = 600
        default_height = 300
        layout_adjustments = calculate_layout_for_long_labels(labels, legend_items, title, legend_labels, default_width, default_height)
        
        # Apply default layout
        fig.update_layout(**self.default_layout)
        
        # Apply dynamic layout adjustments if needed
        if layout_adjustments:
            fig.update_layout(
                width=layout_adjustments.get("width", default_width),
                height=layout_adjustments.get("height", default_height),
                margin=layout_adjustments["margin"],
                legend=layout_adjustments["legend"]
            )
            fig.update_xaxes(
                title_standoff=layout_adjustments["xaxis_title_standoff"],
                tickangle=layout_adjustments["xaxis_tickangle"]
            )
        
        return fig
    
    def render_line(self, df: pd.DataFrame, x_col: str, y_col: str,
                   color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a line plot."""
        fig = px.line(
            df, x=x_col, y=y_col, color=color_col,
            title=title, **kwargs
        )
        
        # Calculate optimal legend positioning
        from .plotting import calculate_optimal_legend_position
        
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        legend_labels = df[color_col].unique().tolist() if color_col and color_col in df.columns else []
        
        legend_config = calculate_optimal_legend_position(
            legend_items=legend_items,
            legend_labels=legend_labels,
            plot_width=1000,
            plot_height=600
        )
        
        # Apply optimal legend positioning
        layout_updates = {
            "width": legend_config.get("width", 1000),
            "margin": legend_config.get("margin", {"l": 50, "r": 50, "t": 50, "b": 50}),
            "font": dict(family='Arial, sans-serif', size=12)
        }
        
        # Add legend configuration if present
        if "legend" in legend_config:
            layout_updates["legend"] = legend_config["legend"]
        
        fig.update_layout(**layout_updates)
        
        return fig
    
    def render_box(self, df: pd.DataFrame, x_col: str, y_col: str,
                  color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a box plot."""
        fig = px.box(
            df, x=x_col, y=y_col, color=color_col,
            title=title, **kwargs
        )
        
        # Apply default layout
        fig.update_layout(**self.default_layout)
        
        return fig
    
    def render_heatmap(self, df: pd.DataFrame, x_col: str, y_col: str, values_col: str,
                      title: str = "", **kwargs) -> go.Figure:
        """Render a heatmap."""
        # Pivot the data for heatmap
        pivot_df = df.pivot_table(
            values=values_col, 
            index=y_col, 
            columns=x_col, 
            aggfunc='mean'
        )
        
        fig = px.imshow(
            pivot_df,
            title=title,
            aspect='auto',
            **kwargs
        )
        
        # Apply default layout
        fig.update_layout(**self.default_layout)
        
        return fig
    
    def render_histogram(self, df: pd.DataFrame, x_col: str,
                        color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a histogram."""
        fig = px.histogram(
            df, x=x_col, color=color_col,
            title=title, **kwargs
        )
        
        # Apply default layout
        fig.update_layout(**self.default_layout)
        
        return fig
    
    def render_violin(self, df: pd.DataFrame, x_col: str, y_col: str,
                     color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a violin plot."""
        fig = px.violin(
            df, x=x_col, y=y_col, color=color_col,
            title=title, **kwargs
        )
        
        # Apply default layout
        fig.update_layout(**self.default_layout)
        
        return fig
    
    def render_3d_scatter(self, df: pd.DataFrame, x_col: str, y_col: str, z_col: str,
                         color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a 3D scatter plot."""
        fig = px.scatter_3d(
            df, x=x_col, y=y_col, z=z_col, color=color_col,
            title=title, **kwargs
        )
        
        # Apply default layout
        fig.update_layout(**self.default_layout)
        
        return fig
    
    def render_subplots(self, plots: List[go.Figure], rows: int, cols: int,
                       titles: Optional[List[str]] = None) -> go.Figure:
        """Render multiple plots as subplots."""
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=titles or [f'Plot {i+1}' for i in range(len(plots))]
        )
        
        # Add each plot to the subplot
        for i, plot in enumerate(plots):
            row = i // cols + 1
            col = i % cols + 1
            
            for trace in plot.data:
                fig.add_trace(trace, row=row, col=col)
        
        # Apply default layout
        fig.update_layout(**self.default_layout)
        
        return fig
    
    def apply_custom_layout(self, fig: go.Figure, layout: Dict[str, Any]) -> go.Figure:
        """Apply custom layout to a figure."""
        fig.update_layout(**layout)
        return fig
    
    def apply_custom_traces(self, fig: go.Figure, trace_updates: Dict[str, Any]) -> go.Figure:
        """Apply custom updates to traces."""
        fig.update_traces(**trace_updates)
        return fig
    
    def export_to_html(self, fig: go.Figure, filepath: str, 
                      include_plotlyjs: bool = True, full_html: bool = True) -> None:
        """Export figure to HTML file with CDN-loaded Plotly.js support."""
        # Use CDN by default for better performance
        plotlyjs_mode = 'cdn' if include_plotlyjs else False
        
        fig.write_html(
            filepath,
            include_plotlyjs=plotlyjs_mode,
            full_html=full_html,
            config=dict(
                editable=True,
                edits=dict(
                    axisTitleText=True,  # Editable axis labels
                    titleText=True,      # Editable chart title
                    legendText=True      # Editable legend items
                )
            )
        )
    
    def export_to_html_optimized(self, fig: go.Figure, filepath: str, 
                               optimization_level: str = 'balanced') -> None:
        """
        Export figure to HTML with size optimization.
        
        Args:
            fig: Plotly figure to export
            filepath: Output file path
            optimization_level: 'minimal', 'balanced', or 'full'
                - minimal: ~200KB, CDN loading, basic features
                - balanced: ~500KB, CDN loading, full features  
                - full: ~4MB, embedded library, offline compatible
        """
        if optimization_level == 'minimal':
            # For embedded viewer - use embedded Plotly for reliability
            include_plotlyjs = True  # Embed for reliability
            config = dict(
                displayModeBar=False,
                editable=False,
                responsive=True,
                displaylogo=False
            )
        elif optimization_level == 'balanced':
            # For external browser - balanced features
            include_plotlyjs = 'cdn'  # Use CDN
            config = dict(
                displayModeBar=True,
                editable=True,
                responsive=True,
                displaylogo=False
            )
        else:  # 'full'
            # For offline use - full features
            include_plotlyjs = True  # Embed for offline use
            config = dict(
                displayModeBar=True,
                editable=True,
                responsive=True,
                displaylogo=False
            )
        
        # Generate the HTML
        html_content = fig.to_html(
            include_plotlyjs=include_plotlyjs,
            full_html=True,
            config=config
        )
        
        # For embedded viewers, ensure CDN loads properly
        if optimization_level in ['minimal', 'balanced'] and include_plotlyjs == 'cdn':
            # Add explicit CDN link and fallback
            cdn_script = '''
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script>
    // Fallback if CDN fails
    if (typeof Plotly === 'undefined') {
        console.log('CDN failed, trying alternative CDN...');
        var script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js';
        document.head.appendChild(script);
    }
</script>
'''
            # Insert CDN script before the plotly div
            if '<div id="' in html_content:
                # Find the plotly div and insert CDN script before it
                div_start = html_content.find('<div id="')
                if div_start != -1:
                    html_content = html_content[:div_start] + cdn_script + html_content[div_start:]
        
        # For minimal mode, always add CDN script since include_plotlyjs=False
        if optimization_level == 'minimal':
            cdn_script = '''
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script>
    // Enhanced fallback for embedded viewers
    if (typeof Plotly === 'undefined') {
        console.log('Primary CDN failed, trying alternative CDN...');
        var script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js';
        script.onload = function() {
            console.log('Alternative CDN loaded successfully');
            // Re-render any existing plots
            if (typeof Plotly !== 'undefined' && document.getElementById('plotly-div')) {
                Plotly.newPlot('plotly-div', data, layout, config);
            }
        };
        script.onerror = function() {
            console.log('Alternative CDN also failed, trying third option...');
            var script2 = document.createElement('script');
            script2.src = 'https://unpkg.com/plotly.js@2.27.0/dist/plotly.min.js';
            document.head.appendChild(script2);
        };
        document.head.appendChild(script);
    }
</script>
'''
            # Insert CDN script in the head section
            if '<head>' in html_content:
                head_end = html_content.find('</head>')
                if head_end != -1:
                    html_content = html_content[:head_end] + cdn_script + html_content[head_end:]
        
        # Write the enhanced HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def export_to_image(self, fig: go.Figure, filepath: str, 
                       format: str = 'png', width: int = 800, height: int = 800) -> None:
        """Export figure to image file."""
        fig.write_image(
            filepath,
            format=format,
            width=width,
            height=height,
            scale=6  # 600 DPI equivalent
        )
    
    def export_to_pdf(self, fig: go.Figure, filepath: str, 
                     width: int = 1800, height: int = 600, scale: int = 1) -> None:
        """Export figure to PDF format with publication-ready settings."""
        # Export plot (excluding legend if desired by temp hiding)
        temp_fig = fig  # Copy to modify
        # Optional: Hide legend for export: temp_fig.update_layout(showlegend=False)
        temp_fig.write_image(filepath, width=width, height=height, scale=scale)  # 6x2 inches at 300 DPI
    
    def get_figure_info(self, fig: go.Figure) -> Dict[str, Any]:
        """Get information about a figure."""
        return {
            'data_count': len(fig.data),
            'layout_keys': list(fig.layout.keys()),
            'traces': [trace.type for trace in fig.data],
            'has_annotations': hasattr(fig.layout, 'annotations') and fig.layout.annotations,
            'has_shapes': hasattr(fig.layout, 'shapes') and fig.layout.shapes
        } 