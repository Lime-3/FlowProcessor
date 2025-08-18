# PDF Export in FlowProcessor

## Overview

FlowProcessor uses **Selenium-based browser automation** for PDF export rather than native Plotly export methods. This approach was chosen after discovering that Plotly's native export methods (including Kaleido) also rely on Chrome internally, but with less control and transparency.

## Why Selenium Instead of Native Export?

### The Problem with "Native" Export
- **Kaleido**: Plotly's recommended PDF export library actually uses Chrome internally
- **Hidden dependencies**: Users don't know Chrome is being used
- **Less control**: Can't customize browser behavior or handle errors gracefully
- **Platform issues**: Chrome dependencies can cause problems on different systems

### Benefits of Selenium Approach
- **Transparent**: Clear what's happening under the hood
- **Controllable**: Full control over browser options and behavior
- **Flexible**: Can use different browsers (Safari, Chrome, Firefox)
- **Debuggable**: Easy to troubleshoot and optimize
- **Consistent**: Same behavior across different platforms

## How It Works

### 1. Browser Detection
The system automatically detects available browsers in order of preference:
1. **Brave** (macOS preferred) - Chromium-based, fastest and most reliable
2. **Safari** (macOS native) - Good performance, built-in support
3. **Chrome** - Most reliable, good performance
4. **Firefox** - Good fallback option

**Note**: Brave browser is automatically detected and prioritized on macOS systems, providing the best performance and reliability for PDF export.

### 2. Export Process
```python
# 1. Create temporary HTML file with Plotly figure
# 2. Launch appropriate browser in headless mode
# 3. Load HTML file in browser
# 4. Wait for Plotly to render completely
# 5. Use Chrome DevTools Protocol (CDP) to print to PDF
# 6. Save PDF data to file
# 7. Clean up temporary files and browser
```

### 3. Browser Optimization
Each browser is configured with optimized options:
- **Headless mode**: No visible browser window
- **Disabled features**: GPU, extensions, images for faster rendering
- **Custom viewport**: Matches desired PDF dimensions
- **Memory optimization**: Minimal resource usage

## Configuration

### Required Dependencies
```bash
pip install selenium>=4.15.0
```

### Browser Drivers
- **Brave**: Automatically detected on macOS, no additional driver needed
- **Safari**: Built into macOS, no additional driver needed
- **Chrome**: Install ChromeDriver or use system Chrome
- **Firefox**: Install GeckoDriver

### Brave Browser Benefits
- **Automatic detection**: No manual configuration required
- **Chromium-based**: Full compatibility with Chrome WebDriver
- **Performance**: Optimized for modern web standards
- **Privacy**: Built-in ad blocking and privacy features
- **macOS native**: Seamless integration with your system

**macOS users**: Brave is automatically detected at `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser` and will be used as the primary PDF export method.

### Environment Variables (Optional)
```bash
# Chrome driver path
export CHROMEDRIVER_PATH=/path/to/chromedriver

# Firefox driver path  
export GECKODRIVER_PATH=/path/to/geckodriver
```

## Usage

### Basic PDF Export
```python
from flowproc.domain.visualization.plotly_renderer import PlotlyRenderer

renderer = PlotlyRenderer()
fig = create_your_plotly_figure()

# Export to PDF
renderer.export_to_pdf(fig, "output.pdf", width=1200, height=800)
```

### Check Capabilities
```python
capabilities = renderer.check_pdf_capabilities()
print(f"Available browsers: {capabilities['browsers']}")
```

### Custom Dimensions
```python
# Custom size and scale
renderer.export_to_pdf(
    fig, 
    "output.pdf", 
    width=1800,      # Width in pixels
    height=1200,     # Height in pixels
    scale=2          # Scale factor (1 = 100%, 2 = 200%)
)
```

## Error Handling

### Common Issues
1. **No browser drivers**: Install appropriate browser drivers
2. **Selenium not available**: `pip install selenium`
3. **Browser launch failure**: Check browser installation and permissions
4. **PDF generation failure**: Check figure validity and dimensions

### Fallback Behavior
- Automatically tries different browsers
- Provides detailed error messages
- Graceful degradation when possible

## Performance Considerations

### Optimization Tips
- **Fixed dimensions**: Avoid responsive layouts for PDF export
- **Minimal data**: Export only necessary traces
- **Browser selection**: Safari is fastest on macOS, Chrome on other platforms
- **Headless mode**: Always enabled for automation

### Memory Usage
- **Temporary files**: Automatically cleaned up
- **Browser instances**: Properly terminated after each export
- **Resource limits**: Configured for minimal resource consumption

## Troubleshooting

### Debug Mode
Enable debug logging to see detailed export process:
```python
import logging
logging.getLogger('flowproc.domain.visualization.plotly_renderer').setLevel(logging.DEBUG)
```

### Test Export
Use the test script to verify your setup:
```bash
python test_pdf_export.py
```

### Browser Issues
- **Safari**: Ensure "Allow Remote Automation" is enabled in Develop menu
- **Chrome**: Check ChromeDriver version compatibility
- **Firefox**: Verify GeckoDriver installation
- **Brave**: 
  - Ensure Brave is installed in the default location
  - Check that Brave can be launched from terminal: `/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --version`
  - If Brave is in a custom location, the system will fall back to Chrome or Safari

## Future Improvements

### Potential Enhancements
1. **Parallel export**: Multiple PDFs simultaneously
2. **Template support**: Predefined PDF layouts
3. **Quality options**: DPI and compression settings
4. **Batch processing**: Export multiple figures at once

### Alternative Approaches
- **WeasyPrint**: Pure Python PDF generation (limited Plotly support)
- **Playwright**: Modern browser automation (replacement for Selenium)
- **Custom renderer**: Direct PDF generation without browser dependency

## Conclusion

The Selenium-based approach provides the best balance of:
- **Reliability**: Consistent results across platforms
- **Control**: Full control over the export process
- **Transparency**: Clear understanding of what's happening
- **Flexibility**: Support for multiple browsers and configurations

While it may seem more complex than "native" export, it's actually more robust and maintainable in the long run.
