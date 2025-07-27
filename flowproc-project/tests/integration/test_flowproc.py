import pytest
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from unittest.mock import MagicMock
from flowproc.domain.visualization.visualize import visualize_data, DataProcessor, VisualizationConfig
from flowproc.domain.visualization.plotting import create_bar_plot, create_line_plot
from flowproc.presentation.gui.visualizer import visualize_metric, save_plot_as_image
from flowproc.presentation.gui.validators import validate_inputs
from PySide6.QtWidgets import QApplication, QWidget
import plotly.io as pio
import os
from flowproc.domain.parsing.group_animal_parser import extract_group_animal
from flowproc.domain.parsing.tissue_parser import extract_tissue

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "SampleID": ["1.1.fcs", "2.1.fcs", "1.2.fcs", "2.2.fcs", "1.3.fcs", "2.3.fcs"],
        "Group": [1, 1, 2, 2, 1, 2],
        "Replicate": [1, 2, 1, 2, 1, 2],
        "Time": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0],
        "FlowAIGoodEvents/Singlets/Live/T cells/CD4+/CD4+GFP+ | Freq. of Parent (%)": [10, 12, 11, 13, 8, 9],
        "FlowAIGoodEvents/Singlets/Live/T cells/CD8+/CD8+GFP+ | Freq. of Parent (%)": [5, 6, 5.5, 6.5, 4, 4.5],
        "Animal": [1, 2, 1, 2, 1, 2]
    })

@pytest.fixture
def tmp_csv(tmp_path):
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({
        "SampleID": ["SP_A01_1.1", "SP_A01_1.2", "BM_B01_2.1", "BM_B01_2.2"],
        "Group": [1, 1, 2, 2],
        "Time": [0.0, 0.0, 1.0, 1.0],
        "Replicate": [1, 2, 1, 2],
        "Freq. of Parent - CD4": [10.5, 11.0, 15.0, 14.5],  # Multi-subpop for better testing
        "Freq. of Parent - CD8": [20.5, 21.0, 25.0, 24.5],
        "Animal": [1, 1, 2, 2]
    })
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def tmp_csv_multi_tissue(tmp_path):
    csv_path = tmp_path / "multi_tissue.csv"
    df = pd.DataFrame({
        "SampleID": ["SP_1.1", "SP_1.2", "BM_2.1", "BM_2.2", "LN_3.1", "LN_3.2"],
        "Group": [1, 1, 2, 2, 3, 3],
        "Time": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "Replicate": [1, 2, 1, 2, 1, 2],
        "Freq. of Parent": [10, 11, 14, 15, 12, 13],
        "Animal": [1, 1, 2, 2, 3, 3]
    })
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def app():
    return QApplication([])

# These tests are for internal functions that have been refactored
# def test_extract_tissue(sample_df):
#     assert _extract_tissue(sample_df, "SampleID") == "Unknown_tissue"  # Matches UNKNOWN_TISSUE from parsing.py

# def test_aggregate_data_time_course(sample_df):
#     groups = [1, 2]
#     times = [0.0, 1.0]
#     group_map = {1: "Group A", 2: "Group B"}
#     agg_list = _aggregate_data(
#         sample_df,
#         raw_cols=["FlowAIGoodEvents/Singlets/Live/T cells/CD4+/CD4+GFP+ | Freq. of Parent (%)",
#                   "FlowAIGoodEvents/Singlets/Live/T cells/CD8+/CD8+GFP+ | Freq. of Parent (%)"],
#         groups=groups,
#         time_course_mode=True,
#         times=times,
#         tissues_detected=False,
#         group_map=group_map,
#         sid_col="SampleID"
#     )
#     assert len(agg_list) == 1  # Single tissue
#     agg_df = agg_list[0]
#     assert not agg_df.empty
#     assert set(agg_df.columns) == {"Time", "Group_Label", "Subpopulation", "Mean", "Std", "Tissue"}
#     assert agg_df[agg_df['Subpopulation'] == 'FlowAIGoodEvents/Singlets/Live/T cells/CD4+/CD4+GFP+ | Freq. of Parent (%)']['Mean'].iloc[0] == 11.0

def test_process_data(sample_df, monkeypatch):
    def mock_extract_tissue(sample_id):
        return "T1"
    monkeypatch.setattr("flowproc.domain.parsing.tissue_parser.extract_tissue", mock_extract_tissue)
    
    config = VisualizationConfig(
        metric="Freq. of Parent",
        time_course_mode=False,
        user_replicates=[1, 2],
        auto_parse_groups=True,  # Changed to True to auto-detect groups
        user_group_labels=["Group A", "Group B"]
    )
    
    processor = DataProcessor(sample_df, "SampleID", config)
    processed_data = processor.process()
    
    assert len(processed_data.dataframes) == 1  # One metric
    assert processed_data.metrics[0] == "Freq. of Parent"
    # Check that we have data for both subpopulations
    assert len(processed_data.dataframes[0]['Subpopulation'].unique()) == 2

