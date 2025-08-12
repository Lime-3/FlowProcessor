"""
Manual Groups and Replicates Dialog.

This dialog allows users to manually define groups and replicates
for data processing instead of using automatic parsing.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QMessageBox, QGroupBox, QCheckBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from flowproc.config import parse_range_or_list


class ManualGroupsDialog(QDialog):
    """
    Dialog for manually defining groups and replicates.
    
    Features:
    - Checkbox to enable/disable manual mode
    - Input fields for group numbers and replicate numbers
    - Save functionality
    - Validation of input values
    """
    
    # Signals
    manual_mode_toggled = Signal(bool)  # Emitted when manual mode is toggled
    definitions_saved = Signal(list, list)  # Emitted when groups/replicates are saved
    
    def __init__(self, parent=None, initial_groups: Optional[List[int]] = None, 
                 initial_replicates: Optional[List[int]] = None, 
                 manual_mode_enabled: bool = False):
        super().__init__(parent)
        
        self.groups: List[int] = initial_groups or [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        self.replicates: List[int] = initial_replicates or [1, 2, 3]
        self.manual_mode_enabled = manual_mode_enabled
        
        self.setWindowTitle("Manual Groups and Replicates")
        self.setModal(True)
        self.resize(500, 400)
        self.setMinimumHeight(400)
        
        self._setup_ui()
        self._setup_styling()
        self._populate_fields()
        
    def _setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Instructions
        instructions = QLabel(
            "Use this dialog to manually define groups and replicates instead of automatic parsing. "
            "Enter group numbers and replicate numbers as ranges (e.g., 1-13) or comma-separated values (e.g., 1,2,3)."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        layout.addWidget(instructions)
        
        # Manual mode checkbox
        self.manual_checkbox = QCheckBox("Enable Manual Groups and Replicates")
        self.manual_checkbox.setChecked(self.manual_mode_enabled)
        self.manual_checkbox.stateChanged.connect(self._on_manual_mode_changed)
        layout.addWidget(self.manual_checkbox)
        
        # Manual definition group
        self.manual_group = QGroupBox("Manual Definition")
        manual_layout = QVBoxLayout(self.manual_group)
        manual_layout.setSpacing(15)
        
        # Group section
        group_section = QWidget()
        group_layout = QVBoxLayout(group_section)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(8)
        
        group_label = QLabel("Group Numbers:")
        group_label.setStyleSheet("font-weight: 600; color: #F0F0F0; font-size: 14px;")
        
        self.groups_entry = QLineEdit()
        self.groups_entry.setPlaceholderText("e.g., 1-13 or 1,2,3,4,5")
        self.groups_entry.setMinimumHeight(35)
        self.groups_entry.setStyleSheet("font-size: 13px;")
        
        group_layout.addWidget(group_label)
        group_layout.addWidget(self.groups_entry)
        
        # Replicate section
        replicate_section = QWidget()
        replicate_layout = QVBoxLayout(replicate_section)
        replicate_layout.setContentsMargins(0, 0, 0, 0)
        replicate_layout.setSpacing(8)
        
        replicate_label = QLabel("Replicate Numbers:")
        replicate_label.setStyleSheet("font-weight: 600; color: #F0F0F0; font-size: 14px;")
        
        self.replicates_entry = QLineEdit()
        self.replicates_entry.setPlaceholderText("e.g., 1-3 or 1,2")
        self.replicates_entry.setMinimumHeight(35)
        self.replicates_entry.setStyleSheet("font-size: 13px;")
        
        replicate_layout.addWidget(replicate_label)
        replicate_layout.addWidget(self.replicates_entry)
        
        # Add sections to manual layout
        manual_layout.addWidget(group_section)
        manual_layout.addWidget(replicate_section)
        
        layout.addWidget(self.manual_group)
        
        # Dialog buttons
        dialog_buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_definitions)
        self.save_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        dialog_buttons_layout.addStretch()
        dialog_buttons_layout.addWidget(self.save_button)
        dialog_buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(dialog_buttons_layout)
        
        # Update UI state based on checkbox
        self._update_ui_state()
        
    def _setup_styling(self):
        """Apply custom styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F0F;
                color: #F0F0F0;
            }
            
            QGroupBox {
                border: 1px solid #303030;
                border-radius: 6px;
                margin-top: 0px;
                padding-top: 15px;
                font-weight: 600;
                color: #0064FF;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 8px;
                font-size: 14px;
            }
            
            QLineEdit {
                background-color: #191919;
                color: #F0F0F0;
                border: 1px solid #303030;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 13px;
            }
            
            QLineEdit:focus {
                border: 2px solid #0064FF;
            }
            
            QLineEdit:disabled {
                background-color: #2A2A2A;
                color: #888888;
                border: 1px solid #404040;
            }
            
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                min-height: 35px;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QPushButton:disabled {
                background-color: #4A4A4A;
                color: #888888;
            }
            
            QCheckBox {
                font-size: 14px;
                font-weight: 600;
                color: #F0F0F0;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #303030;
                border-radius: 3px;
                background-color: #191919;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0064FF;
                border-color: #0064FF;
            }
            
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: white;
                font-weight: bold;
                font-size: 12px;
                position: relative;
                left: 2px;
                top: -1px;
            }
        """)
        
    def _populate_fields(self):
        """Populate the input fields with current values."""
        if self.groups:
            groups_text = self._format_numbers_for_display(self.groups)
            self.groups_entry.setText(groups_text)
        
        if self.replicates:
            replicates_text = self._format_numbers_for_display(self.replicates)
            self.replicates_entry.setText(replicates_text)
            
    def _format_numbers_for_display(self, numbers: List[int]) -> str:
        """Format a list of numbers for display in the input field."""
        if not numbers:
            return ""
        
        # Try to create ranges for consecutive numbers
        ranges = []
        start = end = numbers[0]
        
        for num in numbers[1:]:
            if num == end + 1:
                end = num
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = num
        
        # Add the last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
            
        return ",".join(ranges)
        
    def _on_manual_mode_changed(self, state: int):
        """Handle manual mode checkbox state change."""
        enabled = bool(state)
        self.manual_mode_enabled = enabled
        self._update_ui_state()
        self.manual_mode_toggled.emit(enabled)
        
    def _update_ui_state(self):
        """Update UI state based on manual mode checkbox."""
        enabled = self.manual_mode_enabled
        self.manual_group.setEnabled(enabled)
        self.groups_entry.setEnabled(enabled)
        self.replicates_entry.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        
    def _save_definitions(self):
        """Save the manual group and replicate definitions."""
        try:
            groups_text = self.groups_entry.text().strip()
            replicates_text = self.replicates_entry.text().strip()
            
            if not groups_text or not replicates_text:
                raise ValueError("Both groups and replicates must be specified.")
            
            # Parse the input values
            new_groups = parse_range_or_list(groups_text)
            new_replicates = parse_range_or_list(replicates_text)
            
            if not new_groups:
                raise ValueError("No valid group numbers found.")
                
            if not new_replicates:
                raise ValueError("No valid replicate numbers found.")
            
            # Update internal state
            self.groups = new_groups
            self.replicates = new_replicates
            
            # Emit signal
            self.definitions_saved.emit(self.groups, self.replicates)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Success", 
                f"Successfully saved:\n"
                f"Groups: {', '.join(map(str, self.groups))}\n"
                f"Replicates: {', '.join(map(str, self.replicates))}"
            )
            
            # Accept the dialog
            self.accept()
            
        except ValueError as e:
            QMessageBox.critical(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            
    def get_groups(self) -> List[int]:
        """Get the current list of groups."""
        return self.groups.copy()
        
    def get_replicates(self) -> List[int]:
        """Get the current list of replicates."""
        return self.replicates.copy()
        
    def is_manual_mode_enabled(self) -> bool:
        """Check if manual mode is enabled."""
        return self.manual_mode_enabled
        
    def set_groups(self, groups: List[int]):
        """Set the list of groups."""
        self.groups = groups.copy()
        self._populate_fields()
        
    def set_replicates(self, replicates: List[int]):
        """Set the list of replicates."""
        self.replicates = replicates.copy()
        self._populate_fields()
        
    def set_manual_mode(self, enabled: bool):
        """Set the manual mode state."""
        self.manual_mode_enabled = enabled
        self.manual_checkbox.setChecked(enabled)
        self._update_ui_state()
