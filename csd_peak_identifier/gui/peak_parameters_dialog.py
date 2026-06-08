from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QMessageBox,
)
from PySide6.QtGui import QDoubleValidator, QPixmap
from PySide6.QtCore import Qt
from csd_peak_identifier.gui.constants import (
    COLOR_BG,
    COLOR_TEXT,
    COLOR_GRID,
    COLOR_ACTION,
    FONT_SANS,
    FONT_MONO,
    get_resource_path,
)
from csd_peak_identifier.logic import PeakParameters


class PeakParametersDialog(QDialog):
    def __init__(self, current_params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PEAK SEARCH PARAMETERS")
        self.setFixedWidth(500)  # Increased width for image
        self.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_TEXT};")

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("ANALYSIS CONFIGURATION")
        header.setStyleSheet(
            f"font-family: {FONT_SANS}; font-weight: bold; font-size: 16px;"
        )
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Add visual guide image
        img_path = get_resource_path("data/peak_description.png")
        if img_path.exists():
            img_label = QLabel()
            pixmap = QPixmap(str(img_path))
            # Scale image to fit width while maintaining aspect ratio
            scaled_pixmap = pixmap.scaledToWidth(460, Qt.SmoothTransformation)
            img_label.setPixmap(scaled_pixmap)
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setStyleSheet(
                f"border: 1px solid {COLOR_GRID}; background: white; padding: 5px;"
            )
            layout.addWidget(img_label)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(10)

        validator = QDoubleValidator(self)
        validator.setNotation(QDoubleValidator.StandardNotation)

        edit_style = f"font-family: {FONT_MONO}; padding: 5px; border: 1px solid {COLOR_GRID}; background: white;"

        self.min_height = QLineEdit(str(current_params.min_height))
        self.min_height.setValidator(validator)
        self.min_height.setStyleSheet(edit_style)

        self.max_height = QLineEdit(
            str(current_params.max_height)
            if current_params.max_height is not None
            else ""
        )
        self.max_height.setValidator(validator)
        self.max_height.setPlaceholderText("None")
        self.max_height.setStyleSheet(edit_style)

        self.threshold = QLineEdit(
            str(current_params.threshold)
            if current_params.threshold is not None
            else ""
        )
        self.threshold.setValidator(validator)
        self.threshold.setPlaceholderText("None")
        self.threshold.setStyleSheet(edit_style)

        self.distance = QLineEdit(
            str(current_params.distance) if current_params.distance is not None else ""
        )
        self.distance.setValidator(validator)
        self.distance.setPlaceholderText("None")
        self.distance.setStyleSheet(edit_style)

        self.prominence = QLineEdit(
            str(current_params.prominance)
            if current_params.prominance is not None
            else ""
        )
        self.prominence.setValidator(validator)
        self.prominence.setPlaceholderText("None")
        self.prominence.setStyleSheet(edit_style)
 
        label_style = f"font-family: {FONT_SANS}; font-weight: bold; font-size: 11px;"
 
        def add_param_row(layout_target, label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            layout_target.addRow(lbl, widget)
 
        add_param_row(form_layout, "MIN HEIGHT (μA):", self.min_height)
        add_param_row(form_layout, "MAX HEIGHT (μA):", self.max_height)
        add_param_row(form_layout, "THRESHOLD (μA):", self.threshold)
        add_param_row(form_layout, "DISTANCE (m/q):", self.distance)
        add_param_row(form_layout, "PROMINENCE (μA):", self.prominence)
 
        layout.addLayout(form_layout)
 
        # Candidate Evaluation Section
        cand_header = QLabel("CANDIDATE EVALUATION")
        cand_header.setStyleSheet(
            f"font-family: {FONT_SANS}; font-weight: bold; font-size: 13px; color: {COLOR_ACTION}; margin-top: 10px;"
        )
        cand_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(cand_header)
 
        cand_form = QFormLayout()
        cand_form.setLabelAlignment(Qt.AlignRight)
        cand_form.setSpacing(10)
        
        self.mq_tolerance = QLineEdit(str(current_params.mq_tolerance))
        self.mq_tolerance.setValidator(validator)
        self.mq_tolerance.setStyleSheet(edit_style)
        
        add_param_row(cand_form, "M/Q TOLERANCE (m/q):", self.mq_tolerance)
        
        layout.addLayout(cand_form)

        cand_info = QLabel("Affects how peaks are assigned to elements. This tolerance is the maximum difference between the calculated isotope M/Q and the peak M/Q.")
        cand_info.setWordWrap(True)
        cand_info.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 9px; color: #666666; font-style: italic; margin-left: 20px; margin-right: 20px;")
        layout.addWidget(cand_info)
 
        layout.addStretch() # Ensure alignment
 
        info_label = QLabel("(Leave empty for 'None' / Auto-calculate)")
        info_label.setStyleSheet(
            f"font-family: {FONT_SANS}; font-size: 9px; color: #666666;"
        )
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("SAVE")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: {FONT_SANS}; font-weight: bold; padding: 10px;
                background-color: {COLOR_TEXT}; color: white; border: none;
            }}
            QPushButton:hover {{ background-color: #444444; }}
        """)
        self.save_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: {FONT_SANS}; font-weight: bold; padding: 10px;
                background-color: #cccccc; color: black; border: none;
            }}
            QPushButton:hover {{ background-color: #bbbbbb; }}
        """)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def get_params(self):
        def parse_float(le):
            txt = le.text().strip()
            return float(txt) if txt else None

        return PeakParameters(
            min_height=parse_float(self.min_height) or 0.2,
            max_height=parse_float(self.max_height),
            threshold=parse_float(self.threshold),
            distance=parse_float(self.distance),
            prominance=parse_float(
                self.prominence
            ),  # Note: logic.py spelling is 'prominance'
            mq_tolerance=parse_float(self.mq_tolerance) or 0.03,
        )
