import pytest
from flowproc.gui.config_handler import load_last_output_dir, save_last_output_dir
from pathlib import Path

@pytest.fixture
def mock_config(tmp_path):
    config_file = tmp_path / "config.json"
    return config_file

def test_save_load(mock_config, monkeypatch):
    monkeypatch.setattr("flowproc.gui.config_handler.CONFIG_FILE", mock_config)
    save_last_output_dir("/test/dir")
    assert load_last_output_dir() == "/test/dir"