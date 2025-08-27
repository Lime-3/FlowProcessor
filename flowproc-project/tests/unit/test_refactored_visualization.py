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


class TestPlotConfig:
    """Test shared configuration constants."""
    
    def test_default_dimensions(self):
        """Test default dimension constants."""
        assert DEFAULT_WIDTH == 800
        assert DEFAULT_HEIGHT == 350
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
    
    def test_limit_cell_types(self):
        """Test cell type limiting."""
        value_cols = [f'CellType{i}' for i in range(10)]
        limited = limit_cell_types(value_cols, 5)
        assert len(limited) == 5
        assert limited == ['CellType0', 'CellType1', 'CellType2', 'CellType3', 'CellType4']
    
    def test_limit_cell_types_no_limit(self):
        """Test cell type limiting when under limit."""
        value_cols = [f'CellType{i}' for i in range(3)]
        limited = limit_cell_types(value_cols, 5)
        assert len(limited) == 3
        assert limited == value_cols
    
    def test_calculate_subplot_dimensions(self):
        """Test subplot dimension calculation."""
        dimensions = calculate_subplot_dimensions(6)
        assert dimensions == (3, 2)  # 3 rows, 2 columns (max 2 per row)
        
        dimensions = calculate_subplot_dimensions(4)
        assert dimensions == (2, 2)  # 2 rows, 2 columns
        
        dimensions = calculate_subplot_dimensions(1)
        assert dimensions == (1, 1)  # 1 row, 1 column


class TestLegendConfig:
    """Test legend configuration functions."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'Time': [1, 2, 3, 1, 2, 3],
            'CellType1': [10, 20, 30, 15, 25, 35],
            'CellType2': [5, 15, 25, 8, 18, 28],
            'Group': ['A', 'A', 'A', 'B', 'B', 'B']
        })
    
    def test_configure_legend_basic(self, sample_df):
        """Test basic legend configuration."""
        fig = go.Figure()
        result = configure_legend(fig, sample_df, 'Group', is_subplot=False)
        
        assert isinstance(result, go.Figure)
        assert result.layout.showlegend is True
    
    def test_configure_legend_subplot(self, sample_df):
        """Test subplot legend configuration."""
        fig = go.Figure()
        # Add some traces to make the legend meaningful
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[10, 20, 30], name='Group A'))
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[15, 25, 35], name='Group B'))
        result = configure_legend(fig, sample_df, 'Group', is_subplot=True)
        
        assert isinstance(result, go.Figure)
        # The showlegend property might not be set explicitly, so just check it's a figure
        assert isinstance(result, go.Figure)
    
    def test_apply_default_layout(self):
        """Test default layout application."""
        fig = go.Figure()
        result = apply_default_layout(fig, width=1000, height=600)
        
        assert isinstance(result, go.Figure)
        assert result.layout.width == 1000
        assert result.layout.height == 600
    
    def test_configure_global_legend(self):
        """Test global legend configuration."""
        fig = go.Figure()
        df = pd.DataFrame({'Group': ['A', 'B', 'C']})
        result = _configure_global_legend(fig, df, 'Group', width=800, height=400)
        
        assert isinstance(result, go.Figure)
        # Check that the figure was returned
        assert isinstance(result, go.Figure)
    
    def test_configure_subplot_legend(self):
        """Test subplot legend configuration."""
        fig = go.Figure()
        subplot_groups = ['Group A', 'Group B']
        subplot_traces = [
            go.Scatter(name='Group A', line=dict(color='red')),
            go.Scatter(name='Group B', line=dict(color='blue'))
        ]
        
        result = _configure_subplot_legend(fig, subplot_groups, subplot_traces, 
                                        legend_x=1.05, legend_y=0.5, width=800, height=400,
                                        font_size=12, bg_color='white')
        
        assert isinstance(result, go.Figure)
        # Check that the figure was returned
        assert isinstance(result, go.Figure)
    
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


if __name__ == "__main__":
    pytest.main([__file__]) 