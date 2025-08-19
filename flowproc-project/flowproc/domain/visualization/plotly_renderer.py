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

# Import browser manager for caching
from .browser_manager import browser_manager

class PlotlyRenderer:
    """Renderer for Plotly figures with Selenium-based image export."""
    
    def __init__(self):
        """Initialize the renderer."""
        self._setup_plotly_config()
        # Pre-initialize browser for better performance
        self._preinitialize_browser()
    
    def _preinitialize_browser(self):
        """Pre-initialize browser in background to avoid delays on first export."""
        try:
            if not browser_manager.is_initialized() and not browser_manager.is_initializing():
                logger.debug("Starting background browser initialization for better export performance")
                # Start background initialization with default dimensions
                browser_manager.initialize_browser(
                    width=1800, 
                    height=600, 
                    background=True,
                    callback=self._on_browser_initialized
                )
        except Exception as e:
            logger.debug(f"Browser pre-initialization failed (will initialize on demand): {e}")
    
    def _on_browser_initialized(self, success: bool):
        """Callback for when background browser initialization completes."""
        if success:
            logger.debug("Background browser initialization completed successfully")
        else:
            logger.warning("Background browser initialization failed")
    
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
        Export Plotly figure to PNG using cached browser instance.
        
        This method uses a cached browser driver to render the plot and capture a screenshot,
        providing better performance for multiple exports.
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
            
            # Initialize browser if not already done
            if not browser_manager.is_initialized():
                if browser_manager.is_initializing():
                    logger.info("Browser initialization in progress, waiting for completion...")
                    # Wait for background initialization to complete
                    if not browser_manager.wait_for_initialization(timeout=30.0):
                        raise RuntimeError("Browser initialization timed out")
                else:
                    logger.info("Initializing browser for PNG export")
                    if not browser_manager.initialize_browser(width, height):
                        raise RuntimeError("Failed to initialize browser for PNG export")
            
            # Use cached browser instance
            browser_name = browser_manager.get_browser_name()
            logger.info(f"Using cached {browser_name} browser for PNG export")
            
            try:
                with browser_manager.get_browser() as driver:
                    # Load the HTML file
                    driver.get(f"file://{html_path}")
                    
                    # Wait for Plotly to render
                    driver.implicitly_wait(5)
                    
                    # Set window size
                    driver.set_window_size(width, height)
                    
                    # Take screenshot
                    driver.save_screenshot(filepath)
                    
                    logger.info(f"PNG export successful using {browser_name}: {filepath}")
                
            except Exception as e:
                logger.error(f"Browser operation failed: {e}")
                # Try to reset browser on critical errors
                if "session not created" in str(e).lower() or "chrome not reachable" in str(e).lower():
                    logger.info("Resetting browser due to session error")
                    browser_manager.reset_browser()
                raise
                
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
        Export Plotly figure to SVG using cached browser instance.
        
        This method uses a cached browser driver to render the plot and extract SVG content,
        providing better performance for multiple exports.
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
            
            # Initialize browser if not already done
            if not browser_manager.is_initialized():
                if browser_manager.is_initializing():
                    logger.info("Browser initialization in progress, waiting for completion...")
                    # Wait for background initialization to complete
                    if not browser_manager.wait_for_initialization(timeout=30.0):
                        raise RuntimeError("Browser initialization timed out")
                else:
                    logger.info("Initializing browser for SVG export")
                    if not browser_manager.initialize_browser(width, height):
                        raise RuntimeError("Failed to initialize browser for SVG export")
            
            # Use cached browser instance
            browser_name = browser_manager.get_browser_name()
            logger.info(f"Using cached {browser_name} browser for SVG export")
            
            try:
                with browser_manager.get_browser() as driver:
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
                
            except Exception as e:
                logger.error(f"Browser operation failed: {e}")
                # Try to reset browser on critical errors
                if "session not created" in str(e).lower() or "chrome not reachable" in str(e).lower():
                    logger.info("Resetting browser due to session error")
                    browser_manager.reset_browser()
                raise
                
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
        Export Plotly figure to PDF using cached browser instance.
        
        This method uses a cached browser driver to render the plot and print to PDF,
        providing better performance for multiple exports.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.safari.options import Options as SafariOptions
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            import tempfile
            import os
            
            # Create temporary HTML file with optimized content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                # Export Plotly figure to HTML with minimal dependencies
                html_content = fig.to_html(
                    include_plotlyjs=True,
                    full_html=True,
                    config={
                        'displayModeBar': False,  # Hide toolbar for cleaner PDF
                        'displaylogo': False,
                        'responsive': False,  # Fixed dimensions for PDF
                        'staticPlot': False  # Keep interactivity for rendering
                    }
                )
                tmp.write(html_content)
                tmp.flush()
                html_path = tmp.name
            
            # Initialize browser if not already done
            if not browser_manager.is_initialized():
                if browser_manager.is_initializing():
                    logger.info("Browser initialization in progress, waiting for completion...")
                    # Wait for background initialization to complete
                    if not browser_manager.wait_for_initialization(timeout=30.0):
                        raise RuntimeError("Browser initialization timed out after 30 seconds")
                else:
                    logger.info("Initializing browser for PDF export")
                    if not browser_manager.initialize_browser(width, height):
                        # Get system browser info for better error reporting
                        system_info = browser_manager.get_system_browser_info()
                        available_browsers = [k for k, v in system_info.get('available_browsers', {}).items() if v.get('available', False)]
                        
                        if not available_browsers:
                            raise RuntimeError(
                                "No browsers available for PDF export. Please install Chrome, Brave, Firefox, or Safari."
                            )
                        elif 'safari' in available_browsers and system_info.get('system_default') == 'safari':
                            raise RuntimeError(
                                "Safari browser initialization failed. To use Safari for PDF export, enable 'Allow remote automation' in Safari's Developer settings (Safari > Settings > Advanced > Show Develop menu, then Develop > Allow Remote Automation). Alternatively, the system will automatically try other available browsers."
                            )
                        else:
                            raise RuntimeError(
                                f"Failed to initialize any available browser for PDF export. Available browsers: {', '.join(available_browsers)}. Please check browser installation and try again."
                            )
            
            # Use cached browser instance
            browser_name = browser_manager.get_browser_name()
            logger.info(f"Using cached {browser_name} browser for PDF export")
            
            try:
                with browser_manager.get_browser() as driver:
                    # Load the HTML file
                    driver.get(f"file://{html_path}")
                    
                    # Wait for Plotly to render completely
                    wait = WebDriverWait(driver, 10)
                    try:
                        # Wait for Plotly to be ready
                        wait.until(lambda d: d.execute_script("return typeof Plotly !== 'undefined'"))
                        # Wait a bit more for full rendering
                        driver.implicitly_wait(2)
                    except Exception as e:
                        logger.warning(f"Plotly ready check failed, proceeding anyway: {e}")
                    
                    # Set page size and ensure proper dimensions
                    driver.execute_script(f"document.body.style.width = '{width}px'")
                    driver.execute_script(f"document.body.style.height = '{height}px'")
                    driver.execute_script(f"document.body.style.margin = '0'")
                    driver.execute_script(f"document.body.style.padding = '0'")
                    
                    # Set viewport size
                    driver.set_window_size(width, height)
                    
                    # Print to PDF with optimized settings
                    print_options = {
                        'printBackground': True,
                        'paperWidth': width / 96,  # Convert pixels to inches
                        'paperHeight': height / 96,
                        'marginTop': 0.1,  # Small margin to prevent cutoff
                        'marginBottom': 0.1,
                        'marginLeft': 0.1,
                        'marginRight': 0.1,
                        'scale': scale,
                        'preferCSSPageSize': True
                    }
                    
                    # Use CDP for Chrome-based browsers, fallback for others
                    if browser_name in ['Chrome', 'Brave']:
                        try:
                            # For Brave/Chrome, try CDP commands
                            result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
                            pdf_data = result.get('data', '')
                            
                            if not pdf_data:
                                # Try alternative CDP command for some Brave versions
                                try:
                                    logger.debug("Primary CDP command returned no data, trying alternative...")
                                    result = driver.execute_cdp_cmd('Page.captureScreenshot', {
                                        'format': 'pdf',
                                        'quality': 100
                                    })
                                    pdf_data = result.get('data', '')
                                except Exception as alt_e:
                                    logger.debug(f"Alternative CDP command failed: {alt_e}")
                                    pass
                                    
                            if not pdf_data:
                                # Try to get CDP version info to debug
                                try:
                                    version_info = driver.execute_cdp_cmd('Runtime.evaluate', {
                                        'expression': 'navigator.userAgent'
                                    })
                                    logger.debug(f"Browser user agent: {version_info.get('result', {}).get('value', 'Unknown')}")
                                except Exception:
                                    pass
                                    
                        except Exception as e:
                            logger.warning(f"CDP command failed: {e}, trying alternative method")
                            pdf_data = self._fallback_pdf_export(driver, browser_name)
                            
                    elif browser_name == 'Safari':
                        try:
                            # Safari supports CDP commands
                            result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
                            pdf_data = result.get('data', '')
                        except Exception as e:
                            logger.warning(f"Safari CDP command failed: {e}, trying alternative method")
                            pdf_data = self._fallback_pdf_export(driver, browser_name)
                    else:
                        # Firefox fallback
                        pdf_data = self._fallback_pdf_export(driver, browser_name)
                    
                    # Save PDF - handle both base64 and hex data formats
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
                
            except Exception as e:
                logger.error(f"Browser operation failed: {e}")
                # Try to reset browser on critical errors
                if "session not created" in str(e).lower() or "chrome not reachable" in str(e).lower():
                    logger.info("Resetting browser due to session error")
                    browser_manager.reset_browser()
                raise
                
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
    
    def _fallback_pdf_export(self, driver, browser_name: str) -> str:
        """Fallback PDF export method for browsers that don't support CDP."""
        try:
            if browser_name == 'Brave':
                # Brave-specific fallback - try to use print dialog
                logger.info("Brave CDP failed, trying print dialog fallback")
                try:
                    # Try to trigger print and capture
                    driver.execute_script("window.print();")
                    logger.warning("Brave fallback opened print dialog - manual intervention may be required")
                    return ""
                except Exception as e:
                    logger.warning(f"Brave print dialog failed: {e}")
                    return ""
                    
            elif browser_name == 'Chrome':
                # Chrome fallback
                logger.info("Chrome CDP failed, trying alternative methods")
                try:
                    # Try to use print API
                    driver.execute_script("window.print();")
                    logger.warning("Chrome fallback opened print dialog - manual intervention may be required")
                    return ""
                except Exception as e:
                    logger.warning(f"Chrome print dialog failed: {e}")
                    return ""
                    
            elif browser_name == 'Safari':
                # Safari fallback
                logger.info("Safari CDP failed, trying alternative methods")
                try:
                    driver.execute_script("window.print();")
                    logger.warning("Safari fallback opened print dialog - manual intervention may be required")
                    return ""
                except Exception as e:
                    logger.warning(f"Safari print dialog failed: {e}")
                    return ""
                    
            elif browser_name == 'Firefox':
                # Firefox fallback
                logger.info("Firefox fallback - using print dialog")
                try:
                    driver.execute_script("window.print();")
                    logger.warning("Firefox fallback opened print dialog - manual intervention may be required")
                    return ""
                except Exception as e:
                    logger.warning(f"Firefox print dialog failed: {e}")
                    return ""
            else:
                # Generic fallback
                logger.warning(f"No fallback method available for {browser_name}")
                return ""
                
        except Exception as e:
            logger.error(f"Fallback PDF export failed: {e}")
            return ""
    
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
    
    def check_pdf_capabilities(self) -> Dict[str, bool]:
        """
        Check what PDF export methods are available.
        
        Returns:
            Dictionary with available export methods and their status
        """
        capabilities = {
            'selenium': False,
            'browsers': {
                'safari': False,
                'chrome': False,
                'brave': False,
                'firefox': False
            }
        }
        
        try:
            from selenium import webdriver
            from selenium.webdriver.safari.options import Options as SafariOptions
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            
            # Test Safari
            try:
                safari_options = SafariOptions()
                driver = webdriver.Safari(options=safari_options)
                driver.quit()
                capabilities['browsers']['safari'] = True
                capabilities['selenium'] = True
            except Exception:
                pass
            
            # Test Chrome/Brave
            try:
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                
                # Check for Brave browser
                brave_paths = [
                    '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',  # macOS
                    '/usr/bin/brave-browser',  # Linux
                    '/usr/bin/brave-browser-stable',  # Linux
                    'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',  # Windows
                    'C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe'  # Windows
                ]
                
                brave_found = False
                for brave_path in brave_paths:
                    if os.path.exists(brave_path):
                        chrome_options.binary_location = brave_path
                        brave_found = True
                        break
                
                driver = webdriver.Chrome(options=chrome_options)
                driver.quit()
                
                if brave_found:
                    capabilities['browsers']['brave'] = True
                else:
                    capabilities['browsers']['chrome'] = True
                    
                capabilities['selenium'] = True
            except Exception:
                pass
            
            # Test Firefox
            try:
                firefox_options = FirefoxOptions()
                firefox_options.add_argument('--headless')
                driver = webdriver.Firefox(options=firefox_options)
                driver.quit()
                capabilities['browsers']['firefox'] = True
                capabilities['selenium'] = True
            except Exception:
                pass
                
        except ImportError:
            pass
        
        return capabilities

    def export_to_pdf(self, fig: go.Figure, filepath: str, 
                     width: int = 1800, height: int = 600, scale: int = 1) -> None:
        """
        Export figure to PDF format using Selenium-based browser export.
        
        This method provides direct control over the browser process for reliable PDF generation.
        """
        # Check capabilities first
        capabilities = self.check_pdf_capabilities()
        
        if not capabilities['selenium']:
            raise RuntimeError(
                "Selenium not available for PDF export. Install with: pip install selenium"
            )
        
        available_browsers = [k for k, v in capabilities['browsers'].items() if v]
        if not available_browsers:
            raise RuntimeError(
                "No browser drivers available. Install browser drivers for Safari, Chrome, or Firefox."
            )
        
        logger.info(f"PDF export using Selenium with available browsers: {', '.join(available_browsers)}")
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
    
    def get_browser_status(self) -> Dict[str, Any]:
        """Get current browser status and performance information."""
        return {
            'browser_manager': browser_manager.get_browser_info(),
            'renderer_initialized': hasattr(self, '_setup_plotly_config'),
            'cached_browser_available': browser_manager.is_initialized(),
            'browser_initializing': browser_manager.is_initializing(),
            'browser_ready': browser_manager.is_initialized() and not browser_manager.is_initializing()
        }
    
    def get_browser_initialization_status(self) -> Dict[str, Any]:
        """Get detailed browser initialization status."""
        return {
            'is_initialized': browser_manager.is_initialized(),
            'is_initializing': browser_manager.is_initializing(),
            'browser_name': browser_manager.get_browser_name(),
            'system_browsers': browser_manager.get_system_browser_info(),
            'health_status': browser_manager.health_check() if browser_manager.is_initialized() else None
        }
    
    def reset_browser_cache(self) -> None:
        """Reset the browser cache (useful for troubleshooting)."""
        logger.info("Resetting browser cache")
        browser_manager.reset_browser()
        # Re-initialize if needed
        self._preinitialize_browser()
    
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