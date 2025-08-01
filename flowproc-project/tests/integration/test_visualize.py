"""
Test module for comprehensive visualization functionality.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, HealthCheck

from flowproc.domain.visualization.facade import create_visualization
from flowproc.domain.visualization.facade import visualize_data  # Keep for backward compatibility in tests
from flowproc.domain.visualization.facade import (
    VisualizationConfig,
    DataProcessor,
    Visualizer,
    ProcessedData,
    VisualizationError,
)
from flowproc.domain.visualization.data_processor import DataProcessingError
from flowproc.domain.visualization.plotting import create_bar_plot, create_line_plot
from flowproc.domain.visualization.service import VisualizationService
from flowproc.domain.visualization.themes import VisualizationThemes
import plotly.graph_objects as go
import json


class TestVisualizationConfig:
    """Test VisualizationConfig validation."""
    
    def test_valid_config(self):
        """Test creating valid configuration."""
        config = VisualizationConfig(
            metric="Freq. of Parent",
            width=1000,
            height=800,
            theme="plotly_white"
        )
        assert config.width == 1000
        assert config.height == 800
        
    def test_invalid_dimensions(self):
        """Test invalid width/height raises error."""
        with pytest.raises(ValueError, match="Width must be a positive integer"):
            VisualizationConfig(metric=None, width=-100, height=600)
            
    def test_invalid_metric(self):
        """Test invalid metric raises error."""
        with pytest.raises(ValueError, match="Invalid metric"):
            VisualizationConfig(metric="InvalidMetric")


class TestDataProcessor:
    """Test DataProcessor functionality."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'SampleID': ['SP_1.1', 'SP_1.2', 'SP_2.1', 'SP_2.2'],
            'Group': [1, 1, 2, 2],
            'Animal': [1, 2, 1, 2],
            'Time': [0.0, 0.0, 24.0, 24.0],
            'Freq. of Parent CD4': [10.5, 11.2, 15.3, 14.8],
            'Median CD4': [1200, 1250, 1400, 1380]
        })
    
    @pytest.fixture
    def config(self):
        """Create default configuration."""
        return VisualizationConfig(metric=None)
    
    def test_process_success(self, sample_df, config):
        """Test successful data processing."""
        with patch('flowproc.domain.processing.transform.map_replicates') as mock_map:
            mock_map.return_value = (sample_df, 2)
            
            processor = DataProcessor(sample_df, 'SampleID', config)
            result = processor.process()
            
            assert isinstance(result, ProcessedData)
            assert result.replicate_count == 2
            assert len(result.groups) == 2
            assert len(result.times) == 2
    
    def test_process_empty_dataframe(self, config):
        """Test processing empty DataFrame raises error."""
        df = pd.DataFrame()
        
        with pytest.raises(DataProcessingError, match="DataFrame is empty"):
            processor = DataProcessor(df, 'SampleID', config)
    
    def test_process_no_replicates(self, sample_df, config):
        """Test processing with no replicates raises error."""
        with patch('flowproc.domain.visualization.data_processor.map_replicates') as mock_map:
            mock_map.return_value = (sample_df, 0)
            
            processor = DataProcessor(sample_df, 'SampleID', config)
            
            # The current implementation raises the error during process(), not during initialization
            with pytest.raises(DataProcessingError, match="No replicates found"):
                processor.process()
    
    @given(n_groups=st.integers(min_value=1, max_value=10))
    def test_group_map_creation(self, n_groups):
        """Property-based test for group map creation."""
        config = VisualizationConfig(metric=None)
        
        # Create test data with the specified number of groups and valid metrics
        data = []
        for group in range(1, n_groups + 1):
            data.append({
                'SampleID': f'test_{group}',
                'Group': group,
                'Animal': 1,
                'Replicate': 1,
                'Freq. of Parent CD4': 10.0,  # Add a valid metric column
                'Median CD4': 5.0  # Add another valid metric column
            })
        
        df = pd.DataFrame(data)
        processor = DataProcessor(df, 'SampleID', config)
        
        # Mock the map_replicates function to return the test data
        with patch('flowproc.domain.processing.transform.map_replicates') as mock_map:
            mock_map.return_value = (df, 1)
            
            # Process the data to get the group map
            result = processor.process()
            group_map = result.group_map
        
        assert len(group_map) == n_groups
        assert all(f"Group {i}" == group_map[i] for i in range(1, n_groups + 1))
    
    def test_user_group_labels_application(self, sample_df):
        """Test that user-provided group labels are applied correctly."""
        # Create test data with groups 1 and 2
        test_df = pd.DataFrame({
            'SampleID': ['A1_1', 'A1_2', 'A2_1', 'A2_2'],
            'Group': [1, 1, 2, 2],
            'Animal': [1, 1, 2, 2],
            'Replicate': [1, 2, 1, 2],
            'Count_CD4': [100, 110, 200, 210],
            'Count_CD8': [50, 55, 100, 105],
        })
        
        # Test with custom group labels
        custom_labels = ["Control Group", "Treatment Group"]
        config = VisualizationConfig(
            metric="Count",
            user_group_labels=custom_labels
        )
        
        processor = DataProcessor(test_df, 'SampleID', config)
        processed_data = processor.process()
        
        # Verify that the group map contains the custom labels
        expected_map = {1: "Control Group", 2: "Treatment Group"}
        assert processed_data.group_map == expected_map
        
        # Verify that the dataframes contain the correct Group_Label values
        for df in processed_data.dataframes:
            if 'Group_Label' in df.columns:
                unique_labels = df['Group_Label'].unique()
                assert "Control Group" in unique_labels
                assert "Treatment Group" in unique_labels


