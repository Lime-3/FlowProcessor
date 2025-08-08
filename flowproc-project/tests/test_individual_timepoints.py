#!/usr/bin/env python3
"""
Test script to verify that individual timepoint plotting works correctly.
"""

import sys
import pandas as pd
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flowproc.domain.visualization import plot
    print("✅ Imports successful")
    
    # Create test data with multiple timepoints and cell types
    test_data = pd.DataFrame({
        'SampleID': [
            'AT25-AS001-Control-0', 'AT25-AS002-Control-24', 'AT25-AS003-Control-48',
            'AT25-AS004-Treatment-0', 'AT25-AS005-Treatment-24', 'AT25-AS006-Treatment-48'
        ],
        'Group': ['Control', 'Control', 'Control', 'Treatment', 'Treatment', 'Treatment'],
        'Time': [0, 24, 48, 0, 24, 48],
        'Day': ['Day 0', 'Day 1', 'Day 2', 'Day 0', 'Day 1', 'Day 2'],
        'Tissue': ['Liver', 'Liver', 'Liver', 'Liver', 'Liver', 'Liver'],
        'CD4+ T cells | Freq. of Parent (%)': [15.2, 18.5, 22.1, 12.8, 25.3, 28.7],
        'CD8+ T cells | Freq. of Parent (%)': [8.4, 10.2, 12.8, 7.9, 14.5, 16.2],
        'B cells | Freq. of Parent (%)': [25.6, 28.9, 32.1, 22.4, 35.7, 38.9],
        'NK cells | Freq. of Parent (%)': [5.2, 6.8, 8.4, 4.9, 9.2, 10.5]
    })
    
    print(f"📊 Test data created with {len(test_data)} rows")
    print(f"📊 Timepoints: {sorted(test_data['Time'].unique())}")
    print(f"📊 Groups: {sorted(test_data['Group'].unique())}")
    
    # Test different plot types with individual timepoints
    plot_types = ['bar', 'box', 'scatter']
    
    for plot_type in plot_types:
        print(f"\n🧪 Testing {plot_type} plot with individual timepoints...")
        
        try:
            # Create individual timepoint plots
            fig = plot(
                data=test_data,
                plot_type=plot_type,
                individual_timepoints=True,
                selected_cell_types=['CD4+ T cells', 'CD8+ T cells'],
                save_html=f"test_individual_timepoints_{plot_type}.html"
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
    
    print("\n🎉 Individual timepoint plotting test completed!")
    print("📁 Check the generated HTML files to see the individual timepoint plots")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 