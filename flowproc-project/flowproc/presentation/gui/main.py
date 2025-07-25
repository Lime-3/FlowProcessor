# flowproc/gui/main.py
import sys
from PySide6.QtWidgets import QApplication
import logging

from ...logging_config import setup_logging
from .window import MainWindow

def main() -> None:
    """
    Entry point for the GUI application.
    """
    setup_logging(filemode='a')
    logging.debug("GUI application started")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    logging.debug("Main window shown")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()