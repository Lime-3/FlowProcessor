# Visualization Dialog Layout Update

## 🎯 **User Request**

The user wanted the visualization dialog to show **options/settings on top** and the **plot/graph below**, so they can see the visualization update in real-time as they change the settings, rather than having separate tabs.

## ✅ **New Layout Implemented**

### **Layout Structure**
```
┌─────────────────────────────────────────────────────────────┐
│                    OPTIONS SECTION (TOP)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Basic       │  │ Advanced    │  │ Data        │         │
│  │ Options     │  │ Options     │  │ Information │         │
│  │             │  │             │  │             │         │
│  │ • Metric    │  │ • Tissue    │  │ • Shape     │         │
│  │ • Theme     │  │ • Subpop    │  │ • Time Data │         │
│  │ • Mode      │  │ • Display   │  │ • Metrics   │         │
│  │ • Size      │  │ • Labels    │  │ • Tissues   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
│                                                             │
│                    LIVE PREVIEW SECTION                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                                                         │ │
│  │              INTERACTIVE PLOT                           │ │
│  │              (Updates in real-time)                     │ │
│  │                                                         │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
│                    [Save] [Cancel]                         │
└─────────────────────────────────────────────────────────────┘
```

### **Key Features**

#### **1. Options Section (Top)**
- **Scrollable horizontal layout** with maximum height of 300px
- **Three organized groups**:
  - **Basic Options**: Metric, theme, time course mode, dimensions
  - **Advanced Options**: Tissue/subpopulation filters, display options, custom labels
  - **Data Information**: Real-time data analysis results

#### **2. Live Preview Section (Bottom)**
- **QWebEngineView** for displaying interactive Plotly plots
- **Real-time updates** as options change
- **500ms delay** to avoid too frequent updates
- **Error handling** with user-friendly error display

#### **3. Real-time Updates**
- **Automatic plot regeneration** when any option changes
- **Debounced updates** (500ms delay) for performance
- **Immediate visual feedback** for all parameter changes

## 🔧 **Technical Implementation**

### **Layout Components**
```python
def _setup_ui(self):
    """Set up the user interface components."""
    layout = QVBoxLayout(self)
    
    # Options section on top
    self._setup_options_section(layout)
    
    # Plot section below
    self._setup_plot_section(layout)
    
    # Buttons at bottom
    self._setup_buttons(layout)
```

### **Options Section**
```python
def _setup_options_section(self, parent_layout: QVBoxLayout):
    """Set up the options section on top."""
    options_scroll = QScrollArea()
    options_scroll.setMaximumHeight(300)  # Fixed height
    
    options_widget = QWidget()
    options_layout = QHBoxLayout(options_widget)  # Horizontal layout
    
    # Three groups side by side
    basic_group = self._create_basic_options_group()
    advanced_group = self._create_advanced_options_group()
    info_group = self._create_data_info_group()
    
    options_layout.addWidget(basic_group)
    options_layout.addWidget(advanced_group)
    options_layout.addWidget(info_group)
```

### **Live Preview Section**
```python
def _setup_plot_section(self, parent_layout: QVBoxLayout):
    """Set up the plot section below."""
    # Web view for plot
    self.web_view = QWebEngineView()
    self.web_view.setMinimumHeight(400)
    
    # Load initial loading message
    self.web_view.setHtml("Loading visualization...")
```

### **Real-time Updates**
```python
def _on_option_changed(self):
    """Handle option changes - trigger delayed plot update."""
    if self.update_timer:
        self.update_timer.start(500)  # 500ms delay

def _update_plot(self):
    """Update the plot with current options."""
    # Create new visualization with current options
    fig = create_visualization(...)
    
    # Load in web view
    self.web_view.load(QUrl.fromLocalFile(str(self.temp_html_file)))
```

## 🎨 **User Experience Improvements**

### **Before (Tabbed Interface)**
- ❌ **Separate tabs** for options and preview
- ❌ **No real-time feedback** when changing options
- ❌ **Manual preview button** required
- ❌ **Smaller dialog** (600x500)

### **After (Split Layout)**
- ✅ **Options always visible** on top
- ✅ **Live preview** updates automatically
- ✅ **Immediate visual feedback** for all changes
- ✅ **Larger dialog** (1200x800) for better visibility
- ✅ **Scrollable options** to fit all controls

### **Real-time Features**
- ✅ **Metric changes** → Plot updates immediately
- ✅ **Theme changes** → Visual style updates
- ✅ **Dimension changes** → Plot size adjusts
- ✅ **Filter changes** → Data filtering applied
- ✅ **Label changes** → Axis labels update

## 📊 **Performance Optimizations**

### **Debounced Updates**
- **500ms delay** between option changes and plot updates
- **Prevents excessive** plot regeneration
- **Smooth user experience** without lag

### **Temporary File Management**
- **Automatic cleanup** of temporary HTML files
- **Memory efficient** plot generation
- **Error handling** for file operations

### **Background Processing**
- **Data analysis** in separate thread
- **Non-blocking UI** during analysis
- **Progress feedback** during loading

## 🎯 **Benefits**

### **For Users**
- ✅ **See changes immediately** as they adjust settings
- ✅ **No need to switch tabs** or click preview buttons
- ✅ **Better understanding** of how options affect the plot
- ✅ **Faster workflow** with immediate feedback
- ✅ **More intuitive** interface design

### **For Developers**
- ✅ **Cleaner code structure** with separated concerns
- ✅ **Reusable components** for different option groups
- ✅ **Easy to extend** with new options
- ✅ **Better error handling** with visual feedback
- ✅ **Performance optimized** with debounced updates

## 🔮 **Future Enhancements**

### **Potential Improvements**
1. **Splitter controls** to adjust options/plot ratio
2. **Multiple plot views** (side-by-side comparison)
3. **Plot export options** directly from dialog
4. **Undo/redo** for option changes
5. **Preset management** for common configurations

### **Extension Points**
1. **New option groups** can be easily added
2. **Custom plot types** can be integrated
3. **Advanced filtering** options can be expanded
4. **Theme customization** can be enhanced

## ✅ **Conclusion**

The new **split layout** with **options on top** and **live preview below** provides a much better user experience:

- **Immediate visual feedback** for all parameter changes
- **No need to switch between tabs** or click preview buttons
- **Better understanding** of how options affect the visualization
- **More intuitive and efficient** workflow
- **Professional appearance** with modern UI design

This layout change transforms the visualization dialog from a **configuration tool** into an **interactive visualization workspace** where users can experiment with different settings and see the results immediately. 