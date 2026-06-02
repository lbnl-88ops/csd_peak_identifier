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
    COLOR_CANDIDATE,
    COLOR_TEXT,
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

        # Global Save Button
        self.save_btn = QPushButton("SAVE EVALUATION (Ctrl+S)")
        self.save_btn.setStyleSheet(
            f"background: {COLOR_ACTION}; color: white; font-weight: bold; font-family: {FONT_SANS}; padding: 10px; margin-top: 10px;"
        )
        layout.addWidget(self.save_btn)


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
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 2, 20, 2)  # Minimal top/bottom padding
        self.main_layout.setSpacing(15)

        # Left Side: Candidate Label + Large Icon
        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)
        self.cand_title = add_label(left_layout, "CANDIDATE:")
        self.cand_title.setStyleSheet(
            f"font-family: {FONT_SANS}; font-size: 9px; font-weight: bold; color: #666666;"
        )

        self.isotope_display = add_label(left_layout, "")
        self.isotope_display.setStyleSheet(
            f"font-size: 28px; font-weight: bold; font-family: 'monospace'; color: {COLOR_CANDIDATE};"
        )
        self.main_layout.addLayout(left_layout)

        # Right Side: Isotope Details
        self.details_layout = QVBoxLayout()
        self.details_layout.setSpacing(1)
        self.details_layout.setAlignment(Qt.AlignVCenter)

        self.z_label = add_label(self.details_layout, "")
        self.abundance_label = add_label(self.details_layout, "")
        self.mass_label = add_label(self.details_layout, "")
        self.score_label = add_label(self.details_layout, "")

        label_style = f"font-family: 'monospace'; font-size: 11px; color: {COLOR_TEXT};"
        self.z_label.setStyleSheet(label_style)
        self.abundance_label.setStyleSheet(label_style)
        self.mass_label.setStyleSheet(label_style)
        self.score_label.setStyleSheet(label_style)

        self.main_layout.addLayout(self.details_layout)
        self.main_layout.addStretch()

    def set_candidate_data(self, ev, score=0.0):
        if ev:
            # Format: 48 Ca +5
            parts = ev.symbol().split("-")
            element = parts[0]
            mass = parts[1] if len(parts) > 1 else ""

            large_text = f"<sup>{mass}</sup>{element}"
            self.isotope_display.setText(large_text)

            self.z_label.setText(f"Z: {ev.z}")
            self.abundance_label.setText(f"ABUNDANCE: {ev.a:.3f}%")
            self.mass_label.setText(f"ACTUAL MASS: {ev.m:.5f} u")
            self.score_label.setText(f"MATCH SCORE: {score * 100:.1f}%")

            self.cand_title.show()
        else:
            self.isotope_display.setText("")
            self.z_label.setText("")
            self.abundance_label.setText("")
            self.mass_label.setText("")
            self.score_label.setText("Select a candidate to see details")
            self.cand_title.hide()

    def setText(self, text):
        # Kept for compatibility but not used in current layout
        pass
