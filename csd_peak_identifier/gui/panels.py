from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QGroupBox, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from csd_peak_identifier.gui.constants import (
    COLOR_PLOT_BG, FONT_MONO, COLOR_TEXT, COLOR_GRID, 
    COLOR_TARGET, COLOR_ACTION, COLOR_IDENTIFIED, COLOR_MAYBE
)

class IsotopePanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Isotopes", parent)
        self.setStyleSheet(
            f"QGroupBox {{ font-family: {FONT_MONO}; color: {COLOR_TEXT}; font-weight: bold; border: 1px solid {COLOR_GRID}; margin-top: 1.5ex; }} "
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px; }}"
        )
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)
        
        # Identified List
        layout.addWidget(QLabel("Identified isotopes"))
        self.eval_list = QListWidget()
        self.eval_list.setStyleSheet(f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        layout.addWidget(self.eval_list, 2)

        # Candidate List
        self.candidate_header = QLabel("Candidate isotopes")
        layout.addWidget(self.candidate_header)
        self.candidate_list = QListWidget()
        self.candidate_list.setStyleSheet(f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        layout.addWidget(self.candidate_list, 1)

        # Button Stack
        self.button_stack = QStackedWidget()
        layout.addWidget(self.button_stack)

        # Main Buttons (Mode 0)
        self.main_btn_panel = QWidget()
        main_btn_layout = QVBoxLayout(self.main_btn_panel)
        main_btn_layout.setContentsMargins(0, 0, 0, 0)
        main_btn_layout.setSpacing(0)
        main_btn_layout.addStretch()
        
        self.remove_btn = QPushButton("Remove Identified")
        self.remove_btn.setStyleSheet(f"font-family: {FONT_MONO};")
        main_btn_layout.addWidget(self.remove_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet(f"font-family: {FONT_MONO};")
        main_btn_layout.addWidget(self.clear_btn)
        
        self.button_stack.addWidget(self.main_btn_panel)

        # ID Buttons (Mode 1)
        self.id_btn_panel = QWidget()
        id_btn_layout = QVBoxLayout(self.id_btn_panel)
        id_btn_layout.setContentsMargins(0, 0, 0, 0)
        id_btn_layout.setSpacing(0)
        id_btn_layout.addStretch()

        self.accept_btn = QPushButton("Accept Candidate (Enter)")
        self.accept_btn.setStyleSheet(f"background: {COLOR_ACTION}; color: white; font-weight: bold; font-family: {FONT_MONO};")
        id_btn_layout.addWidget(self.accept_btn)

        self.maybe_btn = QPushButton("Mark as Maybe")
        self.maybe_btn.setStyleSheet(f"font-family: {FONT_MONO};")
        id_btn_layout.addWidget(self.maybe_btn)

        self.reject_btn = QPushButton("Reject Candidate")
        self.reject_btn.setStyleSheet(f"font-family: {FONT_MONO};")
        id_btn_layout.addWidget(self.reject_btn)

        self.exit_btn = QPushButton("Exit Peak ID (Esc)")
        self.exit_btn.setStyleSheet(f"font-family: {FONT_MONO};")
        id_btn_layout.addWidget(self.exit_btn)

        self.button_stack.addWidget(self.id_btn_panel)

class PeakPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Peaks", parent)
        self.setStyleSheet(
            f"QGroupBox {{ font-family: {FONT_MONO}; color: {COLOR_TEXT}; font-weight: bold; border: 1px solid {COLOR_GRID}; margin-top: 0.5ex; }} "
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px; }}"
        )
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Detected peaks"))
        self.peak_list = QListWidget()
        self.peak_list.setStyleSheet(f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        layout.addWidget(self.peak_list, 2)

        self.search_btn = QPushButton("Identify Peak (Enter)")
        self.search_btn.setStyleSheet(f"background: {COLOR_TARGET}; color: white; font-weight: bold; font-family: {FONT_MONO};")
        layout.addWidget(self.search_btn)

        layout.addWidget(QLabel("Peak associations"))
        self.assoc_list = QListWidget()
        self.assoc_list.setStyleSheet(f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        layout.addWidget(self.assoc_list, 1)

        # Right buttons
        self.btn_panel = QWidget()
        btn_layout = QVBoxLayout(self.btn_panel)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)
        btn_layout.addStretch()

        self.remove_assoc_btn = QPushButton("Remove Association")
        self.remove_assoc_btn.setStyleSheet(f"font-family: {FONT_MONO};")
        btn_layout.addWidget(self.remove_assoc_btn)

        # placeholders for balance
        for _ in range(3):
            placeholder = QPushButton(" ")
            placeholder.setStyleSheet("border: none; background: transparent; color: transparent;")
            placeholder.setEnabled(False)
            btn_layout.addWidget(placeholder)
        
        layout.addWidget(self.btn_panel)

class InfoPanel(QLabel):
    def __init__(self, parent=None):
        super().__init__("Select a candidate to see details", parent)
        self.setStyleSheet(f"padding: 2px; font-size: 13px; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        self.setAlignment(Qt.AlignCenter)