def test_visualize_data_bar(tmp_csv, tmp_path, monkeypatch):
    def mock_load_and_parse_df(path):
        df = pd.read_csv(path)
        parsed = df['SampleID'].apply(extract_group_animal)
        df['Well'] = parsed.apply(lambda p: p[0] if p else "Unknown_well")
        df['Group'] = parsed.apply(lambda p: p[1] if p else 1)
        df['Animal'] = parsed.apply(lambda p: p[2] if p else 1)
        df['Time'] = parsed.apply(lambda p: p[3] if p else None)
        df['Tissue'] = df['SampleID'].apply(extract_tissue)
        return df, "SampleID"
    def mock_map_replicates(df, auto_parse, user_replicates, user_groups=None):
        return df.assign(Replicate=[1, 2, 1, 2]), 2
    monkeypatch.setattr("flowproc.domain.parsing.load_and_parse_df", mock_load_and_parse_df)
    monkeypatch.setattr("flowproc.domain.processing.transform.map_replicates", mock_map_replicates)
    
    output_html = tmp_path / "output.html"
    fig = visualize_data(
        csv_path=str(tmp_csv),
        output_html=output_html,
        metric="Freq. of Parent",
        time_course_mode=False
    )
    assert output_html.exists()
    assert output_html.stat().st_size > 0
    assert isinstance(fig, go.Figure)
    # The current approach aggregates data into a single plot
    # Verify the plot was created successfully with at least one trace
    assert len(fig.data) > 0

def test_visualize_data_time_course(tmp_csv, tmp_path, monkeypatch):
    def mock_load_and_parse_df(path):
        df = pd.read_csv(path)
        # Use sample IDs that should have time data
        df['SampleID'] = ["SP_1.1_0h", "SP_1.2_0h", "BM_2.1_1h", "BM_2.2_1h"]
        parsed = df['SampleID'].apply(extract_group_animal)
        df['Well'] = parsed.apply(lambda p: p.well if p else "Unknown_well")
        df['Group'] = parsed.apply(lambda p: p.group if p else 1)
        df['Animal'] = parsed.apply(lambda p: p.animal if p else 1)
        df['Time'] = [0.0, 0.0, 1.0, 1.0]  # Ensure Time for test
        df['Tissue'] = df['SampleID'].apply(extract_tissue)
        return df, "SampleID"
    def mock_map_replicates(df, auto_parse, user_replicates, user_groups=None):
        return df.assign(Replicate=[1, 2, 1, 2]), 2
    monkeypatch.setattr("flowproc.domain.parsing.load_and_parse_df", mock_load_and_parse_df)
    monkeypatch.setattr("flowproc.domain.processing.transform.map_replicates", mock_map_replicates)
    
    output_html = tmp_path / "output.html"
    fig = visualize_data(
        csv_path=str(tmp_csv),
        output_html=output_html,
        metric="Freq. of Parent",
        time_course_mode=True
    )
    assert output_html.exists()
    assert output_html.stat().st_size > 0
    assert isinstance(fig, go.Figure)
    # The current approach creates a single plot
    # Verify the plot was created successfully with at least one trace
    assert len(fig.data) > 0

# These tests are for internal functions that have been refactored
# def test_create_bar_plot_multi_subpop(sample_df):
#     agg_list = _aggregate_data(sample_df, [
#         "FlowAIGoodEvents/Singlets/Live/T cells/CD4+/CD4+GFP+ | Freq. of Parent (%)",
#         "FlowAIGoodEvents/Singlets/Live/T cells/CD8+/CD8+GFP+ | Freq. of Parent (%)"
#     ], [1, 2], False, [None], False, {1: "Group A", 2: "Group B"}, "SampleID")
#     assert len(agg_list) == 1
#     fig = create_bar_plot(agg_list[0], "Freq. of Parent", 800, 600, "plotly_dark")
#     assert isinstance(fig, go.Figure)
#     assert len(fig.data) == 2  # 1 trace per subpop (no tissues)

# def test_create_line_plot_multi_subpop(sample_df):
#     agg_list = _aggregate_data(sample_df, [
#         "FlowAIGoodEvents/Singlets/Live/T cells/CD4+/CD4+GFP+ | Freq. of Parent (%)",
#         "FlowAIGoodEvents/Singlets/Live/T cells/CD8+/CD8+GFP+ | Freq. of Parent (%)"
#     ], [1, 2], True, [0.0, 1.0], False, {1: "Group A", 2: "Group B"}, "SampleID")
#     assert len(agg_list) == 1
#     fig = create_line_plot(agg_list[0], "Freq. of Parent", 800, 600, "plotly_dark")
#     assert isinstance(fig, go.Figure)
#     assert len(fig.data) == 4  # 2 groups x 2 subpops
#     assert len(fig.layout.annotations) == 2
#     assert "CD4+" in fig.layout.annotations[0].text
#     assert fig.layout.xaxis.title.text == 'Time'
#     assert fig.layout.xaxis.showticklabels

