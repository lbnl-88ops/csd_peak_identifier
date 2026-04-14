import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import find_peaks

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStatusBar, QListWidget, QListWidgetItem, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from csd_peak_identifier.logic import ElementEvaluation, create_evaluation, lookup_isotopes
from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_PLOT_BG, COLOR_TARGET, ISOTOPE_DATA
)
from csd_peak_identifier.gui.canvas import MqPlotCanvas

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
        self.identified, self.targeted_mq = [], None
        self.maybe = []
        self.rejected_symbols = set()
        self.candidates = []

        self.setStyleSheet(f"background: {COLOR_BG};")
        main_layout = QHBoxLayout(QWidget(self))
        self.setCentralWidget(main_layout.parent())

        # UI Columns
        sidebar = QVBoxLayout()
        main_layout.addLayout(sidebar, 1)

        center_layout = QVBoxLayout()
        self.canvas = MqPlotCanvas(self)
        self.canvas.on_mq_clicked = self.handle_peak_click
        center_layout.addWidget(self.canvas, 1)

        self.info_label = QLabel("Select a candidate to see details")
        self.info_label.setStyleSheet(
            f"padding: 2px; font-size: 13px;"
        )
        self.info_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.info_label, 0)
        main_layout.addLayout(center_layout, 4)

        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 1)

        # Elements List
        self.eval_list = QListWidget()
        self.eval_list.setStyleSheet(f"background: {COLOR_PLOT_BG}")
        sidebar.addWidget(QLabel("Identified Elements"))
        sidebar.addWidget(self.eval_list, 1)

        # Candidate List
        self.candidate_list = QListWidget()
        self.candidate_list.setStyleSheet(f"background: {COLOR_PLOT_BG}")
        self.candidate_list.itemSelectionChanged.connect(self.handle_candidate_selection)
        sidebar.addWidget(QLabel("Candidate Elements"))
        sidebar.addWidget(self.candidate_list, 2)

        # Button Stack
        self.button_stack = QStackedWidget()
        sidebar.addWidget(self.button_stack)

        # Main Buttons Panel
        self.main_btn_panel = QWidget()
        main_btn_layout = QVBoxLayout(self.main_btn_panel)
        main_btn_layout.setContentsMargins(0, 0, 0, 0)
        main_btn_layout.setSpacing(0)
        main_btn_layout.addStretch()
        self.button_stack.addWidget(self.main_btn_panel)

        for txt, func, style in [
            (
                "Search Candidates (Enter)",
                self.start_identification,
                f"background: {COLOR_TARGET}; color: white; font-weight: bold;",
            ),
            ("Remove Identified", self.remove_selected, ""),
            ("Clear All", self.clear_all, ""),
        ]:
            btn = QPushButton(txt)
            btn.clicked.connect(func)
            btn.setStyleSheet(style)
            main_btn_layout.addWidget(btn)

        # ID Buttons Panel
        self.id_btn_panel = QWidget()
        id_btn_layout = QVBoxLayout(self.id_btn_panel)
        id_btn_layout.setContentsMargins(0, 0, 0, 0)
        id_btn_layout.setSpacing(0)
        id_btn_layout.addStretch()
        self.button_stack.addWidget(self.id_btn_panel)

        for txt, func, style in [
            ("Accept Candidate", self.accept_candidate, "font-weight: bold;"),
            ("Mark as Maybe", self.mark_as_maybe, ""),
            ("Reject Candidate", self.reject_candidate, ""),
            ("Exit Peak ID", self.exit_identification, ""),
        ]:
            btn = QPushButton(txt)
            btn.clicked.connect(func)
            btn.setStyleSheet(style)
            id_btn_layout.addWidget(btn)

        self.button_stack.setCurrentIndex(0)

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

        if candidate is None:
            row = self.candidate_list.currentRow()
            if 0 <= row < len(self.candidates):
                candidate = self.candidates[row]

        if candidate:
            score = candidate.score(self.csd.m_over_q.max())
            self.info_label.setText(
                f"<b>Candidate:</b> {candidate.symbol()} | "
                f"<b>Mass:</b> {candidate.m} | "
                f"<b>Z:</b> {candidate.z} | "
                f"<b>Abundance:</b> {candidate.a:.2f}% | "
                f"<b>Score:</b> {score*100:.1f}% (Found vs Expected)"
            )
        else:
            self.info_label.setText("Select a candidate to see details")

        self.canvas.redraw(self.csd, self.identified + self.maybe, candidate, target_ev)
        if rebuild or self.eval_list.count() != (len(self.identified) + len(self.maybe)):
            self.eval_list.blockSignals(True)
            self.eval_list.clear()
            for ev in self.identified:
                self.eval_list.addItem(
                    f"{ev.symbol()} ({ev.score(self.csd.m_over_q.max()):.2f})"
                )
            for ev in self.maybe:
                item = QListWidgetItem(
                    f"{ev.symbol()} (maybe) ({ev.score(self.csd.m_over_q.max()):.2f})"
                )
                item.setForeground(Qt.darkBlue)
                self.eval_list.addItem(item)
            self.eval_list.blockSignals(False)
        self.update_peak_list()

    def update_peak_list(self):
        self.peak_list.blockSignals(True)
        self.peak_list.clear()
        combined_identified = self.identified + self.maybe
        pk_map = {
            p: [ev.symbol() for ev in combined_identified if p in ev.peak_indices]
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

    def handle_candidate_selection(self):
        self.update_view()

    def update_candidate_list(self):
        self.candidate_list.blockSignals(True)
        self.candidate_list.clear()
        for c in self.candidates:
            item = QListWidgetItem(
                f"{c.symbol()} (S: {c.score(self.targeted_mq * 2):.2f}, A: {c.a:.1f})"
            )
            if c.symbol() in self.rejected_symbols:
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(Qt.gray)
            self.candidate_list.addItem(item)
        if self.candidates:
            self.candidate_list.setCurrentRow(0)
        self.candidate_list.blockSignals(False)

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
        self.candidates = []
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
                    c.symbol() == ev.symbol() for c in self.candidates
                ):
                    self.candidates.append(ev)
        
        if not self.candidates:
            self.status_bar.showMessage(f"No isotopic matches for m/q {mq:.2f}", 3000)
            self.update_candidate_list()
            return
            
        self.candidates.sort(
            key=lambda c: (c.score(self.csd.m_over_q.max()), c.a), reverse=True
        )
        self.button_stack.setCurrentIndex(1) # ID Mode
        self.update_candidate_list()
        self.update_view()

    def accept_candidate(self):
        row = self.candidate_list.currentRow()
        if 0 <= row < len(self.candidates):
            selected = self.candidates[row]
            # remove from maybe if it was there
            self.maybe = [m for m in self.maybe if m.symbol() != selected.symbol()]
            if not any(i.symbol() == selected.symbol() for i in self.identified):
                self.identified.append(selected)
            self.exit_identification()

    def mark_as_maybe(self):
        row = self.candidate_list.currentRow()
        if 0 <= row < len(self.candidates):
            selected = self.candidates[row]
            if not any(m.symbol() == selected.symbol() for m in self.maybe) and \
               not any(i.symbol() == selected.symbol() for i in self.identified):
                self.maybe.append(selected)
                self.update_view(rebuild=True)

    def reject_candidate(self):
        row = self.candidate_list.currentRow()
        if 0 <= row < len(self.candidates):
            selected = self.candidates[row]
            self.rejected_symbols.add(selected.symbol())
            # also remove from maybe/identified if it was there
            self.identified = [i for i in self.identified if i.symbol() != selected.symbol()]
            self.maybe = [m for m in self.maybe if m.symbol() != selected.symbol()]
            self.update_candidate_list()
            self.update_view(rebuild=True)

    def exit_identification(self):
        self.candidates = []
        self.button_stack.setCurrentIndex(0) # Main Mode
        self.update_candidate_list()
        self.update_view()

    def clear_all(self):
        self.identified, self.maybe, self.candidates = [], [], []
        self.rejected_symbols = set()
        self.candidate_list.clear()
        self.update_view()

    def remove_selected(self):
        row = self.eval_list.currentRow()
        if 0 <= row < (len(self.identified) + len(self.maybe)):
            if row < len(self.identified):
                del self.identified[row]
            else:
                del self.maybe[row - len(self.identified)]
            self.update_view()
