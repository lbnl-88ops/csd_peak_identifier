from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton
)
from csd_peak_identifier.gui.constants import COLOR_IDENTIFIED_OUTLINE

class CandidateSelectionDialog(QDialog):
    def __init__(self, candidates, target_mq, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Candidates for {target_mq:.2f}")
        self.setMinimumSize(500, 300)
        self.candidates, self.selected, self.action = candidates, None, None
        layout = QVBoxLayout(self)
        self.table = QTableWidget(len(candidates), 4)
        self.table.setHorizontalHeaderLabels(["Symbol", "Score", "Abundance", "Z"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        for i, c in enumerate(candidates):
            for j, val in enumerate(
                [c.symbol(), f"{c.score(target_mq * 2):.2f}", f"{c.a:.1f}", str(c.z)]
            ):
                self.table.setItem(i, j, QTableWidgetItem(val))
        layout.addWidget(self.table)
        if candidates:
            self.table.selectRow(0)
        btns = QHBoxLayout()
        for txt, act, style in [
            (
                "Accept",
                "accept",
                f"background: {COLOR_IDENTIFIED_OUTLINE}; color: white; font-weight: bold;",
            ),
            ("Maybe", "maybe", "background: #adb5bd;"),
            ("Reject", "reject", "background: #dee2e6;"),
        ]:
            b = QPushButton(txt)
            b.setStyleSheet(style)
            b.clicked.connect(lambda _, a=act: self._finish(a))
            btns.addWidget(b)
        layout.addLayout(btns)

    def get_selected(self):
        row = self.table.currentRow()
        return self.candidates[row] if row >= 0 else None

    def _finish(self, action):
        self.action = action
        if action != "reject":
            self.selected = self.get_selected()
        if self.selected or action == "reject":
            self.accept() if action != "reject" else self.reject()
