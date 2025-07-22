import pytest
import pandas as pd
from pathlib import Path
import logging  # Ensure logging is imported

# Note: Ensure 'flowproc' is a package with __init__.py in /flowproc-project/flowproc/
try:
    from flowproc.visualize import visualize_data
except ImportError as e:
    print(f"Import failed: {e}")
    raise

def test_visualize_data(tmp_path, caplog):
    """Test that visualize_data generates a valid HTML plot file."""
    caplog.set_level(logging.DEBUG)
    csv_file = tmp_path / "test.csv"
    df = pd.DataFrame({
        "SampleID": ["1.1_SP", "1.2_SP", "2.1_SP"],
        "Group": [1, 1, 2],
        "Animal": [1, 2, 1],
        "Freq. of Parent": [10, 20, 30]
    })
    df.to_csv(csv_file, index=False)
    output_html = tmp_path / "plot.html"
    try:
        visualize_data(str(csv_file), str(output_html), metric="Freq. of Parent")
    except Exception as e:
        print(f"Test failed with exception: {e}")
        raise
    assert output_html.exists()
    with open(output_html) as f:
        content = f.read()
        assert '"paper_bgcolor":"#0F0F0F"' in content  # Dark background
        assert '<div class="plotly-graph-div"' in content  # Verify Plotly rendering