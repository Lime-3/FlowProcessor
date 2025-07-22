# tests/test_logging.py
# flowproc/tests/test_logging.py::test_setup_logging FAILED   

import logging
import pytest
import os
from pathlib import Path
from typing import Generator

from flowproc.logging_config import setup_logging

@pytest.fixture(autouse=True)
def clean_handlers() -> Generator[None, None, None]:
    """Clean logging handlers after each test."""
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)

@pytest.fixture
def capsys(capsys) -> pytest.CaptureFixture:
    """Fixture for capturing stdout and stderr."""
    return capsys

def test_setup_logging(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test successful logging setup and log writing."""
    assert setup_logging(filemode='a', project_root=tmp_path)

    logging.debug("Test log")
    captured = capsys.readouterr()
    assert "Test log" in captured.err

    log_file = tmp_path / 'data' / 'logs' / 'processing.log'
    if len(logging.getLogger().handlers) > 1:
        logging.getLogger().handlers[1].flush()  # Force flush file handler if exists
    assert log_file.exists()
    with open(log_file) as f:
        content = f.read()
        assert "Test log" in content

def test_setup_logging_error(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test logging setup failure and error logging."""
    with pytest.raises(OSError):
        setup_logging(project_root=tmp_path, simulate_raise=True)

    captured = capsys.readouterr()
    assert "Failed to set up file logging" in captured.err

def test_log_path_resolution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test log path resolution with mock __file__ and env var."""
    monkeypatch.setattr('flowproc.logging_config.__file__', str(tmp_path / 'flowproc' / 'logging_config.py'))

    assert setup_logging(filemode='a')

    expected_log_file = tmp_path / 'flowproc' / 'data' / 'logs' / 'processing.log'
    assert expected_log_file.exists()

    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)

    monkeypatch.setenv('FLOWPROC_LOG_ROOT', str(tmp_path / 'custom'))
    assert setup_logging(filemode='a')
    expected_override = tmp_path / 'custom' / 'data' / 'logs' / 'processing.log'
    assert expected_override.exists()

@pytest.mark.parametrize("filemode", ['a', 'w'])
def test_filemode_variations(filemode: str, tmp_path: Path) -> None:
    """Test different filemodes."""
    assert setup_logging(filemode=filemode, project_root=tmp_path)
    log_file = tmp_path / 'data' / 'logs' / 'processing.log'
    if len(logging.getLogger().handlers) > 1:
        logging.getLogger().handlers[1].flush()
    assert log_file.exists()

def test_max_size_backup(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test log file backup when exceeding max size."""
    log_path = tmp_path / 'data' / 'logs'
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / 'processing.log'
    with open(log_file, 'w') as f:
        f.write('a' * (11 * 1024 * 1024))  # >10MB

    original_size = os.path.getsize(log_file)
    assert original_size > 10 * 1024 * 1024

    assert setup_logging(max_size_mb=10, project_root=tmp_path)
    backups = list(log_path.glob('processing_*.log'))
    assert len(backups) == 1
    captured = capsys.readouterr()
    assert "Log file cleared" in captured.err
    if len(logging.getLogger().handlers) > 1:
        logging.getLogger().handlers[1].flush()
    assert os.path.getsize(log_file) > 0  # Init logs added
    assert os.path.getsize(log_file) < original_size
    with open(backups[0]) as f:
        assert os.path.getsize(backups[0]) == original_size  # Backup preserves size

if __name__ == "__main__":
    pytest.main(['-v'])