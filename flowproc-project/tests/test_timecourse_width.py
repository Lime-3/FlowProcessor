#!/usr/bin/env python3
"""
Simple test script to verify that timecourse plots use the correct width.
"""

import sys
import logging
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.visualization.time_plots import create_timecourse_visualization
from flowproc.domain.parsing import load_and_parse_df

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_timecourse_width():
    """Test that timecourse plots use the correct width."""
    print("🧪 Testing timecourse plot width...")
    
    # Create test data
    import pandas as pd
    test_data = pd.DataFrame({
        'SampleID': ['SP_1.1_0h', 'SP_1.2_0h', 'SP_1.1_24h', 'SP_1.2_24h'],
        'Group': [1, 1, 1, 1],
        'Animal': [1, 2, 1, 2],
        'Replicate': [1, 2, 1, 2],
        'Time': [0.0, 0.0, 24.0, 24.0],
        'Freq. of Parent CD4': [10.5, 11.2, 12.1, 12.8]
    })
    
    # Create temporary CSV file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_csv:
        test_data.to_csv(tmp_csv.name, index=False)
        csv_path = Path(tmp_csv.name)
    
    try:
        # Load and parse data
        df, sid_col = load_and_parse_df(csv_path)
        
        # Create visualization using current timecourse module
        fig = create_timecourse_visualization(
            data=df,
            time_column='Time',
            metric='Freq. of Parent CD4',
            width=1200,  # Wide default for timecourse
            height=600
        )
        
        # Check that the figure has the correct width
        assert fig.layout.width == 1200, f"Expected width 1200, got {fig.layout.width}"
        print(f"Timecourse plot width: {fig.layout.width}")
        
        # Test with different width
        fig2 = create_timecourse_visualization(
            data=df,
            time_column='Time',
            metric='Freq. of Parent CD4',
            width=800,
            height=600
        )
        assert fig2.layout.width == 800, f"Expected width 800, got {fig2.layout.width}"
        print(f"Timecourse plot width (800): {fig2.layout.width}")
        
        print("✅ Timecourse plot width test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Timecourse plot width test failed: {e}")
        logger.error("Test error", exc_info=True)
        return False
        
    finally:
        # Cleanup
        if csv_path.exists():
            csv_path.unlink()


def test_default_timecourse_dimensions():
    """Test that default timecourse dimensions are appropriate."""
    print("\n🧪 Testing default timecourse dimensions...")
    
    # Create test data
    import pandas as pd
    test_data = pd.DataFrame({
        'SampleID': ['SP_1.1_0h', 'SP_1.2_0h', 'SP_1.1_24h', 'SP_1.2_24h'],
        'Group': [1, 1, 1, 1],
        'Animal': [1, 2, 1, 2],
        'Replicate': [1, 2, 1, 2],
        'Time': [0.0, 0.0, 24.0, 24.0],
        'Freq. of Parent CD4': [10.5, 11.2, 12.1, 12.8]
    })
    
    # Create temporary CSV file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_csv:
        test_data.to_csv(tmp_csv.name, index=False)
        csv_path = Path(tmp_csv.name)
    
    try:
        # Load and parse data
        df, sid_col = load_and_parse_df(csv_path)
        
        # Create visualization using current timecourse module with default dimensions
        fig = create_timecourse_visualization(
            data=df,
            time_column='Time',
            metric='Freq. of Parent CD4'
        )
        
        # Check that default dimensions are reasonable for timecourse
        assert fig.layout.width >= 600, f"Default width too small: {fig.layout.width}"
        assert fig.layout.height >= 300, f"Default height too small: {fig.layout.height}"
        print(f"Default timecourse dimensions: {fig.layout.width}x{fig.layout.height}")
        
        print("✅ Default timecourse dimensions test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Default timecourse dimensions test failed: {e}")
        logger.error("Test error", exc_info=True)
        return False
        
    finally:
        # Cleanup
        if csv_path.exists():
            csv_path.unlink()


if __name__ == "__main__":
    print("🚀 Timecourse Width Test Suite")
    print("=" * 50)
    
    success = True
    success &= test_timecourse_width()
    success &= test_default_timecourse_dimensions()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 