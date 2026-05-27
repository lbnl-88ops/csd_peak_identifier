"""
analysis_dashboard.py — Lab-Wide Analysis Dashboard

Three-panel overview of all evaluations recorded in the database:

  LEFT   — TOP EVALUATORS: ranked leaderboard by evaluation count.
  CENTER — EVALUATED CSDs: scrollable list of every CSD with at least
           one evaluation.  Click any row to open the CrossEvaluationDialog
           for that CSD.
  RIGHT  — QUICK STATS: headline numbers at a glance.

Aesthetic: Cassette Futurism.  No gradients, no animations, no decoration.
High-contrast, monospaced data, clear affordances.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from csd_peak_identifier.gui.constants import (
    FONT_SANS, FONT_MONO,
    COLOR_BG, COLOR_TEXT, COLOR_GRID, COLOR_PLOT_BG,
    COLOR_ACTION, COLOR_SUCCESS, COLOR_MUTED, COLOR_INFO,
)
from csd_peak_identifier.gui.cross_eval_dialog import CrossEvaluationDialog


# Rank medals — plain text, no emoji. High-contrast ordinals.
_RANK_LABELS = ["#1", "#2", "#3"]


def _section_label(text: str) -> QLabel:
    """Styled section heading."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-family: {FONT_SANS}; font-weight: bold; font-size: 12px; "
        f"color: {COLOR_ACTION}; padding-bottom: 4px;"
    )
    return lbl


def _panel_frame() -> QFrame:
    """Framed container matching the chassis aesthetic."""
    frame = QFrame()
    frame.setStyleSheet(
        f"border: 1px solid {COLOR_GRID}; background-color: {COLOR_PLOT_BG};"
    )
    frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return frame


def _stat_row(label: str, value: str) -> QHBoxLayout:
    """Key/value row for the stats panel."""
    row = QHBoxLayout()
    key_lbl = QLabel(label)
    key_lbl.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 11px; color: {COLOR_TEXT}; border: none;")
    val_lbl = QLabel(value)
    val_lbl.setStyleSheet(
        f"font-family: {FONT_MONO}; font-size: 12px; font-weight: bold; "
        f"color: {COLOR_INFO}; border: none;"
    )
    val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    row.addWidget(key_lbl)
    row.addStretch()
    row.addWidget(val_lbl)
    return row


