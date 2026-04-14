from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QDialogButtonBox, QListWidgetItem
)
from PySide6.QtCore import Qt
from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_PLOT_BG, COLOR_TEXT, FONT_MONO, 
    COLOR_IDENTIFIED, COLOR_TARGET
)
from csd_peak_identifier.files.client import get_remote_files

class CsdOpenDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open CSD from Server")
        self.resize(500, 600)
        self.setStyleSheet(f"background: {COLOR_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Checking server connection...")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)

        self.file_list = QListWidget()
        self.file_list.setStyleSheet(f"background: {COLOR_PLOT_BG};")
        self.file_list.itemDoubleClicked.connect(self.accept)
        
        layout.addWidget(QLabel("Available CSD Files (timestamp):"))
        layout.addWidget(self.file_list)
        
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.refresh_files)
        btn_layout.addWidget(self.refresh_btn)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Open | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        btn_layout.addWidget(self.buttons)
        layout.addLayout(btn_layout)
        
        self.refresh_files()

    def refresh_files(self):
        try:
            csd_files = get_remote_files()
            self.file_list.clear()
            for cf in csd_files:
                item = QListWidgetItem(cf.list_value)
                item.setData(Qt.UserRole, cf.filename)
                self.file_list.addItem(item)
            
            self.status_label.setText(f"SERVER: CONNECTED | FILES: {len(csd_files)}")
            self.status_label.setStyleSheet(f"color: {COLOR_IDENTIFIED}; font-weight: bold; padding: 5px;")
        except Exception as e:
            self.status_label.setText(f"SERVER: ERROR ({str(e)})")
            self.status_label.setStyleSheet(f"color: {COLOR_TARGET}; font-weight: bold; padding: 5px;")

    def get_selected_file(self):
        item = self.file_list.currentItem()
        return item.data(Qt.UserRole) if item else None
