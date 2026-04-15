from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QGroupBox,
    QStackedWidget,
    QPushButton,
)
from PySide6.QtCore import Qt
from csd_peak_identifier.gui.constants import (
    FONT_SANS,
    COLOR_ACTION,
    COLOR_TARGET,
)
from csd_peak_identifier.gui.styles import (
    GROUP_BOX_STYLE,
    LIST_STYLE,
    BUTTON_STYLE,
    add_button,
    add_label,
)


class IsotopePanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Isotopes", parent)
        self.setStyleSheet(GROUP_BOX_STYLE)
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)

        # Identified List
        add_label(layout, "Identified isotopes")
        self.eval_list = QListWidget()
        self.eval_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.eval_list, 4)

        # Action buttons for Identified list
        self.eval_btn_widget = QWidget()
        self.eval_btn_layout = QHBoxLayout(self.eval_btn_widget)
        # self.eval_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.remove_btn = add_button(self.eval_btn_layout, "Remove")
        self.clear_btn = add_button(self.eval_btn_layout, "Clear all")
        layout.addWidget(self.eval_btn_widget, 1)

        # Candidate List
        self.candidate_header = add_label(layout, "Candidate isotopes")
        self.candidate_list = QListWidget()
        self.candidate_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.candidate_list, 2)

        # Button Stack (Mode-specific actions)
        self.button_stack = QStackedWidget()
        layout.addWidget(self.button_stack, 1)

        # Main Buttons (Mode 0)
        self.main_btn_panel = QWidget()
        main_btn_layout = QVBoxLayout(self.main_btn_panel)
        # main_btn_layout.setContentsMargins(0, 0, 0, 0)
        main_btn_layout.setSpacing(0)

        self.add_isotope_btn = add_button(main_btn_layout, "Add isotope...")
        # main_btn_layout.addStretch()  # Ensure alignment
        self.button_stack.addWidget(self.main_btn_panel)

        # ID Buttons (Mode 1)
        self.id_btn_panel = QWidget()
        id_btn_layout = QVBoxLayout(self.id_btn_panel)
        # id_btn_layout.setContentsMargins(0, 0, 0, 0)
        id_btn_layout.setSpacing(0)

        self.accept_btn = QPushButton("Accept (Enter)")
        self.accept_btn.setStyleSheet(
            f"background: {COLOR_ACTION}; color: white; font-weight: bold; font-family: {FONT_SANS};"
        )
        id_btn_layout.addWidget(self.accept_btn)

        self.maybe_btn = add_button(id_btn_layout, "Mark as maybe (M)")
        self.reject_btn = add_button(id_btn_layout, "Reject (N)")
        self.exit_btn = add_button(id_btn_layout, "Exit (Esc)")

        self.button_stack.addWidget(self.id_btn_panel)


class PeakPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Peaks", parent)
        self.setStyleSheet(GROUP_BOX_STYLE)
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)

        add_label(layout, "Detected peaks [m/q | μA]")
        self.peak_list = QListWidget()
        self.peak_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.peak_list, 4)

        # Action button for peaks list
        self.peak_btn_widget = QWidget()
        self.peak_btn_layout = QHBoxLayout(self.peak_btn_widget)
        # self.peak_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.search_btn = QPushButton("Identify peak (Enter)")
        self.search_btn.setStyleSheet(
            f"background: {COLOR_TARGET}; color: white; font-weight: bold; font-family: {FONT_SANS};"
        )
        self.peak_btn_layout.addWidget(self.search_btn)
        layout.addWidget(self.peak_btn_widget, 1)

        add_label(layout, "Peak associations")
        self.assoc_list = QListWidget()
        self.assoc_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.assoc_list, 2)

        # Right actions
        self.assoc_btn_widget = QWidget()
        self.assoc_btn_layout = QVBoxLayout(self.assoc_btn_widget)
        # self.assoc_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.assoc_btn_layout.setSpacing(0)

        self.remove_assoc_btn = add_button(self.assoc_btn_layout, "Remove Association")
        # self.assoc_btn_layout.addStretch()

        layout.addWidget(self.assoc_btn_widget, 1)


class InfoPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = add_label(layout, "Select a candidate to see details")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            self.label.styleSheet() + " font-size: 13px; padding: 2px;"
        )

    def setText(self, text):
        self.label.setText(text)
