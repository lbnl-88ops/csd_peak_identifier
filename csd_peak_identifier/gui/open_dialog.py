from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QDialogButtonBox, QListWidgetItem
)
from PySide6.QtCore import Qt
from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_IDENTIFIED, COLOR_TARGET
)
from csd_peak_identifier.gui.styles import LIST_STYLE, add_button, add_label
from csd_peak_identifier.files.client import get_remote_files

class CsdOpenDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open CSD from Server")
        self.resize(500, 600)
        self.setStyleSheet(f"background: {COLOR_BG};")
        self.create_widgets()
        self.refresh_files()

    def create_widgets(self):
        layout = QVBoxLayout(self)
        
        self.status_label = add_label(layout, "Checking server connection...")
        self.status_label.setStyleSheet(self.status_label.styleSheet() + " font-weight: bold; padding: 5px;")

        add_label(layout, "Available CSD files (timestamp):")
        self.file_list = QListWidget()
        self.file_list.setStyleSheet(LIST_STYLE)
        self.file_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.file_list)
        
        btn_layout = QHBoxLayout()
        self.refresh_btn = add_button(btn_layout, "Refresh List")
        self.refresh_btn.clicked.connect(self.refresh_files)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Open | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        # Style the buttons in the button box is harder, but we can set the style on the box
        self.buttons.setStyleSheet(f"font-family: 'Segoe UI', sans-serif;")
        
        btn_layout.addWidget(self.buttons)
        layout.addLayout(btn_layout)

    def refresh_files(self):
        try:
            csd_files = get_remote_files()
            self.file_list.clear()
            for cf in csd_files:
                item = QListWidgetItem(cf.list_value)
                item.setData(Qt.UserRole, cf.filename)
                self.file_list.addItem(item)
            
            self.status_label.setText(f"SERVER: CONNECTED | FILES: {len(csd_files)}")
            self.status_label.setStyleSheet(self.status_label.styleSheet() + f" color: {COLOR_IDENTIFIED};")
        except Exception as e:
            self.status_label.setText(f"SERVER: ERROR ({str(e)})")
            self.status_label.setStyleSheet(self.status_label.styleSheet() + f" color: {COLOR_TARGET};")

    def get_selected_file(self):
        item = self.file_list.currentItem()
        return item.data(Qt.UserRole) if item else None
