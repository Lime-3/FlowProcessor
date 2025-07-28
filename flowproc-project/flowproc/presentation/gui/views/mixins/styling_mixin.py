# File: flowproc/presentation/gui/views/mixins/styling_mixin.py
"""
Styling mixin for consistent UI appearance.
"""

import logging
from PySide6.QtGui import QPalette, QColor, QFont, QIcon
from PySide6.QtWidgets import QApplication

from flowproc.resource_utils import get_resource_path

logger = logging.getLogger(__name__)


class StylingMixin:
    """
    Mixin for UI styling and theming.
    
    Separates styling logic from main window functionality.
    """

    def setup_styling(self) -> None:
        """Setup the application styling and palette."""
        self.setup_palette_and_style()
        self.setup_application_icon()

    def setup_palette_and_style(self) -> None:
        """Configure the application color palette and stylesheet."""
        from typing import cast
        
        # Set up dark palette
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(15, 15, 15))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 100, 255))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app = cast(QApplication, QApplication.instance())
        app.setPalette(dark_palette)

        # Set comprehensive stylesheet
        app.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #0F0F0F; border-radius: 8px; }
            QLabel { color: #F0F0F0; font-size: 14px; font-family: 'Arial', sans-serif; }
            QLineEdit { background-color: #191919; color: #F0F0F0; border: 1px solid #303030;
                        padding: 8px; border-radius: 4px; }
            QLineEdit#groupEntry { min-height: 25px; max-height: 25px; max-width: 100px; padding: 2px; }
            QLineEdit#replicateEntry { min-height: 25px; max-height: 25px; max-width: 100px; padding: 2px; }
            QPushButton { border: none; background-color: #007BFF; color: white; padding: 8px 16px;
                          border-radius: 4px; font-size: 12px; min-height: 30px; font-weight: 600; }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton:disabled { background-color: #4A4A4A; color: #888888; }
            QPushButton#cancelButton { background-color: #DC3545; }
            QPushButton#cancelButton:hover { background-color: #B02A37; }
            QPushButton#pauseButton { background-color: #FFC107; color: #212529; }
            QPushButton#pauseButton:hover { background-color: #E0A800; }
            QCheckBox { color: #FFFFFF; font-size: 12px; spacing: 8px; padding: 4px;
                        background-color: transparent; border-radius: 3px; }
            QCheckBox::indicator { width: 16px; height: 16px; border: 2px solid #0064FF;
                                   background-color: #1A1A1A; border-radius: 3px; }
            QCheckBox::indicator:checked { background-color: #0064FF; border: 2px solid #0064FF;
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAdUlEQVQYV2NkYGBg+P//PwO2gYGBISHBgP8/A4j3798Z4D9//gT+//8fQ2kQJycnGfD///8M6O7uZqC3t7cZ6OvrZwC4uLiA4eHhAobRaCQAe/fuZqCnpycD9+7dA4hGo2kA7O3tZqC7u/sMABkKeg1K9n2GAAAAAElFTkSuQmCC); }
            QCheckBox::indicator:hover { background-color: #252525; }
            QCheckBox::indicator:checked:hover { background-color: #004CCC; }
            QGroupBox { border: 1px solid #303030; margin-top: 0px; color: #F0F0F0; padding: 10px;
                        border-radius: 6px; }
            QGroupBox::title { subcontrol-origin: margin; padding: 0 8px; font-size: 16px;
                               font-weight: 600; color: #0064FF; }
            QProgressBar { background-color: #222222; color: #F0F0F0; border-radius: 4px;
                           text-align: center; min-height: 30px; }
            QProgressBar::chunk { background-color: #0064FF; border-radius: 4px; }
            QTableWidget { background-color: #191919; color: #F0F0F0; border: 1px solid #303030;
                           gridline-color: #303030; selection-background-color: #0064FF;
                           selection-color: #FFFFFF; }
            QTableWidget::item { padding: 4px; }
            QComboBox { background-color: #191919; color: #F0F0F0; border: 1px solid #303030;
                        padding: 8px; border-radius: 4px; min-height: 40px; }
            QDialog { background-color: #0F0F0F; }
            
            /* Enhanced styling for resizable input fields */
            QLineEdit:focus { border: 2px solid #0064FF; background-color: #1A1A1A; }
            QLineEdit:hover { border: 1px solid #404040; }
            """
        )

    def setup_application_icon(self) -> None:
        """Setup the application icon."""
        try:
            icon_path = get_resource_path("resources/icons/icon.icns")
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                logger.info(f"Application icon set from: {icon_path}")
            else:
                logger.warning(f"Application icon not found at: {icon_path}")
        except Exception as e:
            logger.warning(f"Failed to set application icon: {e}")
