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
            'showlegend': True
        }
    
    def render_scatter(self, df: pd.DataFrame, x_col: str, y_col: str, 
                      color_col: Optional[str] = None, size_col: Optional[str] = None,
                      title: str = "", **kwargs) -> go.Figure:
        """Render a scatter plot."""
        fig = px.scatter(
            df, x=x_col, y=y_col, color=color_col, size=size_col,
            title=title, **kwargs
        )
        
        # Calculate dimensions maintaining aspect ratio
        labels = df[x_col].unique().tolist() if x_col in df.columns else []
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        
        from .plot_utils import calculate_aspect_ratio_dimensions
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=labels,
            legend_items=legend_items,
            base_width=DEFAULT_WIDTH
        )
        
        # Apply dimensions maintaining aspect ratio
        fig.update_layout(
            width=dimensions['width'],
            height=dimensions['height'],
            **self.default_layout
        )
        
        # Apply centralized legend configuration
        from .legend_config import configure_legend
        from .plot_config import DEFAULT_HEIGHT
        fig = configure_legend(
            fig=fig,
            df=df,
            color_col=color_col,
            is_subplot=False,
            width=dimensions['width'],
            height=dimensions.get('height', DEFAULT_HEIGHT),
            legend_title=("Groups" if color_col else None),
            show_mean_sem_label=True
        )
        
        return fig
    
    def render_bar(self, df: pd.DataFrame, x_col: str, y_col: str,
                  color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a bar plot."""
        fig = px.bar(
            df, x=x_col, y=y_col, color=color_col,
            title=title, **kwargs
        )
        
        # Calculate dimensions maintaining 2:1 aspect ratio
        labels = df[x_col].unique().tolist() if x_col in df.columns else []
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        
        from .plot_utils import calculate_aspect_ratio_dimensions
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=labels,
            legend_items=legend_items,
            base_width=DEFAULT_WIDTH
        )
        
        # Apply dimensions maintaining aspect ratio
        fig.update_layout(
            width=dimensions['width'],
            height=dimensions['height'],
            **self.default_layout
        )
        
        # Apply centralized legend configuration
        from .legend_config import configure_legend
        from .plot_config import DEFAULT_HEIGHT
        fig = configure_legend(
            fig=fig,
            df=df,
            color_col=color_col,
            is_subplot=False,
            width=dimensions['width'],
            height=dimensions.get('height', DEFAULT_HEIGHT),
            legend_title=("Groups" if color_col else None),
            show_mean_sem_label=True
        )
        
        return fig
    
    def render_line(self, df: pd.DataFrame, x_col: str, y_col: str,
                   color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a line plot."""
        fig = px.line(
            df, x=x_col, y=y_col, color=color_col,
            title=title, **kwargs
        )
        
        # Calculate dimensions maintaining 2:1 aspect ratio
        labels = df[x_col].unique().tolist() if x_col in df.columns else []
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        
        from .plot_utils import calculate_aspect_ratio_dimensions
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=labels,
            legend_items=legend_items,
            base_width=DEFAULT_WIDTH
        )
        
        # Apply dimensions maintaining aspect ratio
        fig.update_layout(
            width=dimensions['width'],
            height=dimensions['height'],
            **self.default_layout
        )
        
        # Apply centralized legend configuration
        from .legend_config import configure_legend
        from .plot_config import DEFAULT_HEIGHT
        fig = configure_legend(
            fig=fig,
            df=df,
            color_col=color_col,
            is_subplot=False,
            width=dimensions['width'],
            height=dimensions.get('height', DEFAULT_HEIGHT),
            legend_title=("Groups" if color_col else None),
            show_mean_sem_label=True
        )
        
        return fig
    
    def render_box(self, df: pd.DataFrame, x_col: str, y_col: str,
                  color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a box plot."""
        fig = px.box(
            df, x=x_col, y=y_col, color=color_col,
            title=title, **kwargs
        )
        
        # Calculate dimensions maintaining 2:1 aspect ratio
        labels = df[x_col].unique().tolist() if x_col in df.columns else []
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        
        from .plot_utils import calculate_aspect_ratio_dimensions
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=labels,
            legend_items=legend_items,
            base_width=DEFAULT_WIDTH
        )
        
        # Apply dimensions maintaining aspect ratio
        fig.update_layout(
            width=dimensions['width'],
            height=dimensions['height'],
            **self.default_layout
        )
        
        # Apply centralized legend configuration
        from .legend_config import configure_legend
        from .plot_config import DEFAULT_HEIGHT
        fig = configure_legend(
            fig=fig,
            df=df,
            color_col=color_col,
            is_subplot=False,
            width=dimensions['width'],
            height=dimensions.get('height', DEFAULT_HEIGHT),
            legend_title=("Groups" if color_col else None),
            show_mean_sem_label=True
        )
        
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
        
        # Calculate dimensions maintaining 2:1 aspect ratio
        x_labels = pivot_df.columns.tolist()
        y_labels = pivot_df.index.tolist()
        labels = x_labels + y_labels
        
        from .plot_utils import calculate_aspect_ratio_dimensions
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=labels,
            legend_items=0,  # Heatmaps don't have legends
            base_width=DEFAULT_WIDTH
        )
        
        # Apply dimensions maintaining aspect ratio
        fig.update_layout(
            width=dimensions['width'],
            height=dimensions['height'],
            margin={'l': 50, 'r': 50, 't': 50, 'b': 50},
            font=dict(family='Arial, sans-serif', size=12)
        )
        
        return fig
    
    def render_histogram(self, df: pd.DataFrame, x_col: str,
                        color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a histogram."""
        fig = px.histogram(
            df, x=x_col, color=color_col,
            title=title, **kwargs
        )
        
        # Calculate dimensions maintaining 2:1 aspect ratio
        labels = df[x_col].unique().tolist() if x_col in df.columns else []
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        
        from .plot_utils import calculate_aspect_ratio_dimensions
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=labels,
            legend_items=legend_items,
            base_width=DEFAULT_WIDTH
        )
        
        # Apply dimensions maintaining aspect ratio
        fig.update_layout(
            width=dimensions['width'],
            height=dimensions['height'],
            **self.default_layout
        )
        
        # Apply centralized legend configuration
        from .legend_config import configure_legend
        from .plot_config import DEFAULT_HEIGHT
        fig = configure_legend(
            fig=fig,
            df=df,
            color_col=color_col,
            is_subplot=False,
            width=dimensions['width'],
            height=dimensions.get('height', DEFAULT_HEIGHT),
            legend_title=("Groups" if color_col else None),
            show_mean_sem_label=True
        )
        
        return fig
    
    def render_violin(self, df: pd.DataFrame, x_col: str, y_col: str,
                     color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a violin plot."""
        fig = px.violin(
            df, x=x_col, y=y_col, color=color_col,
            title=title, **kwargs
        )
        
        # Calculate dimensions maintaining 2:1 aspect ratio
        labels = df[x_col].unique().tolist() if x_col in df.columns else []
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        
        from .plot_utils import calculate_aspect_ratio_dimensions
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=labels,
            legend_items=legend_items,
            base_width=DEFAULT_WIDTH
        )
        
        # Apply dimensions maintaining aspect ratio
        fig.update_layout(
            width=dimensions['width'],
            height=dimensions['height'],
            **self.default_layout
        )
        
        # Apply centralized legend configuration
        from .legend_config import configure_legend
        from .plot_config import DEFAULT_HEIGHT
        fig = configure_legend(
            fig=fig,
            df=df,
            color_col=color_col,
            is_subplot=False,
            width=dimensions['width'],
            height=dimensions.get('height', DEFAULT_HEIGHT),
            legend_title=("Groups" if color_col else None),
            show_mean_sem_label=True
        )
        
        return fig
    
    def render_3d_scatter(self, df: pd.DataFrame, x_col: str, y_col: str, z_col: str,
                         color_col: Optional[str] = None, title: str = "", **kwargs) -> go.Figure:
        """Render a 3D scatter plot."""
        fig = px.scatter_3d(
            df, x=x_col, y=y_col, z=z_col, color=color_col,
            title=title, **kwargs
        )
        
        # Calculate dimensions maintaining 2:1 aspect ratio
        # For 3D plots, we'll use a more square aspect ratio since they need more height
        legend_items = len(df[color_col].unique()) if color_col and color_col in df.columns else 0
        
        from .plot_utils import calculate_aspect_ratio_dimensions
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=[],  # 3D plots don't have x-axis labels in the same way
            legend_items=legend_items,
            base_width=DEFAULT_WIDTH
        )
        
        # For 3D plots, adjust to be more square (reduce aspect ratio)
        adjusted_height = int(dimensions['width'] * 0.8)  # 1.25:1 ratio for 3D
        
        # Apply dimensions maintaining adjusted aspect ratio for 3D
        fig.update_layout(
            width=dimensions['width'],
            height=adjusted_height,
            margin={'l': 50, 'r': 50, 't': 50, 'b': 50},
            font=dict(family='Arial, sans-serif', size=12)
        )
        
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
        
        # Calculate dimensions maintaining 2:1 aspect ratio for subplots
        from .plot_utils import calculate_aspect_ratio_dimensions
        
        # Estimate labels and legend items from the plots
        total_legend_items = sum(len(plot.data) for plot in plots)
        
        from .plot_config import DEFAULT_WIDTH
        dimensions = calculate_aspect_ratio_dimensions(
            labels=[],  # Subplot titles are handled separately
            legend_items=total_legend_items,
            num_subplots=rows * cols,
            base_width=DEFAULT_WIDTH
        )
        
        # Apply dimensions maintaining aspect ratio
        fig.update_layout(
            width=dimensions['width'],
            height=dimensions['height'],
            **self.default_layout
        )
        
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
        """Export figure to HTML file embedding Plotly.js for offline use."""
        fig.write_html(
            filepath,
            include_plotlyjs=True,
            full_html=full_html,
            config=dict(
                editable=True,
                edits=dict(
                    axisTitleText=True,
                    titleText=True,
                    legendText=True
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
        # Always embed Plotly.js for offline use regardless of optimization level
        if optimization_level == 'minimal':
            config = dict(
                displayModeBar=False,
                editable=False,
                responsive=True,
                displaylogo=False
            )
        elif optimization_level == 'balanced':
            config = dict(
                displayModeBar=True,
                editable=True,
                responsive=True,
                displaylogo=False
            )
        else:  # 'full'
            config = dict(
                displayModeBar=True,
                editable=True,
                responsive=True,
                displaylogo=False
            )
        
        # Generate the HTML
        html_content = fig.to_html(
            include_plotlyjs=True,
            full_html=True,
            config=config
        )
        
        # Debug: Check if title is preserved in HTML
        logger.debug(f"HTML export - Figure title before export: {getattr(fig.layout, 'title', 'NO_TITLE')}")
        if 'title' in html_content.lower():
            logger.debug("HTML export - Title found in generated HTML")
        else:
            logger.warning("HTML export - Title not found in generated HTML")
        
        # No CDN injection; HTML is fully self-contained for offline use
        
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

    def export_to_pdf_selenium(self, fig: go.Figure, filepath: str, 
                              width: int = 1800, height: int = 600, scale: int = 1) -> None:
        """
        Export Plotly figure to PDF using Selenium + system browser.
        
        This method uses your system's default browser (Safari, Chrome, Firefox)
        instead of requiring a specific Chrome installation like Kaleido.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.safari.options import Options as SafariOptions
            import tempfile
            import os
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                # Export Plotly figure to HTML (this part stays exactly the same!)
                fig.write_html(tmp.name, include_plotlyjs=True, full_html=True)
                html_path = tmp.name
            
            # Try different browsers in order of preference
            drivers = []
            
            # Try Safari first (macOS default)
            try:
                safari_options = SafariOptions()
                driver = webdriver.Safari(options=safari_options)
                drivers.append(('Safari', driver))
            except:
                pass
            
            # Try Chrome
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                driver = webdriver.Chrome(options=chrome_options)
                drivers.append(('Chrome', driver))
            except:
                pass
            
            # Try Firefox
            try:
                firefox_options = FirefoxOptions()
                firefox_options.add_argument('--headless')
                driver = webdriver.Firefox(options=firefox_options)
                drivers.append(('Firefox', driver))
            except:
                pass
            
            if not drivers:
                raise RuntimeError("No browser drivers available. Install Selenium and a browser driver.")
            
            # Use the first available driver
            browser_name, driver = drivers[0]
            logger.info(f"Using {browser_name} for PDF export")
            
            try:
                # Load the HTML file
                driver.get(f"file://{html_path}")
                
                # Wait for Plotly to render
                driver.implicitly_wait(5)
                
                # Set page size for PDF
                driver.execute_script(f"document.body.style.width = '{width}px'")
                driver.execute_script(f"document.body.style.height = '{height}px'")
                
                # Print to PDF
                print_options = {
                    'printBackground': True,
                    'paperWidth': width / 96,  # Convert pixels to inches
                    'paperHeight': height / 96,
                    'marginTop': 0,
                    'marginBottom': 0,
                    'marginLeft': 0,
                    'marginRight': 0,
                    'scale': scale
                }
                
                result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
                
                # Save PDF - handle both base64 and hex data formats
                pdf_data = result.get('data', '')
                if pdf_data:
                    try:
                        # Try base64 first (most common)
                        import base64
                        pdf_bytes = base64.b64decode(pdf_data)
                        with open(filepath, 'wb') as f:
                            f.write(pdf_bytes)
                    except Exception:
                        try:
                            # Try hex format
                            pdf_bytes = bytes.fromhex(pdf_data)
                            with open(filepath, 'wb') as f:
                                f.write(pdf_bytes)
                        except Exception as hex_error:
                            raise RuntimeError(f"Could not decode PDF data: {hex_error}")
                else:
                    raise RuntimeError("No PDF data received from browser")
                
                logger.info(f"PDF export successful using {browser_name}: {filepath}")
                
            finally:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning(f"Failed to quit browser driver: {e}")
                
            # Clean up temporary file
            try:
                os.unlink(html_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary HTML file: {e}")
            
        except ImportError as e:
            if "selenium" in str(e):
                raise RuntimeError(
                    "Selenium not available. Install with: pip install selenium"
                )
            else:
                raise RuntimeError(f"Required library not available: {e}")
        except Exception as e:
            raise RuntimeError(f"Selenium PDF export failed: {str(e)}")

    def export_to_pdf_with_fallback(self, fig: go.Figure, filepath: str, 
                                  width: int = 1800, height: int = 600, 
                                  scale: int = 1) -> None:
        """
        Export figure to PDF with automatic fallback between Selenium and Kaleido.
        
        This method tries Selenium first (more reliable), then falls back to Kaleido
        if Selenium fails. This gives you the best of both worlds.
        """
        try:
            # Try Selenium first (more reliable)
            logger.info("Attempting PDF export with Selenium...")
            self.export_to_pdf_selenium(fig, filepath, width, height, scale)
            logger.info("Selenium PDF export successful")
            
        except Exception as selenium_error:
            logger.warning(f"Selenium PDF export failed: {selenium_error}")
            
            # Fallback to original Kaleido method
            try:
                logger.info("Falling back to Kaleido method...")
                temp_fig = fig
                temp_fig.write_image(filepath, width=width, height=height, scale=scale)
                logger.info("Kaleido fallback successful")
                
            except Exception as kaleido_error:
                # Both methods failed - provide helpful error
                raise RuntimeError(
                    f"PDF export failed with both methods:\n\n"
                    f"Selenium error: {selenium_error}\n"
                    f"Kaleido error: {kaleido_error}\n\n"
                    f"Recommendations:\n"
                    f"1. Install Selenium: pip install selenium\n"
                    f"2. Use HTML export instead\n"
                    f"3. Check browser permissions"
                )
    
    def get_figure_info(self, fig: go.Figure) -> Dict[str, Any]:
        """Get information about a figure."""
        return {
            'data_count': len(fig.data),
            'layout_keys': list(fig.layout.keys()),
            'traces': [trace.type for trace in fig.data],
            'has_annotations': hasattr(fig.layout, 'annotations') and fig.layout.annotations,
            'has_shapes': hasattr(fig.layout, 'shapes') and fig.layout.shapes
        } 