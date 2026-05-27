from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout, QLabel
)
from PySide6.QtCore import QSettings
from csd_peak_identifier.gui.constants import FONT_SANS, COLOR_BG, COLOR_TEXT

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setFixedSize(300, 150)
        self.settings = QSettings("LBNL", "CsdPeakIdentifier")
        self.create_widgets()

    def create_widgets(self):
        self.setStyleSheet(f"background: {COLOR_BG}; font-family: {FONT_SANS}; color: {COLOR_TEXT};")
        layout = QVBoxLayout(self)

        self.auto_update_cb = QCheckBox("Check for updates automatically on startup")
        self.auto_update_cb.setChecked(self.settings.value("auto_update_check", True, type=bool))
        layout.addWidget(self.auto_update_cb)

        self.use_remote_cb = QCheckBox("Use remote shared database (VPN required)")
        self.use_remote_cb.setChecked(self.settings.value("use_remote_db", False, type=bool))
        layout.addWidget(self.use_remote_cb)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_settings(self):
        self.settings.setValue("auto_update_check", self.auto_update_cb.isChecked())
        self.settings.setValue("use_remote_db", self.use_remote_cb.isChecked())
        self.accept()
