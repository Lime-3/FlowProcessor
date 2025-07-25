from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator
import pytest
import pandas as pd
from unittest.mock import Mock

from flowproc.application.container import Container
from flowproc.core.models import ProcessingConfig
from flowproc.infrastructure.config.settings import FileConfigManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_csv_data() -> pd.DataFrame:
    """Sample CSV data for testing."""
    return pd.DataFrame({
        'SampleID': [
            'SP_A1_1.1.fcs', 'SP_A1_1.2.fcs', 'SP_A2_2.1.fcs', 'SP_A2_2.2.fcs',
            'WB_B1_1.1.fcs', 'WB_B1_1.2.fcs', 'WB_B2_2.1.fcs', 'WB_B2_2.2.fcs'
        ],
        'Freq. of Parent CD4+': [10.5, 11.2, 15.3, 14.8, 8.9, 9.1, 12.4, 11.9],
        'Freq. of Parent CD8+': [5.2, 5.8, 7.1, 6.9, 4.1, 4.3, 6.2, 5.9],
        'Count CD4+': [1250, 1300, 1800, 1750, 980, 1020, 1400, 1350],
        'Count CD8+': [620, 680, 850, 820, 450, 480, 720, 690]
    })


@pytest.fixture
def sample_csv_file(temp_dir: Path, sample_csv_data: pd.DataFrame) -> Path:
    """Create a sample CSV file for testing."""
    csv_path = temp_dir / "sample_data.csv"
    sample_csv_data.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def processing_config(temp_dir: Path, sample_csv_file: Path) -> ProcessingConfig:
    """Sample processing configuration."""
    return ProcessingConfig(
        input_paths=[sample_csv_file],
        output_dir=temp_dir / "output",
        time_course_mode=False,
        auto_parse_groups=True,
        max_workers=2
    )


@pytest.fixture
def mock_container() -> Container:
    """Mock dependency injection container."""
    container = Container()
    
    # Replace services with mocks
    mock_parser = Mock()
    mock_processor = Mock()
    mock_exporter = Mock()
    mock_renderer = Mock()
    mock_config_manager = Mock(spec=FileConfigManager)
    
    container.register_singleton('DataParser', mock_parser)
    container.register_singleton('DataProcessor', mock_processor)
    container.register_singleton('DataExporter', mock_exporter)
    container.register_singleton('VisualizationRenderer', mock_renderer)
    container.register_singleton('ConfigurationManager', mock_config_manager)
    
    return container


@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )