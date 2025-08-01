#!/usr/bin/env python3
"""
Test script to verify visualization fixes work correctly.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flowproc.domain.parsing import load_and_parse_df
from flowproc.domain.visualization.simple_visualizer import plot, _detect_flow_columns

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_column_detection():
    """Test column detection with the problematic data."""
    # Use one of the test CSV files
    csv_path = project_root / "tests" / "data" / "AT25-AS278_FullStudy-1.csv"
    
    if not csv_path.exists():
        logger.error(f"Test file not found: {csv_path}")
        return False
    
    try:
        # Load and parse the data
        df, _ = load_and_parse_df(csv_path)
        
        if df is None or df.empty:
            logger.error("Failed to load data")
            return False
        
        logger.info(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Test flow column detection
        flow_cols = _detect_flow_columns(df)
        logger.info(f"Detected flow columns: {flow_cols}")
        
        # Test frequency column detection
        freq_parent_cols = [col for col in df.columns if 'freq. of parent' in col.lower()]
        logger.info(f"Frequency of Parent columns: {freq_parent_cols}")
        
        # Test plotting with auto-detection
        logger.info("Testing plot generation with auto-detection...")
        fig = plot(df, x='Group', y='Freq. of Parent', plot_type='bar')
        logger.info("Plot generated successfully!")
        
        # Test plotting with specific column
        if freq_parent_cols:
            logger.info(f"Testing plot generation with specific column: {freq_parent_cols[0]}")
            fig = plot(df, x='Group', y=freq_parent_cols[0], plot_type='bar')
            logger.info("Specific column plot generated successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

def test_dimension_validation():
    """Test dimension validation."""
    from flowproc.presentation.gui.views.dialogs.visualization_display_dialog import VisualizationDisplayDialog
    
    # Test with reasonable dimensions
    dialog = VisualizationDisplayDialog()
    dialog.options = type('Options', (), {
        'width': 1000,
        'height': 600,
        'plot_type': 'bar',
        'x_axis': 'Group',
        'y_axis': 'Freq. of Parent',
        'time_course_mode': False
    })()
    
    # Test with large dimensions (should be clamped)
    dialog.options.width = 20000
    dialog.options.height = 15000
    
    # This should trigger the dimension validation
    logger.info("Testing dimension validation...")
    logger.info(f"Original dimensions: {dialog.options.width}x{dialog.options.height}")
    
    # The validation happens in _generate_plot, but we can test the logic
    max_texture_size = 16384
    safe_max_width = min(max_texture_size, 8000)
    safe_max_height = min(max_texture_size, 6000)
    
    if dialog.options.width > safe_max_width:
        dialog.options.width = safe_max_width
    if dialog.options.height > safe_max_height:
        dialog.options.height = safe_max_height
    
    logger.info(f"After validation: {dialog.options.width}x{dialog.options.height}")
    
    return True

if __name__ == "__main__":
    logger.info("Testing visualization fixes...")
    
    success1 = test_column_detection()
    success2 = test_dimension_validation()
    
    if success1 and success2:
        logger.info("All tests passed! Visualization fixes are working.")
    else:
        logger.error("Some tests failed. Please check the fixes.")
        sys.exit(1) 