from PySide6.QtWidgets import (
    QLayout,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QGroupBox,
    QStackedWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from csd_peak_identifier.gui.constants import (
    COLOR_PLOT_BG,
    FONT_MONO,
    FONT_SANS,
    COLOR_TEXT,
    COLOR_GRID,
    COLOR_TARGET,
    COLOR_ACTION,
    COLOR_IDENTIFIED,
    COLOR_MAYBE,
)

GROUP_BOX_STYLE = f"""QGroupBox {{ font-family: {FONT_SANS}; color: {COLOR_TEXT}; font-weight: bold; border: 1px solid {COLOR_GRID}; margin-top: 1.2ex; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 0px; }}
    """
LABEL_STYLE = f"font-family: {FONT_SANS}; font-size: 11px; color: {COLOR_TEXT};"
LIST_STYLE = (
    f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};"
)
BUTTON_STYLE = f"font-family: {FONT_SANS};"


def add_button_to_layout(layout: QLayout, text: str) -> QPushButton:
    button = QPushButton(text)
    button.setStyleSheet(BUTTON_STYLE)
    layout.addWidget(button)
    return button


def add_label_to_layout(layout: QLayout, text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(LABEL_STYLE)
    layout.addWidget(label)
    return label


class IsotopePanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Isotopes", parent)
        self.setStyleSheet(GROUP_BOX_STYLE)
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)

        # Identified List
        add_label_to_layout(layout, "Identified isotopes")
        self.eval_list = QListWidget()
        self.eval_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.eval_list, 2)

        # Action buttons for Identified list
        self.eval_btn_widget = QWidget()
        self.eval_btn_layout = QHBoxLayout(self.eval_btn_widget)
        self.eval_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.remove_btn = add_button_to_layout(self.eval_btn_layout, "Remove")
        self.clear_btn = add_button_to_layout(self.eval_btn_layout, "Clear all")

        # self.remove_btn = QPushButton("Remove")
        # self.remove_btn.setStyleSheet(BUTTON_STYLE)
        # self.clear_btn = QPushButton("Clear All")
        # self.clear_btn.setStyleSheet(BUTTON_STYLE)
        # self.eval_btn_layout.addWidget(self.remove_btn)
        # self.eval_btn_layout.addWidget(self.clear_btn)
        layout.addWidget(self.eval_btn_widget)

        # Candidate List
        self.candidate_header = QLabel("Candidate isotopes")
        self.candidate_header.setStyleSheet(LABEL_STYLE)
        layout.addWidget(self.candidate_header)
        self.candidate_list = QListWidget()
        self.candidate_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.candidate_list, 1)

        # Button Stack (Mode-specific actions)
        self.button_stack = QStackedWidget()
        layout.addWidget(self.button_stack)

        # Main Buttons (Mode 0)
        self.main_btn_panel = QWidget()
        main_btn_layout = QVBoxLayout(self.main_btn_panel)
        main_btn_layout.setContentsMargins(0, 0, 0, 0)
        main_btn_layout.setSpacing(0)

        self.add_isotope_btn = QPushButton("Add isotope...")
        self.add_isotope_btn.setStyleSheet(BUTTON_STYLE)
        main_btn_layout.addWidget(self.add_isotope_btn)
        main_btn_layout.addStretch()  # Ensure alignment
        self.button_stack.addWidget(self.main_btn_panel)

        # ID Buttons (Mode 1)
        self.id_btn_panel = QWidget()
        id_btn_layout = QVBoxLayout(self.id_btn_panel)
        id_btn_layout.setContentsMargins(0, 0, 0, 0)
        id_btn_layout.setSpacing(0)

        self.accept_btn = QPushButton("Accept (Enter)")
        self.accept_btn.setStyleSheet(
            f"background: {COLOR_ACTION}; color: white; font-weight: bold; font-family: {FONT_SANS};"
        )
        id_btn_layout.addWidget(self.accept_btn)

        self.maybe_btn = QPushButton("Mark as maybe (M)")
        self.maybe_btn.setStyleSheet(BUTTON_STYLE)
        id_btn_layout.addWidget(self.maybe_btn)

        self.reject_btn = QPushButton("Reject (N)")
        self.reject_btn.setStyleSheet(BUTTON_STYLE)
        id_btn_layout.addWidget(self.reject_btn)

        self.exit_btn = QPushButton("Exit (Esc)")
        self.exit_btn.setStyleSheet(BUTTON_STYLE)
        id_btn_layout.addWidget(self.exit_btn)

        self.button_stack.addWidget(self.id_btn_panel)


class PeakPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Peaks", parent)
        self.setStyleSheet(GROUP_BOX_STYLE)
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)

        label1 = QLabel("Detected peaks")
        label1.setStyleSheet(LABEL_STYLE)
        layout.addWidget(label1)
        self.peak_list = QListWidget()
        self.peak_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.peak_list, 2)

        # Action button for peaks list
        self.peak_btn_widget = QWidget()
        self.peak_btn_layout = QHBoxLayout(self.peak_btn_widget)
        self.peak_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.search_btn = QPushButton("Identify peak (Enter)")
        self.search_btn.setStyleSheet(
            f"background: {COLOR_TARGET}; color: white; font-weight: bold; font-family: {FONT_SANS};"
        )
        self.peak_btn_layout.addWidget(self.search_btn)
        layout.addWidget(self.peak_btn_widget)

        label2 = QLabel("Peak associations")
        label2.setStyleSheet(LABEL_STYLE)
        layout.addWidget(label2)
        self.assoc_list = QListWidget()
        self.assoc_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.assoc_list, 1)

        # Right actions
        self.assoc_btn_widget = QWidget()
        self.assoc_btn_layout = QVBoxLayout(self.assoc_btn_widget)
        self.assoc_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.assoc_btn_layout.setSpacing(0)

        self.remove_assoc_btn = QPushButton("Remove Association")
        self.remove_assoc_btn.setStyleSheet(BUTTON_STYLE)
        self.assoc_btn_layout.addWidget(self.remove_assoc_btn)
        self.assoc_btn_layout.addStretch()

        layout.addWidget(self.assoc_btn_widget)


class InfoPanel(QLabel):
    def __init__(self, parent=None):
        super().__init__("Select a candidate to see details", parent)
        self.setStyleSheet(
            f"padding: 2px; font-size: 13px; font-family: {FONT_SANS}; color: {COLOR_TEXT};"
        )
        self.setAlignment(Qt.AlignCenter)
