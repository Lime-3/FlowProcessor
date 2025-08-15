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
    
    # Set application icon (platform-aware)
    try:
        if sys.platform == "darwin":
            candidates = ["resources/icons/icon.icns", "resources/icons/icon.png"]
        elif sys.platform.startswith("win"):
            candidates = ["resources/icons/icon.ico", "resources/icons/icon.png", "resources/icons/icon.icns"]
        else:
            candidates = ["resources/icons/icon.png", "resources/icons/icon.ico", "resources/icons/icon.icns"]

        for rel in candidates:
            icon_path = get_resource_path(rel)
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
                logging.info(f"Application icon set from: {icon_path}")
                break
        else:
            logging.warning("Application icon not found in expected locations")
    except Exception as e:
        logging.warning(f"Failed to set application icon: {e}")
    
    window = MainWindow()
    window.show()
    logging.debug("Main window shown")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()