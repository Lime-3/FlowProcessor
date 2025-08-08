#!/usr/bin/env python3
"""
Test script to verify individual timepoint plotting with real test data.
"""

import sys
import pandas as pd
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flowproc.domain.visualization import plot
    print("✅ Imports successful")
    
    # Use existing test data with time information
    test_data_path = Path("tests/data/test_time_data.csv")
    
    if not test_data_path.exists():
        print(f"❌ Test data file not found: {test_data_path}")
        sys.exit(1)
    
    print(f"📁 Using test data: {test_data_path}")
    
    # Test individual timepoint plotting with real data
    plot_types = ['bar', 'box']
    
    for plot_type in plot_types:
        print(f"\n🧪 Testing {plot_type} plot with individual timepoints...")
        
        try:
            # Create individual timepoint plots
            fig = plot(
                data=str(test_data_path),
                plot_type=plot_type,
                individual_timepoints=True,
                save_html=f"test_real_data_individual_timepoints_{plot_type}.html"
            )
            
            print(f"✅ {plot_type} plot created successfully")
            print(f"📊 Figure type: {type(fig)}")
            
            # Check if the figure has subplots (indicating multiple timepoints)
            if hasattr(fig, 'layout') and hasattr(fig.layout, 'grid'):
                grid = fig.layout.grid
                print(f"📊 Grid layout: {grid.rows} rows")
                
                # Check for multiple axes (indicating subplots)
                x_axes = [key for key in dir(fig.layout) if key.startswith('xaxis')]
                y_axes = [key for key in dir(fig.layout) if key.startswith('yaxis')]
                
                print(f"📊 X-axes found: {len(x_axes)}")
                print(f"📊 Y-axes found: {len(y_axes)}")
                
                if len(x_axes) > 1 or len(y_axes) > 1:
                    print(f"✅ Multiple plots detected: {len(x_axes)} x-axes, {len(y_axes)} y-axes")
                    print("✅ Individual timepoint plots are being generated correctly!")
                else:
                    print("❌ Only single plot generated, expected multiple plots")
            else:
                print("❌ No subplot layout found")
                
        except Exception as e:
            print(f"❌ Error creating {plot_type} plot: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n🎉 Individual timepoint plotting test with real data completed!")
    print("📁 Check the generated HTML files to see the individual timepoint plots")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 