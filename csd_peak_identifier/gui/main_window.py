import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import find_peaks

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStatusBar, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt

from csd_peak_identifier.logic import ElementEvaluation, create_evaluation, lookup_isotopes
from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_PLOT_BG, COLOR_TARGET, ISOTOPE_DATA
)
from csd_peak_identifier.gui.canvas import MqPlotCanvas
from csd_peak_identifier.gui.dialogs import CandidateSelectionDialog

from ops.ecris.analysis.io.read_csd_file import read_csd_from_file_pair
from ops.ecris.analysis.model.element import Element
from ops.ecris.analysis.csd.polynomial_fit import polynomial_fit_mq

class CsdPeakIdentifierApp(QMainWindow):
    def __init__(self, csd_path):
        super().__init__()
        self.setWindowTitle("CSD Peak Identifier")
        self.resize(1200, 800)
        self.isotopes = pd.read_csv(
            ISOTOPE_DATA, delimiter="\\s+", names=["s", "z", "a", "m"]
        )
        self.csd = read_csd_from_file_pair(Path(csd_path))
        self.csd.m_over_q, _ = polynomial_fit_mq(
            self.csd, [Element("O", "Oxygen", 16, 8)], 4
        )
        self.peaks, _ = find_peaks(self.csd.beam_current, height=0.2, prominence=0.2)
        self.identified, self.maybe, self.targeted_mq = [], [], None

        self.setStyleSheet(f"background: {COLOR_BG};")
        main_layout = QHBoxLayout(QWidget(self))
        self.setCentralWidget(main_layout.parent())

        # UI Columns
        sidebar = QVBoxLayout()
        main_layout.addLayout(sidebar, 1)
        self.canvas = MqPlotCanvas(self)
        self.canvas.on_mq_clicked = self.handle_peak_click
        main_layout.addWidget(self.canvas, 4)
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 1)

        # Elements List
        self.eval_list = QListWidget()
        self.eval_list.setStyleSheet(f"background: {COLOR_PLOT_BG}")
        sidebar.addWidget(QLabel("Identified Elements"))
        sidebar.addWidget(self.eval_list)
        for txt, func, style in [
            (
                "Identify Peak (Enter)",
                self.start_identification,
                f"background: {COLOR_TARGET}; color: white; font-weight: bold;",
            ),
            ("Remove Selected", self.remove_selected, ""),
            ("Clear All", self.clear_all, ""),
        ]:
            btn = QPushButton(txt)
            btn.clicked.connect(func)
            btn.setStyleSheet(style)
            sidebar.addWidget(btn)

        # Peaks List
        self.peak_list = QListWidget()
        self.peak_list.setStyleSheet(f"background: {COLOR_PLOT_BG}")
        self.peak_list.itemClicked.connect(self.handle_peak_list_click)
        right_panel.addWidget(QLabel("Detected Peaks"))
        right_panel.addWidget(self.peak_list)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.setup_persistent()
        self.update_view()

    def setup_persistent(self):
        for s in ["O", "N", "C"]:
            matches = lookup_isotopes(s, self.isotopes)
            if not matches.empty:
                ev = create_evaluation(
                    matches.iloc[matches["a"].argmax()], self.csd, self.peaks
                )
                if len(ev.peak_indices) > 0:
                    self.identified.append(ev)

    def update_view(self, candidate=None, rebuild=False):
        target_ev = None
        if self.targeted_mq:
            idx = np.argmin(np.abs(self.csd.m_over_q - self.targeted_mq))
            target_ev = ElementEvaluation(
                "TARGET",
                0,
                0,
                0.0,
                np.array([float(self.csd.m_over_q[idx])]),
                np.array([float(self.csd.beam_current[idx])]),
                np.array([idx]),
            )

        self.canvas.redraw(self.csd, self.identified, candidate, target_ev)
        if rebuild or self.eval_list.count() != len(self.identified):
            self.eval_list.blockSignals(True)
            self.eval_list.clear()
            for ev in self.identified:
                self.eval_list.addItem(
                    f"{ev.symbol()} ({ev.score(self.csd.m_over_q.max()):.2f})"
                )
            self.eval_list.blockSignals(False)
        self.update_peak_list()

    def update_peak_list(self):
        self.peak_list.blockSignals(True)
        self.peak_list.clear()
        pk_map = {
            p: [ev.symbol() for ev in self.identified if p in ev.peak_indices]
            for p in self.peaks
        }
        target_item = None
        for p_idx in self.peaks:
            mq, cur, elems = (
                float(self.csd.m_over_q[p_idx]),
                float(self.csd.beam_current[p_idx]),
                pk_map[p_idx],
            )
            txt = f"{'✓' if elems else '●'} m/q: {mq:5.2f} | {cur:6.2f} uA {'[' + ','.join(elems) + ']' if elems else ''}"
            item = QListWidgetItem(txt)
            item.setData(Qt.UserRole, mq)
            if elems:
                item.setForeground(Qt.gray)
            self.peak_list.addItem(item)
            if self.targeted_mq and abs(mq - self.targeted_mq) < 0.001:
                target_item = item
        if target_item:
            self.peak_list.setCurrentItem(target_item)
            self.peak_list.scrollToItem(target_item)
        self.peak_list.blockSignals(False)

    def handle_peak_click(self, x, y):
        self.targeted_mq = float(
            self.csd.m_over_q[
                self.peaks[np.argmin(np.abs(self.csd.m_over_q[self.peaks] - x))]
            ]
        )
        self.update_view()

    def handle_peak_list_click(self, item):
        self.targeted_mq = item.data(Qt.UserRole)
        self.update_view()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.start_identification()
        elif event.key() in (Qt.Key_Left, Qt.Key_Right):
            mqs = sorted([float(self.csd.m_over_q[p]) for p in self.peaks])
            idx = (
                np.argmin(np.abs(np.array(mqs) - self.targeted_mq))
                if self.targeted_mq
                else 0
            )
            self.targeted_mq = mqs[
                (idx + (1 if event.key() == Qt.Key_Right else -1)) % len(mqs)
            ]
            self.update_view()

    def start_identification(self):
        if not self.targeted_mq:
            return
        mq, p_mqs = self.targeted_mq, self.csd.m_over_q[self.peaks]
        p_idx = self.peaks[np.argmin(np.abs(p_mqs - mq))]
        candidates = []
        for q in range(1, 31):
            matches = self.isotopes[
                (self.isotopes["m"] > mq * q - 0.5)
                & (self.isotopes["m"] < mq * q + 0.5)
            ]
            for _, iso in matches.iterrows():
                if q > int(iso["z"]):
                    continue
                ev = create_evaluation(iso, self.csd, self.peaks)
                if p_idx in ev.peak_indices and not any(
                    c.symbol() == ev.symbol() for c in candidates
                ):
                    candidates.append(ev)
        if not candidates:
            self.status_bar.showMessage(f"No isotopic matches for m/q {mq:.2f}", 3000)
            return
        candidates.sort(
            key=lambda c: (c.score(self.csd.m_over_q.max()), c.a), reverse=True
        )
        dialog = CandidateSelectionDialog(candidates, mq, self)
        dialog.table.itemSelectionChanged.connect(
            lambda: self.update_view(dialog.get_selected())
        )
        if dialog.exec():
            if dialog.action == "accept" and dialog.selected not in self.identified:
                self.identified.append(dialog.selected)
            elif dialog.action == "maybe":
                self.maybe.append(dialog.selected)
        self.update_view()

    def clear_all(self):
        self.identified, self.maybe = [], []
        self.update_view()

    def remove_selected(self):
        row = self.eval_list.currentRow()
        if 0 <= row < len(self.identified):
            del self.identified[row]
            self.update_view()
