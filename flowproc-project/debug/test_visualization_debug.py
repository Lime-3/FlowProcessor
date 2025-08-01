#!/usr/bin/env python3
"""
Test script for debugging visualization issues.
"""

import sys
import logging
from pathlib import Path

# Add the flowproc directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flowproc.domain.visualization.unified_service import UnifiedVisualizationService
from flowproc.domain.visualization.config import VisualizationConfig
from flowproc.domain.visualization.models import ProcessedData
from flowproc.domain.parsing import load_and_parse_df

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_visualization_debug():
    """Test visualization debugging functionality."""
    print("🧪 Testing visualization debug...")
    
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
        
        # Create processed data
        processed_data = ProcessedData(
            dataframes=[df],
            metrics=['Freq. of Parent CD4'],
            groups=['Group 1'],
            tissues=['SP'],
            replicate_count=2
        )
        
        # Create configuration
        config = VisualizationConfig(
            metric='Freq. of Parent CD4',
            width=800,
            height=600,
            time_course_mode=True,
            theme='default'
        )
        
        # Create visualization using unified service
        service = UnifiedVisualizationService()
        fig = service.create_flow_cytometry_visualization(processed_data, config.__dict__)
        
        # Check that the figure was created successfully
        assert fig is not None, "Figure should not be None"
        assert hasattr(fig, 'layout'), "Figure should have layout attribute"
        print(f"Visualization created successfully: {fig.layout.width}x{fig.layout.height}")
        
        print("✅ Visualization debug test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Visualization debug test failed: {e}")
        logger.error("Test error", exc_info=True)
        return False
        
    finally:
        # Cleanup
        if csv_path.exists():
            csv_path.unlink()


if __name__ == "__main__":
    print("🚀 Visualization Debug Test Suite")
    print("=" * 50)
    
    success = test_visualization_debug()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 