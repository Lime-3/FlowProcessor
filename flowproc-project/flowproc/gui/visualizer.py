from pathlib import Path
from typing import Optional
import logging
import hashlib
import os
import shutil
import tempfile
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QSizePolicy, QPushButton, QFileDialog, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QResizeEvent

from flowproc.config import AUTO_PARSE_GROUPS, USER_REPLICATES, USER_GROUP_LABELS
from flowproc.visualize import visualize_data
from flowproc.parsing import load_and_parse_df
from flowproc.writer import KEYWORDS
from flowproc.logging_config import setup_logging

logger = logging.getLogger(__name__)

def save_plot_as_image(fig: go.Figure, parent_widget: Optional[QWidget]) -> None:
    """Save the Plotly figure as a PNG image."""
    if not isinstance(parent_widget, QWidget):
        logger.error("Parent widget must be a QWidget, got %s", type(parent_widget))
        return
    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Save Plot as Image",
        str(Path.home() / f"flowproc_plot_{pio.to_image(fig, format='png')[:10]}.png"),
        "PNG Files (*.png);;JPEG Files (*.jpg)"
    )
    if file_path:
        try:
            pio.write_image(fig, file_path)
            logger.info(f"Plot saved as image: {file_path}")
            QMessageBox.information(parent_widget, "Success", f"Plot saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save plot: {str(e)}")
            QMessageBox.critical(parent_widget, "Error", f"Failed to save plot: {str(e)}")

def visualize_metric(
    csv_path: Optional[Path],
    metric: str,
    time_course_mode: bool,
    parent_widget: Optional[QWidget] = None
) -> None:
    """Generate and display visualization for the given CSV and metric (faceted if multi-tissue)."""
    if not csv_path or not csv_path.exists():
        QMessageBox.warning(parent_widget, "No Data", "Select at least one CSV file to visualize.")
        logger.warning("Visualization attempted with no valid CSV")
        return
    temp_html = None
    debug_html = Path.home() / "Desktop" / f"flowproc_plot.html"
    try:
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            temp_html = temp_dir / "plot.html"
            logger.debug(f"Generating plot at: {temp_html}")
            df, sid_col = load_and_parse_df(csv_path)
            if df.empty:
                raise ValueError("No data found in CSV")
            fig = visualize_data(
                csv_path=str(csv_path),
                output_html=temp_html,
                metric=metric,
                time_course_mode=time_course_mode,
                user_replicates=USER_REPLICATES,
                auto_parse_groups=AUTO_PARSE_GROUPS,
                user_group_labels=USER_GROUP_LABELS
            )
            if not temp_html.exists():
                raise ValueError(f"Plot file {temp_html} not created")
            file_size = temp_html.stat().st_size
            with open(temp_html, "rb") as fh:
                file_hash = hashlib.md5(fh.read()).hexdigest()
            logger.debug(f"Plot size: {file_size} bytes, MD5: {file_hash}")
            debug_html.parent.mkdir(exist_ok=True)
            shutil.copy2(temp_html, debug_html)
            if not os.access(temp_html, os.R_OK):
                raise ValueError(f"Plot file {temp_html} not readable")
            dialog = QDialog(None if not isinstance(parent_widget, QWidget) else parent_widget)
            dialog.setWindowTitle(f"Visualization Preview - {metric}")
            dialog.resize(820, 620)
            dialog.setMinimumSize(820, 620)
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            save_button = QPushButton("Save Image")
            save_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            save_button.clicked.connect(lambda: save_plot_as_image(fig, dialog))
            layout.addWidget(save_button)
            view = QWebEngineView()
            view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            layout.addWidget(view, stretch=1)
            def resizeEvent(event: QResizeEvent) -> None:  # Type hint for clarity
                view.resize(event.size())
                view.update()
                logger.debug(f"Dialog resized to {event.size()}")
            dialog.resizeEvent = resizeEvent  # No need for __get__
            def on_load_finished(ok: bool) -> None:
                if ok:
                    logger.info(f"Loaded {temp_html}")
                    dialog.show()
                else:
                    error_string = view.page().lastErrorString() or "Unknown error"
                    logger.error(f"Failed to load {temp_html}: {error_string}")
                    QMessageBox.critical(dialog, "Load Error", f"Failed to load: {error_string}\nCheck {debug_html}")
            view.page().loadFinished.connect(on_load_finished)
            file_url = QUrl.fromLocalFile(str(temp_html.resolve()))
            logger.debug(f"Loading URL: {file_url.toString()}")
            view.load(file_url)
            QTimer.singleShot(2000, lambda: logger.debug(f"Load status: {view.page().isLoading()}"))
            dialog.exec()
    except (ValueError, pd.errors.ParserError, OSError) as e:
        logger.error(f"Visualization failed: {str(e)}")
        if parent_widget and isinstance(parent_widget, QWidget):
            QMessageBox.critical(parent_widget, "Visualization Error", f"Failed: {str(e)}\nCheck {debug_html if debug_html.exists() else 'N/A'}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise RuntimeError(f"Visualization failed: {str(e)}")