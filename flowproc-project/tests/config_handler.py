import pytest
from flowproc.presentation.gui.config_handler import load_last_output_dir, save_last_output_dir
from pathlib import Path

@pytest.fixture
def mock_config(tmp_path):
    config_file = tmp_path / "config.json"
    return config_file

def test_save_load(mock_config, monkeypatch, tmp_path):
    monkeypatch.setattr("flowproc.presentation.gui.config_handler.CONFIG_FILE", mock_config)
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    save_last_output_dir(str(test_dir))
    assert load_last_output_dir() == str(test_dir)