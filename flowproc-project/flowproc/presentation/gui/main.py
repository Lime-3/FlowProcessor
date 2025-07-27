# flowproc/gui/main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import logging
from pathlib import Path

from flowproc.logging_config import setup_logging
from flowproc.presentation.gui.views.main_window import MainWindow
from flowproc.resource_utils import get_resource_path

def main() -> None:
    """
    Entry point for the GUI application.
    """
    setup_logging(filemode='a')
    logging.debug("GUI application started")

    app = QApplication(sys.argv)
    
    # Set application icon
    try:
        icon_path = get_resource_path("resources/icons/icon.icns")
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            logging.info(f"Application icon set from: {icon_path}")
        else:
            logging.warning(f"Application icon not found at: {icon_path}")
    except Exception as e:
        logging.warning(f"Failed to set application icon: {e}")
    
    window = MainWindow()
    window.show()
    logging.debug("Main window shown")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()