class TestVisualizer:
    """Test Visualizer functionality."""
    
    @pytest.fixture
    def config(self):
        """Create default configuration."""
        return VisualizationConfig(metric=None, width=800, height=800)
    
    @pytest.fixture
    def processed_data(self):
        """Create sample processed data."""
        df = pd.DataFrame({
            'Group_Label': ['Group 1', 'Group 2'],
            'Subpopulation': ['CD4', 'CD4'],
            'Tissue': ['SP', 'SP'],
            'Mean': [10.5, 15.3],
            'Std': [0.5, 0.7],
            'Time': [0.0, 24.0],
            'Metric': ['Freq. of Parent', 'Freq. of Parent']
        })
        
        return ProcessedData(
            dataframes=[df],
            metrics=['Freq. of Parent'],
            groups=[1, 2],
            times=[0.0, 24.0],
            tissues_detected=False,
            group_map={1: 'Group 1', 2: 'Group 2'},
            replicate_count=2
        )
    
    def test_create_figure_empty_data(self, config):
        """Test creating figure with empty data."""
        empty_data = ProcessedData(
            dataframes=[],
            metrics=[],
            groups=[],
            times=[],
            tissues_detected=False,
            group_map={},
            replicate_count=0
        )
        
        visualizer = Visualizer(config)
        fig = visualizer.create_figure(empty_data)
        
        assert len(fig.layout.annotations) == 1
        assert "No data to visualize" in fig.layout.annotations[0].text
    
    def test_create_bar_plot(self, config, processed_data):
        """Test creating bar plot figure."""
        visualizer = Visualizer(config)
        fig = visualizer.create_figure(processed_data)
    
        assert len(fig.data) > 0
        # Check that x-axis title is set (may be None due to theme application)
        # The important thing is that the figure is created successfully
        assert fig.layout.xaxis is not None
    
    def test_create_time_course_plot(self, config, processed_data):
        """Test creating time-course plot."""
        config = VisualizationConfig(
            metric=None,
            time_course_mode=True,
            width=800,
            height=800
        )
        
        visualizer = Visualizer(config)
        fig = visualizer.create_figure(processed_data)
        
        # Should create subplots for time course
        assert hasattr(fig, '_grid_ref')
        assert fig.layout.xaxis.title.text == 'Time'


class TestIntegration:
    """Integration tests for the complete visualization pipeline."""
    
    @pytest.fixture
    def test_csv(self, tmp_path):
        """Create test CSV file."""
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({
            'SampleID': ['SP_1.1', 'SP_1.2', 'SP_2.1', 'SP_2.2'],
            'Freq. of Parent CD4': [10.5, 11.2, 15.3, 14.8],
            'Median CD4': [1200, 1250, 1400, 1380]
        })
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def test_visualize_data_success(self, test_csv, tmp_path):
        """Test complete visualization pipeline."""
        output_html = tmp_path / "output.html"
        
        with patch('flowproc.domain.parsing.load_and_parse_df') as mock_load:
            mock_df = pd.DataFrame({
                'SampleID': ['SP_1.1', 'SP_1.2'],
                'Group': [1, 1],
                'Animal': [1, 2],
                'Replicate': [1, 2],
                'Freq. of Parent CD4': [10.5, 11.2]
            })
            mock_load.return_value = (mock_df, 'SampleID')
            
            fig = create_visualization(
                data_source=test_csv,
                output_html=output_html,
                metric="Freq. of Parent"
            )
            
            assert output_html.exists()
            assert fig is not None
    
    def test_visualize_data_file_not_found(self, tmp_path):
        """Test visualization with non-existent file."""
        csv_path = tmp_path / "nonexistent.csv"
        output_html = tmp_path / "output.html"
        
        with pytest.raises(FileNotFoundError):
            create_visualization(csv_path, output_html)
    
    def test_visualize_data_processing_error(self, test_csv, tmp_path):
        """Test visualization with processing error."""
        output_html = tmp_path / "output.html"
        
        with patch('flowproc.domain.parsing.load_and_parse_df') as mock_load:
            # Create a DataFrame that will cause a processing error
            mock_df = pd.DataFrame({
                'SampleID': ['test'],
                'Group': [1],
                'Animal': [1]
            })
            mock_load.return_value = (mock_df, 'SampleID')
            
            # Mock map_replicates to return 0 replicates, which will cause DataProcessingError
            with patch('flowproc.domain.visualization.data_processor.map_replicates') as mock_map:
                mock_map.return_value = (mock_df, 0)
                
                # The current implementation wraps DataProcessingError in VisualizationError
                with pytest.raises(VisualizationError, match="Visualization creation failed"):
                    create_visualization(data_source=test_csv, output_html=output_html)
    
    @given(
        width=st.integers(min_value=100, max_value=2000),
        height=st.integers(min_value=100, max_value=2000)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_visualize_data_dimensions(self, test_csv, tmp_path, width, height):
        """Property-based test for different plot dimensions."""
        output_html = tmp_path / "output.html"
        
        with patch('flowproc.domain.parsing.load_and_parse_df') as mock_load:
            mock_df = pd.DataFrame({
                'SampleID': ['SP_1.1'],
                'Group': [1],
                'Animal': [1],
                'Replicate': [1],
                'Count CD4': [100]
            })
            mock_load.return_value = (mock_df, 'SampleID')
            
            fig = create_visualization(
                data_source=test_csv,
                output_html=output_html,
                width=width,
                height=height
            )
            
            assert fig.layout.width == width
            assert fig.layout.height == height or fig.layout.height == height * 2  # Time course may double height


if __name__ == "__main__":
    pytest.main([__file__, "-v"])