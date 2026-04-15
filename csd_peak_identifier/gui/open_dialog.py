from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QDialogButtonBox, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_IDENTIFIED, COLOR_TARGET, COLOR_TEXT
)
from csd_peak_identifier.gui.styles import LIST_STYLE, LABEL_STYLE, add_button, add_label
from csd_peak_identifier.files.client import get_remote_files

class CsdOpenDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open CSD from Server")
        self.resize(500, 600)
        self.setStyleSheet(f"background: {COLOR_BG};")
        self.create_widgets()
        
        # Manifest immediately, then begin the connection ritual after a short delay
        # to ensure the UI is rendered and responsive to the user's eyes.
        QTimer.singleShot(100, self.refresh_files)

    def create_widgets(self):
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("INITIALIZING CONNECTION...")
        self.status_label.setStyleSheet(LABEL_STYLE + " font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)

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
        self.buttons.setStyleSheet(f"font-family: 'Segoe UI', sans-serif;")
        
        btn_layout.addWidget(self.buttons)
        layout.addLayout(btn_layout)

    def refresh_files(self):
        self.status_label.setText("SERVER: ATTEMPTING CONNECTION...")
        self.status_label.setStyleSheet(LABEL_STYLE + f" font-weight: bold; padding: 5px; color: {COLOR_TEXT};")
        self.refresh_btn.setEnabled(False)
        self.buttons.button(QDialogButtonBox.Open).setEnabled(False)
        
        # Process events to show the status update before blocking
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            csd_files = get_remote_files()
            self.file_list.clear()
            for cf in csd_files:
                item = QListWidgetItem(cf.list_value)
                item.setData(Qt.UserRole, cf.filename)
                self.file_list.addItem(item)
            
            self.status_label.setText(f"SERVER: CONNECTED | FILES: {len(csd_files)}")
            self.status_label.setStyleSheet(LABEL_STYLE + f" font-weight: bold; padding: 5px; color: {COLOR_IDENTIFIED};")
        except Exception as e:
            self.status_label.setText(f"SERVER: ERROR ({str(e)})")
            self.status_label.setStyleSheet(LABEL_STYLE + f" font-weight: bold; padding: 5px; color: {COLOR_TARGET};")
        
        self.refresh_btn.setEnabled(True)
        self.buttons.button(QDialogButtonBox.Open).setEnabled(True)

    def get_selected_file(self):
        item = self.file_list.currentItem()
        return item.data(Qt.UserRole) if item else None
