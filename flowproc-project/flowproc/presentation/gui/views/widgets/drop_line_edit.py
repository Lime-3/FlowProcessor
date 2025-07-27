# flowproc/gui/widgets.py
from PySide6.QtWidgets import QLineEdit, QMessageBox
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DropLineEdit(QLineEdit):
    """A QLineEdit that accepts drag-and-drop of CSV files or folders."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        logger.debug("DropLineEdit initialized")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        logger.debug("Drag enter event on input field received")
        if event.mimeData().hasUrls():
            logger.debug(f"Mime data URLs: {event.mimeData().urls()}")
            event.acceptProposedAction()
        else:
            logger.debug("No URLs in mime data")
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        logger.debug("Drop event on input field received")
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            file_paths = [url.toLocalFile() for url in mime_data.urls()]
            logger.debug(f"Raw dropped paths: {file_paths}")
            valid_paths = []
            for path in file_paths:
                p = Path(path)
                if p.is_dir() or p.suffix.lower() == '.csv':
                    valid_paths.append(path)
            if valid_paths:
                existing_paths = self.text().split("; ") if self.text() else []
                all_paths = existing_paths + valid_paths
                all_paths = list(dict.fromkeys(all_paths))  # Remove duplicates
                self.setText("; ".join(all_paths))
                logger.debug(f"Accepted paths: {valid_paths}")
                event.acceptProposedAction()
            else:
                logger.debug("No valid paths dropped")
                QMessageBox.warning(self.parent(), "Invalid Drop", "Please drop only CSV files or folders.")
                event.ignore()
        else:
            logger.debug("No mime data with URLs")
            event.ignore()