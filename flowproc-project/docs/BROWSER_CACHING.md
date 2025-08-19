# Browser Caching for PDF Export

## Overview

The FlowProcessor application now includes a sophisticated browser caching system that significantly improves performance when exporting multiple PDF files. Instead of creating a new browser instance for each export operation, the system initializes the browser once and reuses it across multiple exports.

## Key Benefits

- **Performance Improvement**: Subsequent PDF exports are significantly faster (typically 2-5x improvement)
- **Resource Efficiency**: Single browser instance reduces memory usage and system overhead
- **Background Initialization**: Browser initializes in background thread, keeping UI responsive
- **Better Reliability**: Improved error handling and automatic recovery from browser failures
- **Multi-format Support**: Cached browser works with PDF, PNG, and SVG exports
- **Automatic Cleanup**: Browser resources are automatically cleaned up on application exit

## Architecture

### Browser Manager (`BrowserManager`)

The `BrowserManager` class implements a singleton pattern that manages the lifecycle of a single browser instance:

- **Initialization**: Automatically detects and initializes the best available browser (Safari, Brave, Chrome, Firefox)
- **Background Initialization**: Supports non-blocking browser initialization in background threads
- **Caching**: Maintains a single browser instance across multiple export operations
- **Health Monitoring**: Provides health checks and status reporting
- **Error Recovery**: Automatically resets browser on critical errors
- **Resource Management**: Handles cleanup and resource management

### PlotlyRenderer Integration

The `PlotlyRenderer` class has been updated to use the cached browser:

- **Automatic Browser Usage**: All export methods automatically use the cached browser
- **Pre-initialization**: Browser is initialized during renderer creation for better performance
- **Error Handling**: Automatic fallback and recovery mechanisms
- **Performance Monitoring**: Built-in performance tracking and reporting

## Usage

### Basic Usage

```python
from flowproc.domain.visualization.plotly_renderer import PlotlyRenderer
import plotly.graph_objects as go

# Create figure
fig = go.Figure(data=go.Scatter(x=[1, 2, 3], y=[1, 4, 2]))

# Create renderer (browser will be initialized automatically in background)
renderer = PlotlyRenderer()

# Export to PDF (browser is cached and reused)
renderer.export_to_pdf(fig, 'output.pdf', width=800, height=600)

# Multiple exports use the same browser instance
renderer.export_to_png(fig, 'output.png', width=800, height=600)
renderer.export_to_svg(fig, 'output.svg', width=800, height=600)
```

### Background Initialization

The browser manager supports background initialization to keep the UI responsive:

```python
from flowproc.domain.visualization.browser_manager import browser_manager

# Start background initialization
browser_manager.initialize_browser(
    width=1200,
    height=800,
    background=True,  # Initialize in background thread
    callback=lambda success: print(f"Browser ready: {success}")
)

# Check initialization status
if browser_manager.is_initializing():
    print("Browser is initializing in background...")
elif browser_manager.is_initialized():
    print("Browser is ready!")
else:
    print("Browser not initialized")

# Wait for initialization to complete (with timeout)
if browser_manager.wait_for_initialization(timeout=30.0):
    print("Browser initialization completed successfully")
else:
    print("Browser initialization timed out")
```

### Advanced Browser Management

```python
from flowproc.domain.visualization.browser_manager import browser_manager

# Initialize browser with specific settings
browser_manager.initialize_browser(
    width=1200, 
    height=800, 
    preferred_browser='chrome'
)

# Check browser status
status = browser_manager.get_browser_info()
print(f"Browser status: {status}")

# Health check
health = browser_manager.health_check()
print(f"Browser health: {health}")

# Reset browser if needed
browser_manager.reset_browser()

# Force cleanup
browser_manager.force_cleanup()
```

### Performance Monitoring

```python
# Get browser status and performance information
browser_status = renderer.get_browser_status()
print(f"Browser status: {browser_status}")

# Check if browser is healthy
health = browser_manager.health_check()
if health['healthy']:
    print("Browser is working correctly")
else:
    print(f"Browser issue: {health['message']}")
```

