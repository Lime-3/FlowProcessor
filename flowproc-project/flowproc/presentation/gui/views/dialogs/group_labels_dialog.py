"""
Group Labels Dialog for managing group labels.

This dialog allows users to add, edit, and remove group labels
that will be used for processing CSV files.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QMessageBox, QGroupBox,
    QInputDialog, QAbstractItemView, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class GroupLabelsDialog(QDialog):
    """
    Dialog for managing group labels.
    
    Features:
    - List view of group labels
    - Add new group labels
    - Edit existing group labels
    - Remove group labels
    - Import from comma-separated text
    """
    
    # Signals
    labels_changed = Signal(list)  # Emitted when labels are modified
    
    def __init__(self, parent=None, initial_labels: Optional[List[str]] = None):
        super().__init__(parent)
        self.labels: List[str] = initial_labels or []
        
        self.setWindowTitle("Group Labels")
        self.setModal(True)
        self.resize(900, 700)
        
        self._setup_ui()
        self._setup_styling()
        self._populate_list()
        
    def _setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Instructions
        instructions = QLabel(
            "Add group labels that will be used to identify different groups in your data. "
            "Labels should be descriptive and unique."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        layout.addWidget(instructions)
        
        # Paste from Excel section
        paste_group = QGroupBox("Paste from Excel")
        paste_layout = QVBoxLayout(paste_group)
        
        paste_instructions = QLabel(
            "Copy a column of labels from Excel and paste them below. "
            "Each line will become a separate group label."
        )
        paste_instructions.setWordWrap(True)
        paste_instructions.setStyleSheet("color: #A0A0A0; font-size: 11px;")
        paste_layout.addWidget(paste_instructions)
        
        paste_input_layout = QHBoxLayout()
        
        self.paste_input = QTextEdit()
        self.paste_input.setPlaceholderText("Paste Excel column here (Ctrl+V)\nEach line will become a separate group label")
        self.paste_input.setMaximumHeight(80)
        self.paste_input.setMinimumHeight(60)
        
        self.paste_button = QPushButton("Add Labels")
        self.paste_button.clicked.connect(self._add_labels_from_paste)
        
        paste_input_layout.addWidget(self.paste_input)
        paste_input_layout.addWidget(self.paste_button)
        paste_layout.addLayout(paste_input_layout)
        
        layout.addWidget(paste_group)
        
        # Labels list section
        list_group = QGroupBox("Group Labels")
        list_layout = QVBoxLayout(list_group)
        
        self.labels_list = QListWidget()
        self.labels_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.labels_list.itemDoubleClicked.connect(self._edit_selected_item)
        list_layout.addWidget(self.labels_list)
        
        # List control buttons
        list_buttons_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self._edit_selected_item)
        self.edit_button.setEnabled(False)
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_selected_item)
        self.remove_button.setEnabled(False)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self._clear_all_labels)
        
        list_buttons_layout.addWidget(self.edit_button)
        list_buttons_layout.addWidget(self.remove_button)
        list_buttons_layout.addStretch()
        list_buttons_layout.addWidget(self.clear_button)
        
        list_layout.addLayout(list_buttons_layout)
        layout.addWidget(list_group)
        
        # Import/Export section
        import_export_group = QGroupBox("Import/Export")
        import_export_layout = QHBoxLayout(import_export_group)
        
        self.import_button = QPushButton("Import from Text")
        self.import_button.clicked.connect(self._import_from_text)
        
        self.export_button = QPushButton("Export to Text")
        self.export_button.clicked.connect(self._export_to_text)
        
        import_export_layout.addWidget(self.import_button)
        import_export_layout.addWidget(self.export_button)
        layout.addWidget(import_export_group)
        
        # Dialog buttons
        dialog_buttons_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        dialog_buttons_layout.addStretch()
        dialog_buttons_layout.addWidget(self.ok_button)
        dialog_buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(dialog_buttons_layout)
        
        # Connect signals
        self.labels_list.itemSelectionChanged.connect(self._update_button_states)
        
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
                padding-top: 10px;
                font-weight: 600;
                color: #0064FF;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 8px;
                font-size: 14px;
            }
            
            QLineEdit, QTextEdit {
                background-color: #191919;
                color: #F0F0F0;
                border: 1px solid #303030;
                padding: 8px;
                border-radius: 4px;
            }
            
            QLineEdit {
                min-height: 30px;
            }
            
            QTextEdit {
                min-height: 60px;
            }
            
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                min-height: 30px;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:disabled {
                background-color: #4A4A4A;
                color: #888888;
            }
            
            QListWidget {
                background-color: #191919;
                color: #F0F0F0;
                border: 1px solid #303030;
                border-radius: 4px;
                selection-background-color: #0064FF;
                selection-color: #FFFFFF;
                min-height: 200px;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #303030;
            }
            
            QListWidget::item:selected {
                background-color: #0064FF;
            }
        """)
        
    def _populate_list(self):
        """Populate the list widget with current labels."""
        self.labels_list.clear()
        for label in self.labels:
            item = QListWidgetItem(label)
            self.labels_list.addItem(item)
            
    def _update_button_states(self):
        """Update button states based on selection."""
        has_selection = len(self.labels_list.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.remove_button.setEnabled(has_selection)
        
    def _add_labels_from_paste(self):
        """Add multiple labels from pasted Excel column data."""
        text = self.paste_input.toPlainText().strip()
        if not text:
            return
            
        # Split by newlines and clean up each label
        labels = []
        for line in text.split('\n'):
            label = line.strip()
            if label:  # Only add non-empty labels
                labels.append(label)
        
        if not labels:
            QMessageBox.warning(self, "No Valid Labels", 
                              "No valid labels found in the pasted text.")
            return
            
        # Check for duplicates with existing labels
        duplicates = [label for label in labels if label in self.labels]
        if duplicates:
            reply = QMessageBox.question(
                self, "Duplicate Labels Found",
                f"The following labels already exist: {', '.join(duplicates[:5])}{'...' if len(duplicates) > 5 else ''}\n\n"
                "Do you want to skip duplicates and add the new labels?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            # Filter out duplicates
            labels = [label for label in labels if label not in self.labels]
        
        # Add all valid labels
        added_count = 0
        for label in labels:
            if label not in self.labels:
                self.labels.append(label)
                added_count += 1
        
        # Update the list display
        self._populate_list()
        self.labels_changed.emit(self.labels.copy())
        
        # Clear the input and show success message
        self.paste_input.clear()
        QMessageBox.information(
            self, "Labels Added", 
            f"Successfully added {added_count} new group label(s)."
        )
            
    def _add_label(self, label: str):
        """Add a new label to the list."""
        if not label.strip():
            return
            
        # Check for duplicates
        if label in self.labels:
            QMessageBox.warning(self, "Duplicate Label", 
                              f"Label '{label}' already exists.")
            return
            
        self.labels.append(label)
        item = QListWidgetItem(label)
        self.labels_list.addItem(item)
        self.labels_list.setCurrentItem(item)
        self.labels_changed.emit(self.labels.copy())
        
    def _edit_selected_item(self):
        """Edit the selected list item."""
        selected_items = self.labels_list.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        current_text = item.text()
        
        new_text, ok = QInputDialog.getText(
            self, "Edit Group Label", 
            "Enter new label:", 
            text=current_text
        )
        
        if ok and new_text.strip():
            new_text = new_text.strip()
            if new_text != current_text:
                if new_text in self.labels:
                    QMessageBox.warning(self, "Duplicate Label", 
                                      f"Label '{new_text}' already exists.")
                    return
                    
                # Update the label
                index = self.labels.index(current_text)
                self.labels[index] = new_text
                item.setText(new_text)
                self.labels_changed.emit(self.labels.copy())
                
    def _remove_selected_item(self):
        """Remove the selected list item."""
        selected_items = self.labels_list.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        label = item.text()
        
        reply = QMessageBox.question(
            self, "Remove Label",
            f"Are you sure you want to remove '{label}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.labels.remove(label)
            self.labels_list.takeItem(self.labels_list.row(item))
            self.labels_changed.emit(self.labels.copy())
            
    def _clear_all_labels(self):
        """Clear all labels from the list."""
        if not self.labels:
            return
            
        reply = QMessageBox.question(
            self, "Clear All Labels",
            "Are you sure you want to remove all group labels?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.labels.clear()
            self.labels_list.clear()
            self.labels_changed.emit(self.labels.copy())
            
    def _import_from_text(self):
        """Import labels from comma-separated text."""
        text, ok = QInputDialog.getMultiLineText(
            self, "Import Labels",
            "Enter comma-separated group labels:",
            text=", ".join(self.labels)
        )
        
        if ok and text.strip():
            # Parse comma-separated values
            new_labels = [label.strip() for label in text.split(",") if label.strip()]
            
            # Check for duplicates
            duplicates = [label for label in new_labels if label in self.labels]
            if duplicates:
                QMessageBox.warning(self, "Duplicate Labels", 
                                  f"Some labels already exist: {', '.join(duplicates)}")
                return
                
            # Add new labels
            for label in new_labels:
                if label not in self.labels:
                    self.labels.append(label)
                    
            self._populate_list()
            self.labels_changed.emit(self.labels.copy())
            
    def _export_to_text(self):
        """Export labels to comma-separated text."""
        if not self.labels:
            QMessageBox.information(self, "No Labels", "No group labels to export.")
            return
            
        text = ", ".join(self.labels)
        QInputDialog.getMultiLineText(
            self, "Export Labels",
            "Copy the following comma-separated labels:",
            text=text
        )
        
    def get_labels(self) -> List[str]:
        """Get the current list of labels."""
        return self.labels.copy()
        
    def set_labels(self, labels: List[str]):
        """Set the list of labels."""
        self.labels = labels.copy()
        self._populate_list() 