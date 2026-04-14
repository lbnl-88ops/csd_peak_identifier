import sys
import numpy as np
import pandas as pd
from pathlib import Path
from collections import deque
from itertools import product
from typing import List, Dict, Optional, Any
from scipy.signal import find_peaks

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStatusBar,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Slot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

from logic import ElementEvaluation, create_evaluation, lookup_isotopes
from ops.ecris.analysis.io.read_csd_file import read_csd_from_file_pair
from ops.ecris.analysis.model.element import Element
from ops.ecris.analysis.csd.polynomial_fit import polynomial_fit_mq

# --- CONSTANTS ---
CURRENT_DIR = Path(__file__).parent
DATA_PATH = CURRENT_DIR.parent / "data"
ISOTOPE_DATA = DATA_PATH / "IsotopeData.txt"
DEFAULT_CSD = DATA_PATH / "csds" / "csd_1762894074"

# Colorblind-friendly Professional palette (Okabe-Ito)
COLOR_BG = "#f4f1ea"
COLOR_PLOT_BG = "#ffffff"
COLOR_GRID = "#d1d1d1"
COLOR_TARGET = "#d55e00"  # Vermilion (High contrast for colorblindness)
COLOR_CANDIDATE = "#0072b2"  # Dark Blue
COLOR_IDENTIFIED_OUTLINE = "#2f3640"
MARKERS = ["v", "^", "p", "d", "*", "D"]
SHADES = ["white", "gray", "white"]


# Verified colorblind-safe palette
# SHADES = [
#     "#e69f00",  # Orange
#     "#56b4e9",  # Sky Blue
#     "#009e73",  # Bluish Green
#     "#f0e442",  # Yellow
#     "#cc79a7",  # Reddish Purple
#     "#000000",  # Black (for high contrast)
# ]
#
#
class MqPlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(9, 6), facecolor=COLOR_BG)
        self.axes = fig.add_subplot(111, facecolor=COLOR_PLOT_BG)
        self.axes.set_xlabel("m/q")
        self.axes.set_ylabel(r"Beam Current ($\mu$A)")
        self.axes.xaxis.set_major_locator(MultipleLocator(1.0))
        # self.axes.spines["top"].set_visible(False)
        # self.axes.spines["right"].set_visible(False)
        super().__init__(fig)
        self.setParent(parent)
        self.on_mq_clicked = None
        self.mpl_connect("button_press_event", self._on_click)

    def _on_click(self, event):
        if event.inaxes == self.axes and event.button == 1 and self.on_mq_clicked:
            self.on_mq_clicked(event.xdata, event.ydata)

    def redraw(self, csd, identified, candidate=None, target=None):
        self.axes.clear()
        self.axes.set_xlabel("m/q")
        self.axes.set_ylabel(r"Beam Current ($\mu$A)")
        self.axes.xaxis.set_major_locator(MultipleLocator(1.0))
        # self.axes.spines["top"].set_visible(False)
        # self.axes.spines["right"].set_visible(False)
        self.axes.spines["top"].set_linewidth(0.1)
        self.axes.spines["right"].set_linewidth(0.1)

        if csd.m_over_q is not None:
            self.axes.plot(
                csd.m_over_q,
                csd.beam_current,
                ":",
                color="black",
                alpha=0.4,
                label="CSD",
            )

        y_min, y_max = self.axes.get_ylim()
        y_range = max(y_max - y_min, 0.1)

        if candidate or target:
            self.axes.set_ylim(y_min, y_max + 0.15 * y_range)
            y_max_extended = self.axes.get_ylim()[1]
        else:
            y_max_extended = y_max

        if target and not candidate:
            self.axes.plot(
                target.m_over_q,
                target.current + 0.05 * y_range,
                "v",
                color=COLOR_TARGET,
                markersize=12,
                label="TARGET",
            )
            self.axes.axvline(
                target.m_over_q[0], color=COLOR_TARGET, ls="-", alpha=0.3, lw=1.5
            )

        if candidate:
            self.axes.plot(
                candidate.m_over_q,
                candidate.current + 0.05 * y_range,
                "v",
                color=COLOR_CANDIDATE,
                markersize=10,
                label=f"CAND: {candidate.symbol()}",
            )
            for q in range(1, candidate.z + 1):
                mq_exp = candidate.m / q
                if self.axes.get_xlim()[0] <= mq_exp <= self.axes.get_xlim()[1]:
                    self.axes.axvline(
                        mq_exp, ls="--", color=COLOR_CANDIDATE, alpha=0.4, lw=1
                    )
                    self.axes.text(
                        mq_exp,
                        y_max + 0.05 * y_range,
                        str(q),
                        color=COLOR_CANDIDATE,
                        ha="center",
                        fontsize=9,
                        fontweight="bold",
                    )
            if len(candidate.missing_m_over_q) > 0:
                self.axes.plot(
                    candidate.missing_m_over_q,
                    candidate.missing_current,
                    "o",
                    mfc="none",
                    mec=COLOR_CANDIDATE,
                    alpha=0.6,
                )

        peak_counts, style_cycle = (
            {},
            deque([(m, s) for s, m in product(SHADES, MARKERS)]),
        )
        for ev in identified:
            m, c = style_cycle[0]
            cur_off = [
                cur + peak_counts.setdefault(round(mq, 2), 0) * 0.02 * y_range
                for mq, cur in zip(ev.m_over_q, ev.current)
            ]
            for mq in ev.m_over_q:
                peak_counts[round(mq, 2)] += 1
            self.axes.plot(
                ev.m_over_q,
                cur_off,
                m,
                mfc=c,
                mec=COLOR_IDENTIFIED_OUTLINE,
                label=ev.symbol(),
            )
            if candidate and len(ev.missing_m_over_q) > 0:
                self.axes.plot(
                    ev.missing_m_over_q,
                    ev.missing_current,
                    "o",
                    mfc="none",
                    mec=c,
                    alpha=0.4,
                )
            style_cycle.rotate(-1)

        self.axes.legend(loc="upper right", fontsize="small")
        self.axes.grid(color=COLOR_GRID, ls="--", alpha=0.5)
        self.draw()


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


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = CsdPeakIdentifierApp(DEFAULT_CSD)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
