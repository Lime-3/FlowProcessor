"""
Plotly-specific rendering functionality for flow cytometry visualizations.
"""

import logging
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple, Union
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

class PlotlyRenderer:
    """Renderer for Plotly figures with Selenium-based image export."""
    
    def __init__(self):
        """Initialize the renderer."""
        self._setup_plotly_config()
    
    def _setup_plotly_config(self):
        """Configure Plotly for offline use."""
        # Ensure Plotly works offline without CDN
        pio.renderers.default = "browser"
        
        # Configure for offline use
        pio.templates.default = "plotly_white"
        
        logger.debug("Plotly configured for offline use")
    
    def create_figure(self, data: List[go.Trace], layout: Optional[Dict[str, Any]] = None) -> go.Figure:
        """Create a Plotly figure with the given data and layout."""
        fig = go.Figure(data=data)
        
        if layout:
            fig.update_layout(**layout)
        
        return fig
    
    def create_subplots(self, rows: int, cols: int, **kwargs) -> go.Figure:
        """Create subplots with the specified number of rows and columns."""
        return make_subplots(rows=rows, cols=cols, **kwargs)
    
    def render_to_html(self, fig: go.Figure, filepath: str, 
                      include_plotlyjs: bool = True, full_html: bool = True) -> None:
        """Render figure to HTML file."""
        try:
            # Export to HTML with full Plotly.js included
            html_content = fig.to_html(
                include_plotlyjs=include_plotlyjs,
                full_html=full_html,
                config={'displayModeBar': True, 'displaylogo': False}
            )
            
            # Ensure the HTML is written to the specified filepath
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML export successful: {filepath}")
            
        except Exception as e:
            logger.error(f"HTML export failed: {e}")
            raise RuntimeError(f"Failed to export HTML: {e}")
    
    def export_to_html_optimized(self, fig: go.Figure, filepath: str, 
                                optimization_level: str = 'minimal') -> None:
        """
        Export figure to optimized HTML file.
        
        Args:
            fig: Plotly figure to export
            filepath: Path to save the HTML file
            optimization_level: Level of optimization ('minimal', 'standard', 'full')
        """
        try:
            # Configure optimization based on level
            if optimization_level == 'minimal':
                # Minimal optimization - include plotly.js but optimize config
                html_content = fig.to_html(
                    include_plotlyjs=True,
                    full_html=True,
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                        'responsive': True
                    }
                )
            elif optimization_level == 'standard':
                # Standard optimization - balanced performance and features
                html_content = fig.to_html(
                    include_plotlyjs=True,
                    full_html=True,
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'hoverClosestCartesian'],
                        'responsive': True,
                        'scrollZoom': True
                    }
                )
            elif optimization_level == 'full':
                # Full optimization - maximum performance
                html_content = fig.to_html(
                    include_plotlyjs=True,
                    full_html=True,
                    config={
                        'displayModeBar': False,
                        'displaylogo': False,
                        'responsive': True,
                        'staticPlot': True
                    }
                )
            else:
                # Default to minimal if invalid level specified
                html_content = fig.to_html(
                    include_plotlyjs=True,
                    full_html=True,
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            
            # Write the optimized HTML to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Optimized HTML export successful ({optimization_level}): {filepath}")
            
        except Exception as e:
            logger.error(f"Optimized HTML export failed: {e}")
            raise RuntimeError(f"Failed to export optimized HTML: {e}")
    
    def export_to_png_selenium(self, fig: go.Figure, filepath: str, 
                              width: int = 800, height: int = 600, scale: int = 1) -> None:
        """
        Export Plotly figure to PNG using Selenium + system browser.
        
        This method uses your system's default browser to render the plot and capture a screenshot.
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
                # Export Plotly figure to HTML
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
                chrome_options.add_argument(f'--window-size={width},{height}')
                driver = webdriver.Chrome(options=chrome_options)
                drivers.append(('Chrome', driver))
            except:
                pass
            
            # Try Firefox
            try:
                firefox_options = FirefoxOptions()
                firefox_options.add_argument('--headless')
                firefox_options.add_argument(f'--width={width}')
                firefox_options.add_argument(f'--height={height}')
                driver = webdriver.Firefox(options=firefox_options)
                drivers.append(('Firefox', driver))
            except:
                pass
            
            if not drivers:
                raise RuntimeError("No browser drivers available. Install Selenium and a browser driver.")
            
            # Use the first available driver
            browser_name, driver = drivers[0]
            logger.info(f"Using {browser_name} for PNG export")
            
            try:
                # Load the HTML file
                driver.get(f"file://{html_path}")
                
                # Wait for Plotly to render
                driver.implicitly_wait(5)
                
                # Set window size
                driver.set_window_size(width, height)
                
                # Take screenshot
                driver.save_screenshot(filepath)
                
                logger.info(f"PNG export successful using {browser_name}: {filepath}")
                
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
            raise RuntimeError(f"Selenium PNG export failed: {str(e)}")
    
    def export_to_svg_selenium(self, fig: go.Figure, filepath: str, 
                              width: int = 800, height: int = 600, scale: int = 1) -> None:
        """
        Export Plotly figure to SVG using Selenium + system browser.
        
        This method uses your system's default browser to render the plot and extract SVG content.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.safari.options import Options as SafariOptions
            import tempfile
            import os
            import re
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                # Export Plotly figure to HTML
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
                chrome_options.add_argument(f'--window-size={width},{height}')
                driver = webdriver.Chrome(options=chrome_options)
                drivers.append(('Chrome', driver))
            except:
                pass
            
            # Try Firefox
            try:
                firefox_options = FirefoxOptions()
                firefox_options.add_argument('--headless')
                firefox_options.add_argument(f'--width={width}')
                firefox_options.add_argument(f'--height={height}')
                driver = webdriver.Firefox(options=firefox_options)
                drivers.append(('Firefox', driver))
            except:
                pass
            
            if not drivers:
                raise RuntimeError("No browser drivers available. Install Selenium and a browser driver.")
            
            # Use the first available driver
            browser_name, driver = drivers[0]
            logger.info(f"Using {browser_name} for SVG export")
            
            try:
                # Load the HTML file
                driver.get(f"file://{html_path}")
                
                # Wait for Plotly to render
                driver.implicitly_wait(5)
                
                # Set window size
                driver.set_window_size(width, height)
                
                # Extract SVG content from the plot
                svg_element = driver.find_element("css selector", "svg.main-svg")
                svg_content = svg_element.get_attribute("outerHTML")
                
                # Clean up SVG content
                if svg_content:
                    # Write SVG to file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(svg_content)
                    
                    logger.info(f"SVG export successful using {browser_name}: {filepath}")
                else:
                    raise RuntimeError("No SVG content found in the plot")
                
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
            raise RuntimeError(f"Selenium SVG export failed: {str(e)}")
    
    def export_to_pdf_selenium(self, fig: go.Figure, filepath: str, 
                              width: int = 1800, height: int = 600, scale: int = 1) -> None:
        """
        Export Plotly figure to PDF using Selenium + system browser.
        
        This method uses your system's default browser (Safari, Chrome, Firefox)
        to render the plot and print to PDF.
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
                # Export Plotly figure to HTML
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
    
    def export_to_image(self, fig: go.Figure, filepath: str, 
                       format: str = 'png', width: int = 800, height: int = 600) -> None:
        """Export figure to image file using Selenium."""
        format = format.lower()
        
        if format == 'png':
            self.export_to_png_selenium(fig, filepath, width, height)
        elif format == 'svg':
            self.export_to_svg_selenium(fig, filepath, width, height)
        elif format == 'pdf':
            self.export_to_pdf_selenium(fig, filepath, width, height)
        else:
            raise ValueError(f"Unsupported format: {format}. Supported formats: png, svg, pdf")
    
    def export_to_png(self, fig: go.Figure, filepath: str, 
                     width: int = 800, height: int = 600) -> None:
        """Export figure to PNG format using Selenium."""
        self.export_to_png_selenium(fig, filepath, width, height)
    
    def export_to_pdf(self, fig: go.Figure, filepath: str, 
                     width: int = 1800, height: int = 600, scale: int = 1) -> None:
        """Export figure to PDF format using Selenium."""
        self.export_to_pdf_selenium(fig, filepath, width, height, scale)
    
    def export_to_svg(self, fig: go.Figure, filepath: str, 
                     width: int = 800, height: int = 600) -> None:
        """Export figure to SVG format using Selenium."""
        self.export_to_svg_selenium(fig, filepath, width, height)
    
    def get_figure_info(self, fig: go.Figure) -> Dict[str, Any]:
        """Get information about a figure."""
        return {
            'data_count': len(fig.data),
            'layout': fig.layout.to_dict() if fig.layout else {},
            'frames': len(fig.frames) if fig.frames else 0,
            'config': fig.config.to_dict() if fig.config else {}
        }
    
    def update_layout(self, fig: go.Figure, **kwargs) -> go.Figure:
        """Update figure layout with the given parameters."""
        fig.update_layout(**kwargs)
        return fig
    
    def add_trace(self, fig: go.Figure, trace: go.Trace, row: Optional[int] = None, 
                  col: Optional[int] = None) -> go.Figure:
        """Add a trace to the figure."""
        fig.add_trace(trace, row=row, col=col)
        return fig
    
    def show(self, fig: go.Figure) -> None:
        """Display the figure in the default browser."""
        fig.show()
    
    def to_dict(self, fig: go.Figure) -> Dict[str, Any]:
        """Convert figure to dictionary representation."""
        return fig.to_dict()
    
    def from_dict(self, data: Dict[str, Any]) -> go.Figure:
        """Create figure from dictionary representation."""
        return go.Figure(data)
    
    @staticmethod
    def save_plot(fig: go.Figure, filepath: str, format: str = 'html') -> None:
        """
        Static method to save a plot in the specified format.
        
        Args:
            fig: Plotly figure to save
            filepath: Path to save the file
            format: Output format ('html', 'png', 'pdf', 'svg')
        """
        renderer = PlotlyRenderer()
        
        if format.lower() == 'html':
            renderer.export_to_html_optimized(fig, filepath, 'minimal')
        elif format.lower() == 'png':
            renderer.export_to_png(fig, filepath)
        elif format.lower() == 'pdf':
            renderer.export_to_pdf(fig, filepath)
        elif format.lower() == 'svg':
            renderer.export_to_svg(fig, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}. Supported formats: html, png, pdf, svg") 