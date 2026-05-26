from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QLineEdit, QFormLayout, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from .constants import FONT_SANS, FONT_MONO, COLOR_BG, COLOR_TEXT, COLOR_GRID, COLOR_ACTION, COLOR_MUTED
from .styles import LABEL_STYLE

class ProfileDialog(QDialog):
    """
    Dialog for selecting or creating a user profile.
    Following the 'Cassette Futurism' aesthetic: functional, high-contrast, tactile.
    """
    
    def __init__(self, users, last_username=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ECRIS SYSTEM ACCESS")
        self.setFixedWidth(400)
        self.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_TEXT};")
        
        self.selected_username = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Instructions
        instr = QLabel("Select existing operator or enter a new designation.")
        instr.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 11px; color: {COLOR_TEXT}; margin-bottom: 5px;")
        instr.setWordWrap(True)
        layout.addWidget(instr)
        
        # Frame for selection
        frame = QFrame()
        frame.setStyleSheet(f"border: 1px solid {COLOR_GRID}; padding: 15px; background-color: {COLOR_BG};")
        frame_layout = QFormLayout(frame)
        frame_layout.setVerticalSpacing(10)
        
        self.user_combo = QComboBox()
        self.user_combo.setEditable(True)
        # Fixed QSS to show a distinct triangle for the arrow
        self.user_combo.setStyleSheet(f"""
            QComboBox {{
                font-family: {FONT_MONO};
                background-color: white;
                border: 1px solid {COLOR_GRID};
                padding: 5px;
                color: {COLOR_TEXT};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid {COLOR_GRID};
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 9px solid {COLOR_TEXT};
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
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # Shared tactile button style
        base_btn_style = f"""
            QPushButton {{
                font-family: {FONT_SANS};
                font-weight: bold;
                padding: 8px 20px;
                border: 1px solid {COLOR_GRID};
            }}
        """
        
        self.select_btn = QPushButton("LOGIN")
        self.select_btn.setDefault(True) # Pressing Enter will trigger this
        self.select_btn.setStyleSheet(base_btn_style + f"""
            QPushButton {{
                background-color: {COLOR_ACTION};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #e67e22;
            }}
            QPushButton:pressed {{
                background-color: #bf5500;
            }}
        """)
        self.select_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setStyleSheet(base_btn_style + f"""
            QPushButton {{
                background-color: {COLOR_BG};
                color: {COLOR_TEXT};
            }}
            QPushButton:hover {{
                background-color: {COLOR_GRID};
            }}
        """)
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
