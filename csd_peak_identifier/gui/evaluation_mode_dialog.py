from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from .constants import FONT_SANS, COLOR_BG, COLOR_TEXT, COLOR_GRID, COLOR_ACTION, COLOR_MUTED
from .styles import BUTTON_STYLE

class EvaluationModeDialog(QDialog):
    """
    Dialog for Evaluation Mode status and actions.
    Tactile, functional layout.
    """
    
    def __init__(self, username, eval_count, pending_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EVALUATION MODE")
        self.setFixedWidth(450)
        self.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_TEXT};")
        
        self.action = None # 'pending', 'random', or None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header
        header = QLabel("EVALUATION STATUS")
        header.setStyleSheet(f"font-family: {FONT_SANS}; font-weight: bold; font-size: 16px; color: {COLOR_ACTION};")
        layout.addWidget(header)
        
        # Info Panel
        info_frame = QFrame()
        info_frame.setStyleSheet(f"border: 1px solid {COLOR_GRID}; padding: 15px; background-color: {COLOR_BG};")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(10)
        
        user_lbl = QLabel(f"OPERATOR: {username}")
        user_lbl.setStyleSheet(f"font-family: {FONT_SANS}; font-weight: bold; color: {COLOR_TEXT};")
        info_layout.addWidget(user_lbl)
        
        count_lbl = QLabel(f"TOTAL CSDs EVALUATED: {eval_count}")
        count_lbl.setStyleSheet(f"font-family: {FONT_SANS}; color: {COLOR_TEXT};")
        info_layout.addWidget(count_lbl)
        
        layout.addWidget(info_frame)
        
        # Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)
        
        # Shared button style
        btn_style = f"""
            QPushButton {{
                font-family: {FONT_SANS};
                font-weight: bold;
                padding: 10px;
                border: 1px solid {COLOR_GRID};
                background-color: {COLOR_BG};
                color: {COLOR_TEXT};
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {COLOR_GRID};
            }}
            QPushButton:disabled {{
                color: {COLOR_MUTED};
                border-color: {COLOR_GRID};
                background-color: #eeeeee;
            }}
        """
        
        self.pending_btn = QPushButton(f"EVALUATE PENDING CSD ({pending_count} REMAINING)")
        self.pending_btn.setStyleSheet(btn_style)
        self.pending_btn.setEnabled(pending_count > 0)
        self.pending_btn.clicked.connect(self.select_pending)
        btn_layout.addWidget(self.pending_btn)
        
        self.random_btn = QPushButton("EVALUATE RANDOM CSD")
        self.random_btn.setStyleSheet(btn_style)
        self.random_btn.clicked.connect(self.select_random)
        btn_layout.addWidget(self.random_btn)
        
        layout.addLayout(btn_layout)
        
        # Exit Button
        exit_layout = QHBoxLayout()
        self.exit_btn = QPushButton("EXIT")
        self.exit_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: {FONT_SANS};
                font-weight: bold;
                padding: 8px 20px;
                background-color: {COLOR_MUTED};
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #7a7a7a;
            }}
        """)
        self.exit_btn.clicked.connect(self.reject)
        exit_layout.addStretch()
        exit_layout.addWidget(self.exit_btn)
        layout.addLayout(exit_layout)
        
    def select_pending(self):
        self.action = 'pending'
        self.accept()
        
    def select_random(self):
        self.action = 'random'
        self.accept()
        
    def get_action(self):
        return self.action