# --------------------------------------------------------------------------- #
class AnalysisDashboard(QDialog):
    """
    Lab-wide analysis dashboard.

    Signals
    -------
    load_csd_requested : Signal(str)
        Forwarded from CrossEvaluationDialog when the user requests that a
        specific CSD be loaded in the main plot.
    """

    load_csd_requested = Signal(str)

    def __init__(self, db, parent=None):
        """
        Parameters
        ----------
        db : DatabaseManager
            Live database handle.  The dashboard calls read-only methods only.
        parent : QWidget, optional
        """
        super().__init__(parent)

        self._db = db

        self.setWindowTitle("ANALYSIS DASHBOARD — LAB-WIDE EVALUATION SUMMARY")
        self.resize(960, 580)
        self.setStyleSheet(
            f"background-color: {COLOR_BG}; color: {COLOR_TEXT}; font-family: {FONT_SANS};"
        )

        self._build_ui()

    # ---------------------------------------------------------------------- #
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(20, 20, 20, 20)

        # Page header
        hdr = QLabel("ANALYSIS DASHBOARD")
        hdr.setStyleSheet(
            f"font-family: {FONT_SANS}; font-weight: bold; font-size: 16px; color: {COLOR_ACTION};"
        )
        root.addWidget(hdr)

        sub = QLabel(
            "Click any CSD entry to review cross-operator evaluations.  "
            "Data reflects the currently active database."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 11px; color: {COLOR_TEXT};")
        root.addWidget(sub)

        # Three-panel body
        body = QHBoxLayout()
        body.setSpacing(14)

        body.addLayout(self._make_leaderboard_panel(), 2)
        body.addLayout(self._make_csd_list_panel(), 4)
        body.addLayout(self._make_stats_panel(), 2)

        root.addLayout(body, 1)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("CLOSE")
        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                font-family: {FONT_SANS};
                font-weight: bold;
                padding: 8px 24px;
                background-color: {COLOR_MUTED};
                color: white;
                border: none;
            }}
            QPushButton:hover {{ background-color: #7a7a7a; }}
            """
        )
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    # ---------------------------------------------------------------------- #
    def _make_leaderboard_panel(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(_section_label("TOP EVALUATORS"))

        leaderboard = self._db.get_leaderboard() or []

        frame = _panel_frame()
        fl = QVBoxLayout(frame)
        fl.setSpacing(8)
        fl.setContentsMargins(12, 10, 12, 10)

        if not leaderboard:
            empty = QLabel("No evaluations recorded.")
            empty.setStyleSheet(
                f"font-family: {FONT_SANS}; font-size: 11px; color: {COLOR_MUTED}; border: none;"
            )
            fl.addWidget(empty)
        else:
            for rank_idx, (username, count) in enumerate(leaderboard):
                rank_str = _RANK_LABELS[rank_idx] if rank_idx < len(_RANK_LABELS) else f"#{rank_idx + 1}"

                row = QHBoxLayout()
                rank_lbl = QLabel(rank_str)
                rank_lbl.setStyleSheet(
                    f"font-family: {FONT_MONO}; font-weight: bold; font-size: 12px; "
                    f"color: {COLOR_MUTED}; border: none; min-width: 28px;"
                )

                name_lbl = QLabel(username)
                name_lbl.setStyleSheet(
                    f"font-family: {FONT_MONO}; font-size: 11px; color: {COLOR_TEXT}; border: none;"
                )

                count_lbl = QLabel(str(count))
                count_lbl.setStyleSheet(
                    f"font-family: {FONT_MONO}; font-weight: bold; font-size: 12px; "
                    f"color: {COLOR_SUCCESS}; border: none;"
                )
                count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

                row.addWidget(rank_lbl)
                row.addWidget(name_lbl, 1)
                row.addWidget(count_lbl)
                fl.addLayout(row)

        fl.addStretch()
        col.addWidget(frame, 1)
        return col

    # ---------------------------------------------------------------------- #
    def _make_csd_list_panel(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(_section_label("EVALUATED CSDs  (click to review)"))

        self._csd_list = QListWidget()
        self._csd_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {COLOR_PLOT_BG};
                color: {COLOR_TEXT};
                font-family: {FONT_MONO};
                font-size: 11px;
                border: 1px solid {COLOR_GRID};
            }}
            QListWidget::item {{
                padding: 5px 8px;
                border-bottom: 1px solid {COLOR_GRID};
            }}
            QListWidget::item:selected {{
                background-color: {COLOR_INFO};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {COLOR_GRID};
                color: {COLOR_TEXT};
            }}
            """
        )
        self._csd_list.setSelectionMode(QAbstractItemView.SingleSelection)

        summary = self._db.get_evaluations_summary() or []

        if not summary:
            item = QListWidgetItem("No CSDs evaluated yet.")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(QColor(COLOR_MUTED))
            self._csd_list.addItem(item)
        else:
            for entry in summary:
                ts    = entry.get("csd_timestamp", "UNKNOWN")
                count = entry.get("eval_count", 0)
                label = f"{ts}    [{count} evaluation(s)]"
                item  = QListWidgetItem(label)
                item.setData(Qt.UserRole, ts)
                self._csd_list.addItem(item)

        self._csd_list.itemDoubleClicked.connect(self._open_cross_eval)
        # Also respond to single-click with Enter / Return via activated
        self._csd_list.itemActivated.connect(self._open_cross_eval)

        col.addWidget(self._csd_list, 1)

        hint = QLabel("Double-click or press Enter to open a CSD's cross-evaluation view.")
        hint.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 10px; color: {COLOR_MUTED};")
        col.addWidget(hint)

        return col

    # ---------------------------------------------------------------------- #
    def _make_stats_panel(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(_section_label("QUICK STATS"))

        summary     = self._db.get_evaluations_summary() or []
        leaderboard = self._db.get_leaderboard() or []

        total_csds   = len(summary)
        total_ops    = len(leaderboard)
        total_evals  = sum(e.get("eval_count", 0) for e in summary)
        multi_eval   = sum(1 for e in summary if e.get("eval_count", 0) > 1)

        frame = _panel_frame()
        fl = QVBoxLayout(frame)
        fl.setSpacing(10)
        fl.setContentsMargins(12, 10, 12, 10)

        fl.addLayout(_stat_row("UNIQUE CSDs EVALUATED:", str(total_csds)))
        fl.addLayout(_stat_row("TOTAL EVALUATIONS:", str(total_evals)))
        fl.addLayout(_stat_row("CSDs WITH MULTIPLE EVALUATIONS:", str(multi_eval)))
        fl.addLayout(_stat_row("OPERATORS ON LEADERBOARD:", str(total_ops)))

        fl.addStretch()
        col.addWidget(frame, 1)
        return col

    # ---------------------------------------------------------------------- #
    def _open_cross_eval(self, item: QListWidgetItem):
        """Opens the CrossEvaluationDialog for the selected CSD."""
        ts = item.data(Qt.UserRole)
        if not ts:
            return

        evaluations = self._db.get_all_evaluations_for_csd(ts)

        dlg = CrossEvaluationDialog(ts, evaluations, parent=self)
        dlg.load_requested.connect(self._forward_load_request)
        dlg.exec()

    def _forward_load_request(self, csd_timestamp: str):
        """Relay the load request outward and close the dashboard."""
        self.load_csd_requested.emit(csd_timestamp)
        self.accept()

    # ---------------------------------------------------------------------- #
    def open_csd_directly(self, csd_timestamp: str):
        """
        Programmatic shortcut: open the cross-evaluation view for a specific
        CSD without requiring user interaction with the list.
        Called from the main window's 'Review Evaluations for this CSD' action.
        """
        evaluations = self._db.get_all_evaluations_for_csd(csd_timestamp)
        dlg = CrossEvaluationDialog(csd_timestamp, evaluations, parent=self.parent())
        dlg.load_requested.connect(self.load_csd_requested)
        dlg.exec()