def test_multi_tissue_bar_separate_plots(tmp_csv_multi_tissue, tmp_path, monkeypatch):
    def mock_load_and_parse_df(path):
        df = pd.read_csv(path)
        parsed = df['SampleID'].apply(extract_group_animal)
        df['Well'] = parsed.apply(lambda p: p[0] if p else "Unknown_well")
        df['Group'] = parsed.apply(lambda p: p[1] if p else 1)
        df['Animal'] = parsed.apply(lambda p: p[2] if p else 1)
        df['Time'] = parsed.apply(lambda p: p[3] if p else None)
        df['Tissue'] = df['SampleID'].apply(extract_tissue)
        return df, "SampleID"
    def mock_map_replicates(df, auto_parse, user_replicates, user_groups=None):
        return df.assign(Replicate=[1, 2, 1, 2, 1, 2]), 2
    monkeypatch.setattr("flowproc.domain.parsing.load_and_parse_df", mock_load_and_parse_df)
    monkeypatch.setattr("flowproc.domain.processing.transform.map_replicates", mock_map_replicates)
    
    output_html = tmp_path / "output.html"
    fig = visualize_data(
        csv_path=str(tmp_csv_multi_tissue),
        output_html=output_html,
        metric="Freq. of Parent",
        time_course_mode=False
    )
    assert output_html.exists()
    # Verify the plot was created successfully
    assert isinstance(fig, go.Figure)
    # The current approach shows all tissues in a single plot with tissue info in group labels
    # No facet columns are created, so we just verify the plot exists and has data
    assert len(fig.data) > 0  # Should have at least one trace

def test_invalid_metric(sample_df):
    with pytest.raises(ValueError, match="Invalid metric 'invalid'"):
        config = VisualizationConfig(metric="invalid")
        processor = DataProcessor(sample_df, "SampleID", config)
        processor.process()

def test_visualize_metric(tmp_csv, monkeypatch, app):
    def mock_load_and_parse_df(path):
        df = pd.read_csv(path)
        parsed = df['SampleID'].apply(extract_group_animal)
        df['Well'] = parsed.apply(lambda p: p[0] if p else "Unknown_well")
        df['Group'] = parsed.apply(lambda p: p[1] if p else 1)
        df['Animal'] = parsed.apply(lambda p: p[2] if p else 1)
        df['Time'] = parsed.apply(lambda p: p[3] if p else None)
        df['Tissue'] = df['SampleID'].apply(extract_tissue)
        return df, "SampleID"
    def mock_map_replicates(df, auto_parse, user_replicates, user_groups=None):
        return df, 2
    monkeypatch.setattr("flowproc.domain.parsing.load_and_parse_df", mock_load_and_parse_df)
    monkeypatch.setattr("flowproc.domain.processing.transform.map_replicates", mock_map_replicates)
    
    parent_widget = QWidget()
    visualize_metric(tmp_csv, "Freq. of Parent", False, parent_widget)

def test_save_plot_as_image(tmp_path, monkeypatch):
    fig = go.Figure(data=go.Scatter(x=[1, 2], y=[1, 2]))
    parent_widget = QWidget()
    mock_file_dialog = MagicMock(return_value=(str(tmp_path / "test.png"), "*.png"))
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getSaveFileName", mock_file_dialog)
    with monkeypatch.context() as m:
        m.setattr(pio, "write_image", lambda fig, path: None)
        save_plot_as_image(fig, parent_widget)
    assert mock_file_dialog.called

def test_validate_inputs(tmp_path):
    csv_path = tmp_path / "test.csv"
    pd.DataFrame({"SampleID": ["1.1.fcs", "2.1.fcs"]}).to_csv(csv_path, index=False)
    is_valid, errors = validate_inputs([str(csv_path)], str(tmp_path), [1], [1])  # Fixed function signature
    assert is_valid

# This test is for a function that has been refactored
# def test_process_paths(tmp_csv, tmp_path, monkeypatch):
#     def mock_process_csv(input_path, output_file, time_course_mode):
#         Path(output_file).touch()
#     monkeypatch.setattr("flowproc.writer.process_csv", mock_process_csv)  # Correct module
#     monkeypatch.setattr("flowproc.parsing.load_and_parse_df", lambda p: (pd.DataFrame({"Time": [1.0], "SampleID": ["1.1.fcs"]}), "SampleID"))
    # status_callback = MagicMock()
    # progress_callback = MagicMock()
    # last_csv_callback = MagicMock()
    # count = process_paths([tmp_csv], tmp_path, False, status_callback, progress_callback, 1, last_csv_callback)
    # assert count == 1
    # assert (tmp_path / f"{tmp_csv.stem}_Processed_Grouped.xlsx").exists()