## Browser Priority

The system automatically selects the best available browser in this order:

1. **Safari** (macOS native, fastest initialization)
2. **Brave** (Chromium-based, good compatibility)
3. **Chrome** (Chromium-based, fallback)
4. **Firefox** (fallback option)

## Error Handling and Recovery

### Automatic Recovery

The system automatically handles common browser issues:

- **Session Errors**: Automatically resets browser on session failures
- **Connection Issues**: Retries operations with error logging
- **Resource Cleanup**: Ensures proper cleanup even on failures

### Manual Recovery

```python
# Reset browser cache
renderer.reset_browser_cache()

# Force browser cleanup
browser_manager.force_cleanup()

# Reinitialize browser
browser_manager.initialize_browser(width=1200, height=800)
```

## Performance Characteristics

### Typical Performance Improvements

- **First Export**: 2-5 seconds (includes browser initialization)
- **Subsequent Exports**: 0.5-1.5 seconds (uses cached browser)
- **Performance Gain**: 2-5x improvement for multiple exports

### Factors Affecting Performance

- **Browser Type**: Safari typically fastest, Firefox slowest
- **Figure Complexity**: Complex plots take longer to render
- **Export Format**: PDF typically slowest, PNG fastest
- **System Resources**: Available memory and CPU affect performance

## Configuration

### Browser Options

```python
# Initialize with specific dimensions
browser_manager.initialize_browser(
    width=1800,      # Browser window width
    height=600,      # Browser window height
    preferred_browser='safari'  # Preferred browser type
)

# Background initialization (recommended for UI applications)
browser_manager.initialize_browser(
    width=1200,
    height=800,
    background=True,  # Initialize in background thread
    callback=lambda success: print(f"Browser ready: {success}")  # Optional callback
)
```

### Export Options

```python
# Export with specific dimensions and scale
renderer.export_to_pdf(
    fig, 
    'output.pdf',
    width=1800,      # Export width
    height=600,      # Export height
    scale=1          # Export scale factor
)
```

## Troubleshooting

### Common Issues

1. **Browser Not Initializing**
   - Check if Selenium is installed: `pip install selenium`
   - Verify browser drivers are available
   - Check system permissions

2. **Slow Performance**
   - Ensure browser is properly cached
   - Check browser health status
   - Consider resetting browser cache

3. **Export Failures**
   - Check browser health
   - Verify figure data is valid
   - Check available disk space

### Debug Information

```python
# Get detailed browser information
browser_info = browser_manager.get_browser_info()
print(f"Browser info: {browser_info}")

# Get renderer status
renderer_status = renderer.get_browser_status()
print(f"Renderer status: {renderer_status}")

# Check browser health
health = browser_manager.health_check()
print(f"Health check: {health}")
```

## Testing

### Run Tests

```bash
# Run comprehensive tests
python test_browser_caching.py

# Run demonstration
python demo_browser_caching.py
```

### Test Coverage

The test suite covers:
- Browser initialization and caching
- Multiple export operations
- Performance improvements
- Error handling and recovery
- Health monitoring
- Resource cleanup

## Integration

### Application Container

The browser manager is automatically registered in the application container:

```python
from flowproc.application.container import container
from flowproc.domain.visualization.browser_manager import browser_manager

# Browser manager is automatically available as a singleton
browser_status = browser_manager.get_browser_info()
```

### GUI Integration

The visualization dialog automatically uses the cached browser for PDF exports, providing seamless performance improvements without user intervention.

## Future Enhancements

Planned improvements include:
- **Browser Pooling**: Multiple browser instances for parallel processing
- **Adaptive Caching**: Dynamic browser selection based on workload
- **Performance Metrics**: Detailed performance tracking and reporting
- **Configuration Persistence**: Save and restore browser preferences

## Support

For issues or questions about the browser caching system:
- Check the troubleshooting section above
- Review browser health and status information
- Run the test suite to verify functionality
- Check system logs for detailed error information
