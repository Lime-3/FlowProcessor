# GUI Folder Structure

This document describes the organized folder structure for the GUI module of the Flow Cytometry Processor application.

## Overview

The GUI module follows a clean architecture pattern with clear separation of concerns:

- **Controllers**: Handle business logic and coordinate between views and domain services
- **Views**: User interface components and widgets
- **Workers**: Background processing and validation tasks
- **Utilities**: Helper functions and configuration management

## Directory Structure

```
flowproc/presentation/gui/
├── __init__.py                 # Main GUI package exports
├── main.py                     # GUI entry point
├── config_handler.py           # Configuration management
├── validators.py               # Input validation utilities
├── visualizer.py               # Visualization utilities
├── processor.py                # Processing utilities
│
├── controllers/                # Business logic controllers
│   ├── __init__.py
│   ├── main_controller.py      # Main application controller
│   └── processing_controller.py # Processing workflow controller
│
├── views/                      # User interface components
│   ├── __init__.py
│   ├── main_window.py          # Main application window
│   │
│   ├── widgets/                # Custom widget components
│   │   ├── __init__.py
│   │   ├── drop_line_edit.py   # Drag-and-drop file input
│   │   └── progress_widget.py  # Enhanced progress display
│   │
│   └── dialogs/                # Modal dialog windows
│       ├── __init__.py
│       └── preview_dialog.py   # CSV file preview dialog
│
└── workers/                    # Background processing workers
    ├── __init__.py
    ├── processing_worker.py    # File processing worker
    └── validation_worker.py    # Input validation worker
```

## Component Descriptions

### Controllers

#### MainController
- Coordinates between the main window and domain services
- Handles input validation and processing coordination
- Manages error handling and state management
- Provides signals for UI updates

#### ProcessingController
- Manages the complete processing workflow
- Handles data parsing, processing, and export
- Coordinates between different domain services
- Provides detailed processing feedback

### Views

#### MainWindow
- Main application interface
- Contains all user input controls
- Displays processing progress and results
- Handles user interactions

#### Widgets

##### DropLineEdit
- Custom line edit widget with drag-and-drop support
- Accepts CSV files and directories
- Provides visual feedback for drag operations

##### ProgressWidget
- Enhanced progress display with time estimates
- Shows status messages and processing details
- Includes cancel functionality
- Provides visual styling and animations

#### Dialogs

##### PreviewDialog
- Modal dialog for previewing CSV files
- Shows file statistics and sample data
- Allows file selection for processing
- Provides background loading with progress indication

### Workers

#### ProcessingWorker
- Background thread for file processing operations
- Provides progress updates and status messages
- Supports cancellation and pausing
- Handles thread-safe operations

#### ValidationWorker
- Background validation of user inputs
- Validates files, directories, and processing options
- Provides detailed error and warning messages
- Supports cancellation of validation operations

### Utilities

#### config_handler.py
- Manages application configuration
- Handles saving and loading of user preferences
- Provides default configuration values

#### validators.py
- Input validation utilities
- File format validation
- Processing option validation

#### visualizer.py
- Data visualization utilities
- Chart generation and display
- Plot customization options

#### processor.py
- Processing utility functions
- Data transformation helpers
- Export functionality

## Architecture Benefits

1. **Separation of Concerns**: Clear separation between UI, business logic, and background processing
2. **Maintainability**: Organized structure makes it easy to locate and modify components
3. **Testability**: Controllers and workers can be tested independently
4. **Scalability**: Easy to add new views, controllers, or workers
5. **Reusability**: Widgets and dialogs can be reused across the application

## Usage Examples

### Creating the Main Window
```python
from flowproc.presentation.gui import MainWindow, MainController

# Create the main window
main_window = MainWindow()

# Create and connect the controller
controller = MainController(main_window)

# Show the window
main_window.show()
```

### Using Custom Widgets
```python
from flowproc.presentation.gui import DropLineEdit, ProgressWidget

# Create drag-and-drop input
input_widget = DropLineEdit()

# Create progress widget
progress_widget = ProgressWidget()
progress_widget.start_progress("Processing files...")
```

### Background Processing
```python
from flowproc.presentation.gui import ProcessingWorker, ValidationWorker

# Create processing worker
worker = ProcessingWorker()
worker.progress_updated.connect(self.update_progress)
worker.processing_completed.connect(self.on_completion)
worker.start_processing(input_paths, output_dir, options)
```

## Migration Notes

The new structure maintains backward compatibility while providing a more organized architecture. Existing code can be gradually migrated to use the new controllers and workers for better separation of concerns. 