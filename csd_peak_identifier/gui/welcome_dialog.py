from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QMessageBox,
    QFormLayout,
    QCheckBox,
)
from PySide6.QtCore import Qt
from .constants import (
    FONT_SANS,
    FONT_MONO,
    COLOR_BG,
    COLOR_TEXT,
    COLOR_GRID,
    COLOR_ACTION,
    COLOR_MUTED,
)
from .styles import LABEL_STYLE


class WelcomeDialog(QDialog):
    """
    Unified Welcome Screen for ECRIS System Access.
    Combines profile selection with quick-start actions.
    """

    def __init__(self, db_manager, users, last_username=None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("ECRIS SYSTEM ACCESS")
        self.setFixedWidth(450)
        self.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_TEXT};")

        self.selected_username = None
        self.action = None  # 'open', 'pending', 'random'

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QLabel("Welcome to the VENUS CSD Peak Identifier")
        header.setStyleSheet(
            f"font-family: {FONT_SANS}; font-weight: bold; font-size: 18px; color: {COLOR_ACTION};"
        )
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # User Selection Section
        user_frame = QFrame()
        user_frame.setStyleSheet(
            f"border: 1px solid {COLOR_GRID}; padding: 15px; background-color: {COLOR_BG};"
        )
        user_layout = QFormLayout(user_frame)

        self.user_combo = QComboBox()
        self.user_combo.setEditable(True)
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

        self.user_combo.currentTextChanged.connect(self.update_stats)

        user_label = QLabel("OPERATOR ID:")
        user_label.setStyleSheet(LABEL_STYLE)
        user_layout.addRow(user_label, self.user_combo)
        
        # Remote Toggle in User Frame
        remote_layout = QHBoxLayout()
        self.remote_cb = QCheckBox("USE REMOTE")
        self.remote_cb.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 11px; color: {COLOR_TEXT}; margin-top: 5px;")
        self.remote_cb.setChecked(self.db.use_remote)
        self.remote_cb.toggled.connect(self.on_remote_toggled)
        remote_layout.addWidget(self.remote_cb)
        
        self.conn_status_lbl = QLabel("")
        self.conn_status_lbl.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 10px; font-weight: bold; margin-top: 5px;")
        remote_layout.addStretch()
        remote_layout.addWidget(self.conn_status_lbl)
        
        user_layout.addRow(remote_layout)
        
        layout.addWidget(user_frame)

        # Stats Section
        stats_layout = QVBoxLayout()
        self.stats_lbl = QLabel("Total CSDs evaluated: 0")
        self.stats_lbl.setStyleSheet(
            f"font-family: {FONT_SANS}; font-size: 14px; color: {COLOR_TEXT};"
        )
        self.stats_lbl.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.stats_lbl)
        layout.addLayout(stats_layout)

        # Action Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(12)

        btn_style = f"""
            QPushButton {{
                font-family: {FONT_SANS};
                font-weight: bold;
                padding: 12px;
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

        self.open_btn = QPushButton("OPEN A CSD")
        self.open_btn.setStyleSheet(btn_style)
        self.open_btn.clicked.connect(self.select_open)
        btn_layout.addWidget(self.open_btn)

        self.pending_btn = QPushButton("EVALUATE PENDING CSD (0 REMAINING)")
        self.pending_btn.setStyleSheet(btn_style)
        self.pending_btn.clicked.connect(self.select_pending)
        btn_layout.addWidget(self.pending_btn)

        self.random_btn = QPushButton("EVALUATE RANDOM CSD")
        self.random_btn.setStyleSheet(btn_style)
        self.random_btn.clicked.connect(self.select_random)
        btn_layout.addWidget(self.random_btn)

        layout.addLayout(btn_layout)

        # Exit
        exit_layout = QHBoxLayout()
        self.exit_btn = QPushButton("EXIT SYSTEM")
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

        # Initial stats
        self.update_connection_indicator(self.db.is_connected_to_remote)
        self.update_stats()

    def on_remote_toggled(self, checked):
        connected = self.db.toggle_remote(checked)
        self.update_connection_indicator(connected)
        # Refresh the user list in the combo
        current_text = self.user_combo.currentText()
        self.user_combo.blockSignals(True)
        self.user_combo.clear()
        self.user_combo.addItems(self.db.get_all_users())
        self.user_combo.setCurrentText(current_text)
        self.user_combo.blockSignals(False)
        self.update_stats()

    def update_connection_indicator(self, connected):
        if not self.remote_cb.isChecked():
            self.conn_status_lbl.setText("")
        elif connected:
            self.conn_status_lbl.setText("CONNECTED")
            self.conn_status_lbl.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 10px; font-weight: bold; color: green; margin-top: 5px;")
        else:
            self.conn_status_lbl.setText("OFFLINE")
            self.conn_status_lbl.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 10px; font-weight: bold; color: red; margin-top: 5px;")

    def update_stats(self):
        username = self.user_combo.currentText().strip()
        if not username:
            self.stats_lbl.setText("Total CSDs evaluated: --")
            self.pending_btn.setText("EVALUATE PENDING CSD (0 REMAINING)")
            self.pending_btn.setEnabled(False)
            return

        eval_count, pending_count = self.db.get_user_stats(username)
        self.stats_lbl.setText(f"Total CSDs evaluated: {eval_count}")
        self.pending_btn.setText(f"EVALUATE PENDING CSD ({pending_count} REMAINING)")
        self.pending_btn.setEnabled(pending_count > 0)

    def select_open(self):
        if self._validate_user():
            self.action = "open"
            self.accept()

    def select_pending(self):
        if self._validate_user():
            self.action = "pending"
            self.accept()

    def select_random(self):
        if self._validate_user():
            self.action = "random"
            self.accept()

    def _validate_user(self):
        username = self.user_combo.currentText().strip()
        if not username:
            QMessageBox.warning(self, "ERROR", "OPERATOR ID REQUIRED")
            return False
        self.selected_username = username
        return True

    def get_action_details(self):
        return self.selected_username, self.action, self.remote_cb.isChecked()
