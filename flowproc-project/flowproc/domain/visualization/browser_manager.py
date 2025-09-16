"""
Browser manager for Selenium-based PDF export operations.

This module provides a centralized browser management system that:
- Initializes browser drivers once and reuses them
- Manages browser lifecycle and cleanup
- Provides fallback options for different browsers
- Handles browser-specific configurations
"""

import logging
import os
import tempfile
import subprocess
import platform
import threading
import time
from typing import Optional, Dict, Any, Tuple, Callable, List
from contextlib import contextmanager
import atexit

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.safari.options import Options as SafariOptions
    from selenium.webdriver.remote.webdriver import WebDriver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    webdriver = None
    Options = None
    FirefoxOptions = None
    SafariOptions = None
    WebDriver = None

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Manages browser instances for PDF export operations.
    
    This class implements a singleton pattern to ensure only one browser
    instance is created and reused across multiple export operations.
    """
    
    _instance = None
    _browser_driver: Optional[WebDriver] = None
    _browser_name: Optional[str] = None
    _browser_options: Optional[Dict[str, Any]] = None
    _instance_initialized = False  # Track if the instance has been initialized
    _is_initializing = False
    _initialization_thread: Optional[threading.Thread] = None
    _initialization_callbacks: List[Callable[[bool], None]] = []
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the browser manager."""
        if not self._instance_initialized:
            self._instance_initialized = True
            # Register cleanup on application exit
            atexit.register(self.cleanup)
    
    def _detect_system_default_browser(self) -> Optional[str]:
        """
        Detect the system default browser.
        
        Returns:
            Browser type string ('safari', 'chrome', 'brave', 'firefox') or None
        """
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                # Use macOS system command to get default browser
                try:
                    result = subprocess.run(
                        ['defaults', 'read', 'com.apple.LaunchServices', 'com.apple.launchservices.secure', 'LSHandlers'],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        # Parse the output to find the default browser
                        output = result.stdout
                        if 'com.apple.safari' in output:
                            return 'safari'
                        elif 'com.brave.browser' in output:
                            return 'brave'
                        elif 'com.google.chrome' in output:
                            return 'chrome'
                        elif 'org.mozilla.firefox' in output:
                            return 'firefox'
                except Exception as e:
                    logger.debug(f"Failed to detect macOS default browser via defaults: {e}")
                
                # Skip browser detection that opens HTML files to avoid test windows
                # This method was causing test browser windows to open when packaged
                # Instead, we'll rely on the file existence checks above
                logger.debug("Skipping browser detection via HTML file opening to prevent test windows")
                
                # Final fallback: check common browser locations with better priority
                # Since the defaults command failed, we'll prioritize browsers that are more likely
                # to be user-installed rather than system-default
                if os.path.exists('/Applications/Brave Browser.app'):
                    logger.debug("Brave Browser found, assuming it's the preferred choice")
                    return 'brave'
                elif os.path.exists('/Applications/Google Chrome.app'):
                    logger.debug("Google Chrome found, assuming it's the preferred choice")
                    return 'chrome'
                elif os.path.exists('/Applications/Firefox.app'):
                    logger.debug("Firefox found, assuming it's the preferred choice")
                    return 'firefox'
                elif os.path.exists('/Applications/Safari.app'):
                    logger.debug("Safari found (system default)")
                    return 'safari'
                    
            elif system == "linux":
                # Try to get default browser from xdg-settings
                try:
                    result = subprocess.run(
                        ['xdg-settings', 'get', 'default-web-browser'],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        browser = result.stdout.strip()
                        if 'brave' in browser.lower():
                            return 'brave'
                        elif 'chrome' in browser.lower():
                            return 'chrome'
                        elif 'firefox' in browser.lower():
                            return 'firefox'
                        elif 'safari' in browser.lower():
                            return 'safari'
                except Exception as e:
                    logger.debug(f"Failed to detect Linux default browser: {e}")
                
                # Fallback: check common browser locations
                if os.path.exists('/usr/bin/brave-browser'):
                    return 'brave'
                elif os.path.exists('/usr/bin/google-chrome'):
                    return 'chrome'
                elif os.path.exists('/usr/bin/firefox'):
                    return 'firefox'
                    
            elif system == "windows":
                # Try to get default browser from registry
                try:
                    import winreg
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                      r'Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice') as key:
                        program_id = winreg.QueryValueEx(key, 'ProgId')[0]
                        if 'Chrome' in program_id:
                            return 'chrome'
                        elif 'Firefox' in program_id:
                            return 'firefox'
                        elif 'Brave' in program_id:
                            return 'brave'
                        elif 'Safari' in program_id:
                            return 'safari'
                except Exception as e:
                    logger.debug(f"Failed to detect Windows default browser: {e}")
                
                # Fallback: check common browser locations
                if os.path.exists(r'C:\Program Files\Google\Chrome\Application\chrome.exe'):
                    return 'chrome'
                elif os.path.exists(r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'):
                    return 'brave'
                elif os.path.exists(r'C:\Program Files\Mozilla Firefox\firefox.exe'):
                    return 'firefox'
            
            logger.debug("Could not detect system default browser")
            return None
            
        except Exception as e:
            logger.debug(f"Error detecting system default browser: {e}")
            return None
    
    def _get_browser_binary_path(self, browser_type: str) -> Optional[str]:
        """
        Get the binary path for a specific browser type.
        
        Args:
            browser_type: Type of browser ('safari', 'chrome', 'brave', 'firefox')
            
        Returns:
            Path to browser binary or None if not found
        """
        system = platform.system().lower()
        
        if browser_type == 'safari':
            if system == "darwin":
                return '/Applications/Safari.app/Contents/MacOS/Safari'
            return None
            
        elif browser_type == 'brave':
            if system == "darwin":
                return '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
            elif system == "linux":
                paths = ['/usr/bin/brave-browser', '/usr/bin/brave-browser-stable']
                for path in paths:
                    if os.path.exists(path):
                        return path
            elif system == "windows":
                paths = [
                    r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
                    r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe'
                ]
                for path in paths:
                    if os.path.exists(path):
                        return path
                        
        elif browser_type == 'chrome':
            if system == "darwin":
                return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            elif system == "linux":
                paths = ['/usr/bin/google-chrome', '/usr/bin/chromium-browser']
                for path in paths:
                    if os.path.exists(path):
                        return path
            elif system == "windows":
                paths = [
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
                ]
                for path in paths:
                    if os.path.exists(path):
                        return path
                        
        elif browser_type == 'firefox':
            if system == "darwin":
                return '/Applications/Firefox.app/Contents/MacOS/firefox'
            elif system == "linux":
                paths = ['/usr/bin/firefox', '/usr/bin/firefox-esr']
                for path in paths:
                    if os.path.exists(path):
                        return path
            elif system == "windows":
                paths = [
                    r'C:\Program Files\Mozilla Firefox\firefox.exe',
                    r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'
                ]
                for path in paths:
                    if os.path.exists(path):
                        return path
        
        return None
    
    def initialize_browser(self, width: int = 1800, height: int = 600, 
                          preferred_browser: Optional[str] = None, 
                          background: bool = False,
                          callback: Optional[Callable[[bool], None]] = None) -> bool:
        """
        Initialize the browser driver if not already initialized.
        
        Args:
            width: Browser window width
            height: Browser window height
            preferred_browser: Preferred browser ('chrome', 'brave', 'safari', 'firefox')
            background: If True, initialize in background thread
            callback: Optional callback function called with success status
            
        Returns:
            True if browser was initialized successfully or background initialization started, False otherwise
        """
        if self._browser_driver is not None:
            logger.debug("Browser already initialized, reusing existing instance")
            if callback:
                callback(True)
            return True
        
        if self._is_initializing:
            logger.debug("Browser initialization already in progress")
            if callback:
                self._initialization_callbacks.append(callback)
            return True
        
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium not available for browser initialization")
            if callback:
                callback(False)
            return False
        
        # Store browser options for reuse
        self._browser_options = {
            'width': width,
            'height': height,
            'preferred_browser': preferred_browser
        }
        
        if background:
            # Start background initialization
            return self._start_background_initialization(width, height, preferred_browser, callback)
        else:
            # Synchronous initialization
            try:
                success = self._try_initialize_browser(width, height, preferred_browser)
                if success:
                    logger.info(f"Browser initialized successfully: {self._browser_name}")
                else:
                    logger.error("Failed to initialize any available browser")
                
                if callback:
                    callback(success)
                return success
                    
            except Exception as e:
                logger.error(f"Browser initialization failed: {e}")
                if callback:
                    callback(False)
                return False
    
    def _start_background_initialization(self, width: int, height: int, 
                                       preferred_browser: Optional[str], 
                                       callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Start browser initialization in a background thread."""
        try:
            self._is_initializing = True
            
            # Add callback to list
            if callback:
                self._initialization_callbacks.append(callback)
            
            # Create and start initialization thread
            self._initialization_thread = threading.Thread(
                target=self._background_initialization_worker,
                args=(width, height, preferred_browser),
                daemon=True,
                name="BrowserInitializationThread"
            )
            self._initialization_thread.start()
            
            logger.info("Browser initialization started in background thread")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start background initialization: {e}")
            self._is_initializing = False
            if callback:
                callback(False)
            return False
    
    def _background_initialization_worker(self, width: int, height: int, 
                                        preferred_browser: Optional[str]) -> None:
        """Background thread worker for browser initialization."""
        try:
            logger.debug("Background browser initialization started")
            success = self._try_initialize_browser(width, height, preferred_browser)
            
            if success:
                logger.info(f"Background browser initialization successful: {self._browser_name}")
            else:
                logger.error("Background browser initialization failed")
            
        except Exception as e:
            logger.error(f"Background browser initialization error: {e}")
            success = False
        
        finally:
            # Update state
            self._is_initializing = False
            self._initialization_thread = None
            
            # Notify all callbacks
            for callback in self._initialization_callbacks:
                try:
                    callback(success)
                except Exception as e:
                    logger.error(f"Callback notification failed: {e}")
            
            # Clear callbacks
            self._initialization_callbacks.clear()
    
    def _try_initialize_browser(self, width: int, height: int, 
                               preferred_browser: Optional[str]) -> bool:
        """
        Try to initialize different browsers in order of preference.
        
        Args:
            width: Browser window width
            height: Browser window height
            preferred_browser: Preferred browser type
            
        Returns:
            True if any browser was initialized successfully
        """
        # Define browser priority order
        if preferred_browser:
            browser_priority = [preferred_browser.lower()]
        else:
            # First try to detect system default browser
            system_default = self._detect_system_default_browser()
            if system_default:
                logger.info(f"Detected system default browser: {system_default}")
                # Include system default first, then fallback browsers
                if os.name == 'posix' and os.uname().sysname == 'Darwin':  # macOS
                    # For macOS, try Safari first, then Chrome/Brave as fallbacks
                    fallback_browsers = ['brave', 'chrome', 'firefox']
                    # Remove system default from fallbacks if it's already there
                    fallback_browsers = [b for b in fallback_browsers if b != system_default]
                    browser_priority = [system_default] + fallback_browsers
                else:
                    # For other platforms, try system default first, then fallbacks
                    fallback_browsers = ['brave', 'chrome', 'firefox', 'safari']
                    fallback_browsers = [b for b in fallback_browsers if b != system_default]
                    browser_priority = [system_default] + fallback_browsers
            else:
                # Fallback to platform-specific priority
                if os.name == 'posix' and os.uname().sysname == 'Darwin':  # macOS
                    browser_priority = ['safari', 'brave', 'chrome', 'firefox']
                else:
                    browser_priority = ['brave', 'chrome', 'firefox', 'safari']
        
        # Try each browser in priority order
        for browser_type in browser_priority:
            try:
                if self._initialize_specific_browser(browser_type, width, height):
                    return True
            except Exception as e:
                logger.debug(f"Failed to initialize {browser_type}: {e}")
                continue
        
        return False
    
    def _initialize_specific_browser(self, browser_type: str, width: int, height: int) -> bool:
        """
        Initialize a specific browser type.
        
        Args:
            browser_type: Type of browser to initialize
            width: Browser window width
            height: Browser window height
            
        Returns:
            True if browser was initialized successfully
        """
        try:
            if browser_type == 'brave':
                return self._initialize_brave(width, height)
            elif browser_type == 'chrome':
                return self._initialize_chrome(width, height)
            elif browser_type == 'safari':
                return self._initialize_safari(width, height)
            elif browser_type == 'firefox':
                return self._initialize_firefox(width, height)
            else:
                logger.warning(f"Unknown browser type: {browser_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize {browser_type}: {e}")
            return False
    
    def _initialize_brave(self, width: int, height: int) -> bool:
        """Initialize Brave browser."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            # Note: JavaScript is required for Plotly rendering, so we don't disable it
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument(f'--window-size={width},{height}')
            
            # Get Brave browser binary path
            brave_path = self._get_browser_binary_path('brave')
            if brave_path and os.path.exists(brave_path):
                chrome_options.binary_location = brave_path
                logger.debug(f"Using Brave browser at: {brave_path}")
            else:
                logger.debug("Brave browser not found, falling back to Chrome")
                return False
            
            # Add Brave-specific options
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            driver = webdriver.Chrome(options=chrome_options)
            self._browser_driver = driver
            self._browser_name = 'Brave'
            return True
            
        except Exception as e:
            logger.debug(f"Brave initialization failed: {e}")
            return False
    
    def _initialize_chrome(self, width: int, height: int) -> bool:
        """Initialize Chrome browser."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            # Note: JavaScript is required for Plotly rendering, so we don't disable it
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument(f'--window-size={width},{height}')
            
            # Get Chrome browser binary path
            chrome_path = self._get_browser_binary_path('chrome')
            if chrome_path and os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
                logger.debug(f"Using Chrome browser at: {chrome_path}")
            
            driver = webdriver.Chrome(options=chrome_options)
            self._browser_driver = driver
            self._browser_name = 'Chrome'
            return True
            
        except Exception as e:
            logger.debug(f"Chrome initialization failed: {e}")
            return False
    
    def _initialize_safari(self, width: int, height: int) -> bool:
        """Initialize Safari browser."""
        try:
            safari_options = SafariOptions()
            driver = webdriver.Safari(options=safari_options)
            self._browser_driver = driver
            self._browser_name = 'Safari'
            return True
            
        except Exception as e:
            logger.debug(f"Safari initialization failed: {e}")
            return False
    
    def _initialize_firefox(self, width: int, height: int) -> bool:
        """Initialize Firefox browser."""
        try:
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--headless')
            firefox_options.add_argument(f'--width={width}')
            firefox_options.add_argument(f'--height={height}')
            
            # Get Firefox browser binary path
            firefox_path = self._get_browser_binary_path('firefox')
            if firefox_path and os.path.exists(firefox_path):
                firefox_options.binary_location = firefox_path
                logger.debug(f"Using Firefox browser at: {firefox_path}")
            
            driver = webdriver.Firefox(options=firefox_options)
            self._browser_driver = driver
            self._browser_name = 'Firefox'
            return True
            
        except Exception as e:
            logger.debug(f"Firefox initialization failed: {e}")
            return False
    
    @contextmanager
    def get_browser(self):
        """
        Context manager to get the browser driver.
        
        Yields:
            WebDriver: The browser driver instance
            
        Raises:
            RuntimeError: If browser is not initialized
        """
        if self._browser_driver is None:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")
        
        try:
            yield self._browser_driver
        except Exception as e:
            logger.error(f"Browser operation failed: {e}")
            # Don't close the browser on error, just log it
            raise
    
    def is_initialized(self) -> bool:
        """Check if browser is initialized."""
        return self._browser_driver is not None
    
    def is_initializing(self) -> bool:
        """Check if browser is currently being initialized."""
        return self._is_initializing
    
    def wait_for_initialization(self, timeout: float = 30.0) -> bool:
        """
        Wait for browser initialization to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if initialization completed successfully, False if timeout or failed
        """
        if self.is_initialized():
            return True
        
        if not self._is_initializing:
            return False
        
        start_time = time.time()
        while self._is_initializing and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        return self.is_initialized()
    
    def get_browser_name(self) -> Optional[str]:
        """Get the name of the initialized browser."""
        return self._browser_name
    
    def get_browser_info(self) -> Dict[str, Any]:
        """Get information about the current browser instance."""
        if not self.is_initialized():
            return {'status': 'not_initialized'}
        
        try:
            return {
                'status': 'initialized',
                'browser_name': self._browser_name,
                'browser_options': self._browser_options,
                'driver_capabilities': self._browser_driver.capabilities if self._browser_driver else None
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_system_browser_info(self) -> Dict[str, Any]:
        """Get information about available system browsers."""
        try:
            system_default = self._detect_system_default_browser()
            available_browsers = {}
            
            for browser_type in ['safari', 'brave', 'chrome', 'firefox']:
                binary_path = self._get_browser_binary_path(browser_type)
                available_browsers[browser_type] = {
                    'available': binary_path is not None and os.path.exists(binary_path),
                    'binary_path': binary_path,
                    'is_default': browser_type == system_default
                }
            
            return {
                'system_default': system_default,
                'available_browsers': available_browsers,
                'platform': platform.system().lower(),
                'detection_method': 'system_commands_and_file_checks'
            }
        except Exception as e:
            return {
                'error': str(e),
                'platform': platform.system().lower()
            }
    
    def reset_browser(self) -> None:
        """Reset the browser instance (close and reinitialize)."""
        if self._browser_driver:
            try:
                self._browser_driver.quit()
            except Exception as e:
                logger.warning(f"Failed to quit browser driver: {e}")
            finally:
                self._browser_driver = None
                self._browser_name = None
        
        # Reinitialize if we have stored options
        if self._browser_options:
            self.initialize_browser(
                width=self._browser_options['width'],
                height=self._browser_options['height'],
                preferred_browser=self._browser_options.get('preferred_browser')
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the browser instance.
        
        Returns:
            Dictionary with health status information
        """
        if not self.is_initialized():
            return {
                'status': 'not_initialized',
                'healthy': False,
                'message': 'Browser not initialized'
            }
        
        try:
            # Try to execute a simple command to check if browser is responsive
            self._browser_driver.current_url
            return {
                'status': 'healthy',
                'healthy': True,
                'browser_name': self._browser_name,
                'message': 'Browser is responsive'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'healthy': False,
                'browser_name': self._browser_name,
                'message': f'Browser health check failed: {str(e)}',
                'error': str(e)
            }
    
    def force_cleanup(self) -> None:
        """Force cleanup of browser resources, even if normal cleanup fails."""
        logger.warning("Force cleaning up browser resources")
        try:
            if self._browser_driver:
                # Try multiple cleanup methods
                try:
                    self._browser_driver.quit()
                except:
                    pass
                try:
                    self._browser_driver.close()
                except:
                    pass
                try:
                    del self._browser_driver
                except:
                    pass
        except Exception as e:
            logger.error(f"Force cleanup failed: {e}")
        finally:
            self._browser_driver = None
            self._browser_name = None
            self._is_initializing = False
    
    def cleanup(self) -> None:
        """Clean up browser resources."""
        if self._browser_driver:
            try:
                logger.info("Cleaning up browser resources")
                self._browser_driver.quit()
            except Exception as e:
                logger.warning(f"Failed to cleanup browser: {e}")
            finally:
                self._browser_driver = None
                self._browser_name = None
                self._is_initializing = False
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


# Global browser manager instance
browser_manager = BrowserManager()
