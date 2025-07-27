"""Test suite for GUI functionality."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Need to define fixtures or import the function being tested
@pytest.fixture
def temp_csv(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("SampleID,Data\nSP_1.1,10\nSP_1.2,20")
    return csv_file

@pytest.fixture  
def mock_home(tmp_path):
    """Create a mock home directory."""
    return tmp_path

def visualize_selected():
    """Mock function - would need to import from actual GUI module."""
    pass

def test_visualize_selected_permission_denied(qapp, temp_csv, mock_home, monkeypatch):
    global last_csv
    last_csv = temp_csv
    monkeypatch.setattr("pathlib.Path.home", lambda: mock_home)
    temp_html = mock_home / ".flowproc" / "temp" / "plot.html"

    mock_visualize = MagicMock()
    def create_file(csv_path, output_html, **kwargs):
        raise PermissionError("Permission denied")
    mock_visualize.side_effect = create_file
    monkeypatch.setattr("flowproc.domain.visualization.visualize.visualize_data", mock_visualize)

    mock_window = MagicMock()
    mock_msgbox = MagicMock()
    monkeypatch.setattr("flowproc.presentation.gui.main.window", mock_window)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.critical", mock_msgbox)
    monkeypatch.setattr("flowproc.presentation.gui.main.visualize_combo", MagicMock(currentText=MagicMock(return_value="Freq. of Parent")))
    monkeypatch.setattr("flowproc.presentation.gui.main.time_course_checkbox", MagicMock(isChecked=MagicMock(return_value=False)))
    monkeypatch.setattr("flowproc.presentation.gui.main.USER_REPLICATES", [1, 2, 3])
    monkeypatch.setattr("flowproc.presentation.gui.main.AUTO_PARSE_GROUPS", True)
    monkeypatch.setattr("flowproc.presentation.gui.main.USER_GROUP_LABELS", [])

    visualize_selected()
    assert mock_msgbox.called
    assert "Permission denied" in mock_msgbox.call_args[0][2]