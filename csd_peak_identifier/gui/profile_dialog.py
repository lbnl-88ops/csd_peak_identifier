from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QLineEdit, QFormLayout, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from .constants import FONT_SANS, FONT_MONO, COLOR_BG, COLOR_TEXT, COLOR_GRID, COLOR_ACTION
from .styles import BUTTON_STYLE, LABEL_STYLE

class ProfileDialog(QDialog):
    """
    Dialog for selecting or creating a user profile.
    Following the 'Cassette Futurism' aesthetic: functional, high-contrast, tactile.
    """
    
    def __init__(self, users, last_username=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("USER PROFILE SELECTION")
        self.setFixedWidth(400)
        self.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_TEXT};")
        
        self.selected_username = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header - tactile feel
        header = QLabel("SYSTEM ACCESS: PROFILE")
        header.setStyleSheet(f"font-family: {FONT_SANS}; font-weight: bold; font-size: 14px; color: {COLOR_ACTION};")
        layout.addWidget(header)
        
        # Frame for selection
        frame = QFrame()
        frame.setStyleSheet(f"border: 1px solid {COLOR_GRID}; padding: 10px;")
        frame_layout = QFormLayout(frame)
        
        self.user_combo = QComboBox()
        self.user_combo.setEditable(True)
        self.user_combo.setStyleSheet(f"""
            QComboBox {{
                font-family: {FONT_MONO};
                background-color: white;
                border: 1px solid {COLOR_GRID};
                padding: 4px;
            }}
            QComboBox::drop-down {{
                border-left: 1px solid {COLOR_GRID};
            }}
        """)
        
        self.user_combo.addItems(users)
        
        if last_username and last_username in users:
            self.user_combo.setCurrentText(last_username)
        elif users:
            self.user_combo.setCurrentIndex(0)
            
        label = QLabel("OPERATOR ID:")
        label.setStyleSheet(LABEL_STYLE)
        frame_layout.addRow(label, self.user_combo)
        
        layout.addWidget(frame)
        
        # Instructions
        instr = QLabel("Select existing operator or enter a new designation.")
        instr.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 10px; color: {COLOR_TEXT};")
        instr.setWordWrap(True)
        layout.addWidget(instr)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("LOGIN")
        self.select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACTION};
                color: white;
                font-family: {FONT_SANS};
                font-weight: bold;
                padding: 6px 15px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #e67e22;
            }}
        """)
        self.select_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setStyleSheet(BUTTON_STYLE)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.select_btn)
        
        layout.addLayout(btn_layout)
        
    def accept(self):
        username = self.user_combo.currentText().strip()
        if not username:
            QMessageBox.warning(self, "ERROR", "OPERATOR ID REQUIRED")
            return
        
        self.selected_username = username
        super().accept()

    def get_selected_username(self):
        return self.selected_username
