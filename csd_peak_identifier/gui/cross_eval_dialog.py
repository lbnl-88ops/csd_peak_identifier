"""
cross_eval_dialog.py — Cross-Evaluation Comparison View

Displays a table comparing all operator evaluations for a single CSD.
Rows are unique isotopes found by any operator.
Columns are operator IDs, plus a final CONSENSUS column.

Consensus colour coding follows the functional palette in constants.py:
  FULL     -> COLOR_SUCCESS  (green)
  MAJORITY -> COLOR_CAUTION  (amber)
  SPLIT    -> COLOR_ACTION   (vermilion)
  UNIQUE   -> COLOR_MUTED    (grey)

No decorative elements. High contrast. Tactile.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from csd_peak_identifier.gui.constants import (
    FONT_SANS, FONT_MONO,
    COLOR_BG, COLOR_TEXT, COLOR_GRID, COLOR_PLOT_BG,
    COLOR_ACTION, COLOR_SUCCESS, COLOR_CAUTION, COLOR_MUTED, COLOR_INFO,
)
from csd_peak_identifier.utils.consensus import (
    analyze_consensus,
    CONSENSUS_FULL, CONSENSUS_MAJORITY, CONSENSUS_SPLIT, CONSENSUS_UNIQUE,
    STATUS_IDENTIFIED, STATUS_MAYBE,
)


# --- Cell display values -------------------------------------------------- #
_STATUS_DISPLAY = {
    STATUS_IDENTIFIED: "IDENTIFIED",
    STATUS_MAYBE:      "MAYBE",
}
_ABSENT_TEXT = "-"

# Consensus column background colours (text always white or dark per contrast)
_CONSENSUS_BG = {
    CONSENSUS_FULL:     COLOR_SUCCESS,   # green
    CONSENSUS_MAJORITY: COLOR_CAUTION,   # amber
    CONSENSUS_SPLIT:    COLOR_ACTION,    # vermilion
    CONSENSUS_UNIQUE:   COLOR_MUTED,     # grey
}
_CONSENSUS_FG = {
    CONSENSUS_FULL:     "#ffffff",
    CONSENSUS_MAJORITY: "#262626",       # dark text on amber for legibility
    CONSENSUS_SPLIT:    "#ffffff",
    CONSENSUS_UNIQUE:   "#ffffff",
}

# Status cell foreground colours within operator columns
_STATUS_FG = {
    STATUS_IDENTIFIED: COLOR_SUCCESS,
    STATUS_MAYBE:      COLOR_CAUTION,
}


# --------------------------------------------------------------------------- #
class CrossEvaluationDialog(QDialog):
    """
    Modal dialog comparing every operator's evaluation for a single CSD.

    Signals
    -------
    load_requested : Signal(str)
        Emitted when the user clicks "LOAD IN MAIN PLOT". Carries the
        csd_timestamp string so the coordinator can fetch and open the file.
    """

    load_requested = Signal(str)

    def __init__(self, csd_timestamp: str, evaluations: list, parent=None):
        """
        Parameters
        ----------
        csd_timestamp : str
            The CSD identifier (timestamp string).
        evaluations : list[dict]
            Raw list from DatabaseManager.get_all_evaluations_for_csd().
            Each dict: {'operator': str, 'isotopes': [(symbol, status, s, m, z), ...]}
        parent : QWidget, optional
        """
        super().__init__(parent)

        self.csd_timestamp = csd_timestamp
        self._evaluations = evaluations

        self.setWindowTitle(f"CROSS-EVALUATION: {csd_timestamp}")
        self.resize(820, 520)
        self.setStyleSheet(
            f"background-color: {COLOR_BG}; color: {COLOR_TEXT}; font-family: {FONT_SANS};"
        )

        self._build_ui()

    # ---------------------------------------------------------------------- #
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header row
        hdr = QLabel(f"CSD: {self.csd_timestamp}")
        hdr.setStyleSheet(
            f"font-family: {FONT_SANS}; font-weight: bold; font-size: 14px; color: {COLOR_ACTION};"
        )
        layout.addWidget(hdr)

        # Sub-header: how many operators contributed
        op_count = len(self._evaluations)
        sub = QLabel(
            f"{op_count} operator evaluation(s) on record.  "
            "Rows: unique isotopes found by any operator.  "
            "Columns: operator ID, then consensus."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 11px; color: {COLOR_TEXT};")
        layout.addWidget(sub)

        # Legend strip
        layout.addWidget(self._make_legend())

        # Main table
        self._table = self._build_table()
        layout.addWidget(self._table, 1)

        # Bottom button bar
        btn_row = QHBoxLayout()

        self._load_btn = QPushButton("LOAD IN MAIN PLOT")
        self._load_btn.setStyleSheet(
            f"""
            QPushButton {{
                font-family: {FONT_SANS};
                font-weight: bold;
                padding: 8px 22px;
                background-color: {COLOR_ACTION};
                color: white;
                border: none;
            }}
            QPushButton:hover {{ background-color: #bf5500; }}
            QPushButton:pressed {{ background-color: #9e4400; }}
            """
        )
        self._load_btn.clicked.connect(self._on_load_clicked)

        close_btn = QPushButton("CLOSE")
        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                font-family: {FONT_SANS};
                font-weight: bold;
                padding: 8px 22px;
                background-color: {COLOR_MUTED};
                color: white;
                border: none;
            }}
            QPushButton:hover {{ background-color: #7a7a7a; }}
            """
        )
        close_btn.clicked.connect(self.reject)

        btn_row.addWidget(self._load_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    # ---------------------------------------------------------------------- #
    def _make_legend(self) -> QFrame:
        """Compact inline legend strip explaining the colour codes."""
        frame = QFrame()
        frame.setStyleSheet(
            f"border: 1px solid {COLOR_GRID}; background-color: {COLOR_PLOT_BG}; padding: 6px;"
        )
        row = QHBoxLayout(frame)
        row.setSpacing(16)
        row.setContentsMargins(8, 4, 8, 4)

        def _swatch(label_text, bg, fg="#ffffff"):
            lbl = QLabel(f"  {label_text}  ")
            lbl.setStyleSheet(
                f"background-color: {bg}; color: {fg}; "
                f"font-family: {FONT_SANS}; font-weight: bold; font-size: 10px; padding: 2px 4px;"
            )
            return lbl

        row.addWidget(QLabel("CONSENSUS:"))
        row.addWidget(_swatch("FULL",     COLOR_SUCCESS))
        row.addWidget(_swatch("MAJORITY", COLOR_CAUTION, "#262626"))
        row.addWidget(_swatch("SPLIT",    COLOR_ACTION))
        row.addWidget(_swatch("UNIQUE",   COLOR_MUTED))
        row.addStretch()

        status_note = QLabel(
            f'  <span style="color:{COLOR_SUCCESS}; font-weight:bold;">IDENTIFIED</span>'
            f'  <span style="color:{COLOR_CAUTION}; font-weight:bold;">MAYBE</span>'
            f'  <span style="color:{COLOR_MUTED};">-&nbsp;=&nbsp;not&nbsp;found</span>'
        )
        status_note.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 10px;")
        status_note.setTextFormat(Qt.RichText)
        row.addWidget(status_note)

        return frame

    # ---------------------------------------------------------------------- #
    def _build_table(self) -> QTableWidget:
        """Construct and populate the comparison table."""
        consensus_data = analyze_consensus(self._evaluations)

        # Collect sorted operator list (stable, preserves DB order)
        operators = []
        seen = set()
        for ev in self._evaluations:
            op = ev.get("operator", "")
            if op and op not in seen:
                operators.append(op)
                seen.add(op)

        # Sort isotope rows by symbol for a deterministic display order
        isotope_keys = sorted(consensus_data.keys(), key=lambda k: consensus_data[k]["symbol"])

        col_headers = operators + ["CONSENSUS"]
        row_headers = [consensus_data[k]["symbol"] for k in isotope_keys]

        table = QTableWidget(len(isotope_keys), len(col_headers))
        table.setHorizontalHeaderLabels(col_headers)
        table.setVerticalHeaderLabels(row_headers)

        # Style the table shell
        table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {COLOR_PLOT_BG};
                color: {COLOR_TEXT};
                font-family: {FONT_MONO};
                font-size: 11px;
                border: 1px solid {COLOR_GRID};
                gridline-color: {COLOR_GRID};
            }}
            QHeaderView::section {{
                background-color: {COLOR_BG};
                color: {COLOR_TEXT};
                font-family: {FONT_SANS};
                font-weight: bold;
                font-size: 11px;
                padding: 4px 6px;
                border: 1px solid {COLOR_GRID};
            }}
            QTableWidget::item {{
                padding: 4px 6px;
            }}
            """
        )
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setDefaultSectionSize(26)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)

        # Build a quick lookup: operator -> isotope_key -> status_str
        op_iso_status: dict[str, dict] = {op: {} for op in operators}
        for ev in self._evaluations:
            op = ev.get("operator", "")
            if op not in op_iso_status:
                continue
            for row_tuple in ev.get("isotopes", []):
                if len(row_tuple) < 5:
                    continue
                _, status, s, m, z = row_tuple
                if s is None and m is None and z is None:
                    continue
                key = (
                    str(s).strip() if s is not None else "",
                    int(m) if m is not None else None,
                    int(z) if z is not None else None,
                )
                op_iso_status[op][key] = str(status).strip().lower()

        # Fill cells
        for row_idx, iso_key in enumerate(isotope_keys):
            info = consensus_data[iso_key]

            for col_idx, op in enumerate(operators):
                status = op_iso_status[op].get(iso_key, None)
                if status == STATUS_IDENTIFIED:
                    text = _STATUS_DISPLAY[STATUS_IDENTIFIED]
                    fg   = _STATUS_FG[STATUS_IDENTIFIED]
                elif status == STATUS_MAYBE:
                    text = _STATUS_DISPLAY[STATUS_MAYBE]
                    fg   = _STATUS_FG[STATUS_MAYBE]
                else:
                    text = _ABSENT_TEXT
                    fg   = COLOR_MUTED

                cell = QTableWidgetItem(text)
                cell.setTextAlignment(Qt.AlignCenter)
                cell.setForeground(QColor(fg))
                table.setItem(row_idx, col_idx, cell)

            # Consensus column (always last)
            consensus_level = info["consensus"]
            cons_cell = QTableWidgetItem(consensus_level)
            cons_cell.setTextAlignment(Qt.AlignCenter)
            cons_cell.setBackground(QColor(_CONSENSUS_BG[consensus_level]))
            cons_cell.setForeground(QColor(_CONSENSUS_FG[consensus_level]))
            f = QFont(FONT_SANS.split(",")[0].strip().strip("'"))
            f.setBold(True)
            cons_cell.setFont(f)
            table.setItem(row_idx, len(operators), cons_cell)

        return table

    # ---------------------------------------------------------------------- #
    def _on_load_clicked(self):
        self.load_requested.emit(self.csd_timestamp)
        self.accept()
