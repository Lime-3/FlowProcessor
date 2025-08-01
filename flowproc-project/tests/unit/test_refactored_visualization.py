"""
Unit tests for refactored visualization modules.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go
from unittest.mock import patch, MagicMock

from flowproc.domain.visualization.plot_config import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, MARGIN, VERTICAL_SPACING, HORIZONTAL_SPACING,
    MAX_CELL_TYPES, SUBPLOT_HEIGHT_PER_ROW, DEFAULT_TRACE_CONFIG
)
from flowproc.domain.visualization.plot_utils import (
    format_time_title, validate_plot_data, limit_cell_types, calculate_subplot_dimensions
)
from flowproc.domain.visualization.legend_config import (
    configure_legend, apply_default_layout, _configure_global_legend,
    _configure_subplot_legend, _create_subplot_legend_annotation
)
from flowproc.domain.visualization.faceted_plots import (
    _create_faceted_plot, create_cell_type_faceted_plot,
    create_group_faceted_plot, create_single_column_faceted_plot
)


class TestPlotConfig:
    """Test shared configuration constants."""
    
    def test_default_dimensions(self):
        """Test default dimension constants."""
        assert DEFAULT_WIDTH == 1200
        assert DEFAULT_HEIGHT == 800
        assert MARGIN == {'l': 50, 'r': 200, 't': 50, 'b': 50}
    
    def test_spacing_constants(self):
        """Test spacing constants."""
        assert VERTICAL_SPACING == 0.12
        assert HORIZONTAL_SPACING == 0.05
    
    def test_legend_constants(self):
        """Test legend configuration constants."""
        assert MAX_CELL_TYPES == 8
        assert SUBPLOT_HEIGHT_PER_ROW == 200
        assert DEFAULT_TRACE_CONFIG == {'line': {'width': 2}, 'marker': {'size': 6}}


class TestPlotUtils:
    """Test utility functions."""
    
    def test_format_time_title_days(self):
        """Test time formatting for days."""
        time_values = [24, 48, 72]
        result = format_time_title(time_values)
        assert result == " (Day 1, Day 2, Day 3)"
    
    def test_format_time_title_hours(self):
        """Test time formatting for hours."""
        time_values = [1, 2, 3]
        result = format_time_title(time_values)
        assert result == " (1h, 2h, 3h)"
    
    def test_format_time_title_minutes(self):
        """Test time formatting for minutes."""
        time_values = [0.5, 1.0]  # 30 min, 1 hour
        result = format_time_title(time_values)
        assert result == " (30min, 1h)"
    
    def test_format_time_title_mixed(self):
        """Test time formatting for mixed values."""
        time_values = [0.5, 2, 25]  # 30 min, 2h, 25h
        result = format_time_title(time_values)
        assert result == " (30min, 2h, Day 1.0)"
    
    def test_format_time_title_numpy_array(self):
        """Test time formatting with numpy array."""
        import numpy as np
        time_values = np.array([1, 2, 3])
        result = format_time_title(time_values)
        assert result == " (1h, 2h, 3h)"
    
    def test_validate_plot_data_success(self):
        """Test successful data validation."""
        df = pd.DataFrame({
            'Time': [1, 2, 3],
            'CellType1': [10, 20, 30],
            'CellType2': [15, 25, 35],
            'Group': ['A', 'B', 'C']
        })
        validate_plot_data(df, 'Time', ['CellType1', 'CellType2'], 'Group')
        # Should not raise any exception
    
    def test_validate_plot_data_empty_df(self):
        """Test validation with empty DataFrame."""
        df = pd.DataFrame()
        with pytest.raises(ValueError, match="DataFrame is empty"):
            validate_plot_data(df, 'Time', ['CellType1'], 'Group')
    
    def test_validate_plot_data_missing_time_col(self):
        """Test validation with missing time column."""
        df = pd.DataFrame({'CellType1': [10, 20, 30]})
        with pytest.raises(ValueError, match="Time column 'Time' not found"):
            validate_plot_data(df, 'Time', ['CellType1'])
    
    def test_validate_plot_data_missing_value_cols(self):
        """Test validation with missing value columns."""
        df = pd.DataFrame({'Time': [1, 2, 3], 'CellType1': [10, 20, 30]})
        with pytest.raises(ValueError, match="Value columns not found in data"):
            validate_plot_data(df, 'Time', ['CellType1', 'MissingCol'])
    
    def test_validate_plot_data_missing_facet_col(self):
        """Test validation with missing facet column."""
        df = pd.DataFrame({'Time': [1, 2, 3], 'CellType1': [10, 20, 30]})
        with pytest.raises(ValueError, match="Facet column 'Group' not found"):
            validate_plot_data(df, 'Time', ['CellType1'], 'Group')
    
    def test_limit_cell_types_no_limit(self):
        """Test cell type limiting when under limit."""
        value_cols = ['CellType1', 'CellType2', 'CellType3']
        result = limit_cell_types(value_cols, 8)
        assert result == value_cols
    
    def test_limit_cell_types_with_limit(self):
        """Test cell type limiting when over limit."""
        value_cols = ['CellType1', 'CellType2', 'CellType3', 'CellType4', 
                     'CellType5', 'CellType6', 'CellType7', 'CellType8', 'CellType9']
        result = limit_cell_types(value_cols, 8)
        assert len(result) == 8
        assert result == sorted(value_cols)[:8]
    
    def test_calculate_subplot_dimensions_single_column(self):
        """Test subplot dimension calculation for single column."""
        rows, cols = calculate_subplot_dimensions(5)
        assert rows == 5
        assert cols == 1
    
    def test_calculate_subplot_dimensions_multi_column(self):
        """Test subplot dimension calculation for multi-column."""
        rows, cols = calculate_subplot_dimensions(6, 3)
        assert rows == 2
        assert cols == 3


class TestLegendConfig:
    """Test legend configuration functions."""
    
    def test_configure_legend_global(self):
        """Test global legend configuration."""
        fig = go.Figure()
        df = pd.DataFrame({
            'Time': [1, 2, 3],
            'CellType1': [10, 20, 30],
            'Group': ['A', 'B', 'C']
        })
        
        result = configure_legend(
            fig=fig,
            df=df,
            color_col='Group',
            is_subplot=False
        )
        
        assert isinstance(result, go.Figure)
        assert result.layout.legend is not None
        assert result.layout.legend.x == 1.05
    
    def test_configure_legend_subplot(self):
        """Test subplot legend configuration."""
        fig = go.Figure()
        subplot_groups = ['Group A', 'Group B']
        subplot_traces = [
            go.Scatter(name='Group A', line=dict(color='red')),
            go.Scatter(name='Group B', line=dict(color='blue'))
        ]
        
        result = configure_legend(
            fig=fig,
            subplot_groups=subplot_groups,
            subplot_traces=subplot_traces,
            is_subplot=True
        )
        
        assert isinstance(result, go.Figure)
        # Should have annotations for subplot legend
        assert hasattr(result.layout, 'annotations')
    
    def test_apply_default_layout(self):
        """Test default layout application."""
        fig = go.Figure()
        result = apply_default_layout(fig)
        
        assert isinstance(result, go.Figure)
        assert result.layout.width == DEFAULT_WIDTH
        assert result.layout.height == DEFAULT_HEIGHT
        # Check margin attributes individually
        assert result.layout.margin.l == MARGIN['l']
        assert result.layout.margin.r == MARGIN['r']
        assert result.layout.margin.t == MARGIN['t']
        assert result.layout.margin.b == MARGIN['b']
    
    def test_apply_default_layout_custom(self):
        """Test default layout with custom parameters."""
        fig = go.Figure()
        custom_margin = {'l': 100, 'r': 100, 't': 100, 'b': 100}
        result = apply_default_layout(fig, width=1000, height=600, margin=custom_margin)
        
        assert result.layout.width == 1000
        assert result.layout.height == 600
        # Check margin attributes individually
        assert result.layout.margin.l == custom_margin['l']
        assert result.layout.margin.r == custom_margin['r']
        assert result.layout.margin.t == custom_margin['t']
        assert result.layout.margin.b == custom_margin['b']
    
    def test_create_subplot_legend_annotation(self):
        """Test subplot legend annotation creation."""
        subplot_groups = ['Group A', 'Group B']
        subplot_traces = [
            go.Scatter(name='Group A', line=dict(color='red')),
            go.Scatter(name='Group B', line=dict(color='blue'))
        ]
        
        result = _create_subplot_legend_annotation(subplot_groups, subplot_traces)
        
        assert isinstance(result, dict)
        assert 'text' in result
        assert 'x' in result
        assert 'y' in result
        assert 'bgcolor' in result
        assert 'red' in result['text']  # Should contain color information
        assert 'blue' in result['text']


class TestFacetedPlots:
    """Test faceted plot functions."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'Time': [1, 2, 3, 1, 2, 3],
            'CellType1': [10, 20, 30, 15, 25, 35],
            'CellType2': [5, 15, 25, 8, 18, 28],
            'Group': ['A', 'A', 'A', 'B', 'B', 'B']
        })
    
    @patch('flowproc.domain.visualization.faceted_plots.create_enhanced_title')
    @patch('flowproc.domain.visualization.faceted_plots.get_base_columns')
    @patch('flowproc.domain.visualization.faceted_plots.prepare_data_for_plotting')
    def test_create_cell_type_faceted_plot(self, mock_prepare, mock_base_cols, mock_title, sample_df):
        """Test cell type faceted plot creation."""
        # Mock dependencies
        mock_title.return_value = "Test Title"
        mock_base_cols.return_value = ['Time', 'Group']
        # Mock prepare_data_for_plotting to return data with both columns
        mock_prepare.return_value = pd.DataFrame({
            'Time': [1, 2, 3],
            'CellType1': [10, 20, 30],
            'CellType2': [5, 15, 25],
            'Group': ['A', 'A', 'A']
        })
        
        result = create_cell_type_faceted_plot(
            df=sample_df,
            time_col='Time',
            value_cols=['CellType1', 'CellType2']
        )
        
        assert isinstance(result, go.Figure)
        assert result.layout.title.text == "Time Course by Cell Type"
        assert result.layout.width == DEFAULT_WIDTH
    
    @patch('flowproc.domain.visualization.faceted_plots.extract_cell_type_name')
    @patch('flowproc.domain.visualization.faceted_plots.get_base_columns')
    @patch('flowproc.domain.visualization.faceted_plots.prepare_data_for_plotting')
    def test_create_group_faceted_plot(self, mock_prepare, mock_base_cols, mock_extract, sample_df):
        """Test group faceted plot creation."""
        # Mock dependencies
        mock_extract.return_value = "Test Cell Type"
        mock_base_cols.return_value = ['Time', 'Group']
        # Mock prepare_data_for_plotting to return data with both columns
        mock_prepare.return_value = pd.DataFrame({
            'Time': [1, 2, 3],
            'CellType1': [10, 20, 30],
            'CellType2': [5, 15, 25],
            'Group': ['A', 'A', 'A']
        })
        
        result = create_group_faceted_plot(
            df=sample_df,
            time_col='Time',
            value_cols=['CellType1', 'CellType2'],
            facet_by='Group'
        )
        
        assert isinstance(result, go.Figure)
        assert result.layout.title.text == "Time Course by Group"
        assert result.layout.width == DEFAULT_WIDTH
    
    @patch('flowproc.domain.visualization.faceted_plots.get_base_columns')
    @patch('flowproc.domain.visualization.faceted_plots.prepare_data_for_plotting')
    def test_create_single_column_faceted_plot(self, mock_prepare, mock_base_cols, sample_df):
        """Test single column faceted plot creation."""
        # Mock dependencies
        mock_base_cols.return_value = ['Time', 'Group']
        # Mock prepare_data_for_plotting to return data with the single column
        mock_prepare.return_value = pd.DataFrame({
            'Time': [1, 2, 3],
            'CellType1': [10, 20, 30],
            'Group': ['A', 'A', 'A']
        })
        
        result = create_single_column_faceted_plot(
            df=sample_df,
            time_col='Time',
            value_col='CellType1',
            facet_by='Group'
        )
        
        assert isinstance(result, go.Figure)
        assert result.layout.title.text == "CellType1 over Time by Group"
        assert result.layout.width == DEFAULT_WIDTH
    
    def test_create_faceted_plot_validation_error(self):
        """Test faceted plot creation with validation error."""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="DataFrame is empty"):
            _create_faceted_plot(
                df=empty_df,
                time_col='Time',
                value_cols=['CellType1']
            )
    
    def test_create_faceted_plot_custom_parameters(self):
        """Test faceted plot creation with custom parameters."""
        df = pd.DataFrame({
            'Time': [1, 2, 3],
            'CellType1': [10, 20, 30],
            'Group': ['A', 'A', 'A']
        })
        
        with patch('flowproc.domain.visualization.faceted_plots.create_enhanced_title') as mock_title, \
             patch('flowproc.domain.visualization.faceted_plots.get_base_columns') as mock_base_cols, \
             patch('flowproc.domain.visualization.faceted_plots.prepare_data_for_plotting') as mock_prepare:
            
            mock_title.return_value = "Test Title"
            mock_base_cols.return_value = ['Time', 'Group']
            mock_prepare.return_value = df
            
            result = _create_faceted_plot(
                df=df,
                time_col='Time',
                value_cols=['CellType1'],
                title="Custom Title",
                width=1000,
                height=600,
                max_cell_types=5
            )
            
            assert isinstance(result, go.Figure)
            assert result.layout.title.text == "Custom Title"
            assert result.layout.width == 1000
            assert result.layout.height == 600


if __name__ == "__main__":
    pytest.main([__file__]) 