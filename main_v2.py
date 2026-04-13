import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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
    QFrame,
)
from PySide6.QtCore import Qt, Slot, Signal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

# Import our refined logic
from logic import (
    ElementEvaluation,
    find_element_peaks,
    create_evaluation,
    lookup_isotopes,
)

# Mocking the package for data loading
from ops.ecris.analysis.io.read_csd_file import read_csd_from_file_pair
from ops.ecris.analysis.model.element import Element
from ops.ecris.analysis.csd.polynomial_fit import polynomial_fit_mq


class MqPlotCanvas(FigureCanvas):
    """An advanced Matplotlib canvas with ECRIS CSD flourishes."""

    def __init__(self, parent=None, width=9, height=6, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.set_xlabel("m/q")
        self.axes.set_ylabel(r"Beam Current ($\mu$A)")

        # Grid lines at whole m/q values
        self.axes.xaxis.set_major_locator(MultipleLocator(1.0))
        # self.axes.grid(True, which="both", linestyle="--", alpha=0.5)
        self.axes.grid()

        # Style for modern aesthetic
        fig.patch.set_facecolor("#f8f9fa")
        self.axes.set_facecolor("white")
        self.axes.spines["top"].set_visible(False)
        self.axes.spines["right"].set_visible(False)

        super().__init__(fig)
        self.setParent(parent)

        self.on_mq_clicked = None
        self.mpl_connect("button_press_event", self._on_click)

    def _on_click(self, event):
        if event.inaxes != self.axes or event.button != 1:
            return
        if self.on_mq_clicked:
            self.on_mq_clicked(event.xdata, event.ydata)

    def redraw_spectrum(self, csd, identified_evals, candidate_eval=None, target_eval=None):
        """Perform all the advanced plotting flourishes from the TUI ritual."""
        self.axes.clear()

        # 1. Base Spectrum
        if csd.m_over_q is not None and csd.beam_current is not None:
            self.axes.plot(
                csd.m_over_q,
                csd.beam_current,
                ":",
                color="black",
                alpha=0.6,
                label="Measured CSD",
            )

        # Set limits to ensure y_range is meaningful
        y_min, y_max = self.axes.get_ylim()
        y_range = y_max - y_min if y_max > y_min else 1.0

        # 2. Target Peak Highlight (The Magenta 'v')
        if target_eval and not candidate_eval:
            color = "black"  # Magenta
            offset = 0.05 * y_range
            self.axes.plot(
                target_eval.m_over_q,
                target_eval.current + offset,
                "v",
                markersize=12,
                label="TARGET PEAK",
                color=color,
                markeredgecolor="k",
            )
            self.axes.axvline(target_eval.m_over_q[0], ls="-", color=color, alpha=0.3)

        # 3. Candidate Investigation Overlay (The "v" markers and charge lines)
        if candidate_eval:
            color = "#17a2b8"  # Cyan-ish
            offset = 0.03 * y_range

            # Marker for identified peaks of candidate
            (line,) = self.axes.plot(
                candidate_eval.m_over_q,
                candidate_eval.current + offset,
                "v",
                markersize=10,
                label=f"CANDIDATE: {candidate_eval.symbol()}",
                color=color,
            )

            # Vertical dashed lines and q labels for ALL charge states
            for q in range(1, candidate_eval.z + 1):
                mq_expected = candidate_eval.m / q
                mq_min, mq_max = self.axes.get_xlim()
                if mq_min < mq_expected < mq_max:
                    self.axes.axvline(mq_expected, ls="--", color=color, alpha=0.4)
                    self.axes.text(
                        mq_expected,
                        y_max + 0.01 * y_range,
                        f"{q}",
                        color=color,
                        ha="center",
                        va="bottom",
                        fontsize=9,
                        fontweight="bold",
                    )

            # Missing peaks markers
            if len(candidate_eval.missing_m_over_q) > 0:
                self.axes.plot(
                    candidate_eval.missing_m_over_q,
                    candidate_eval.missing_current,
                    "o",
                    fillstyle="none",
                    color=color,
                    markersize=10,
                    alpha=0.8,
                )

        # 3. Identified Elements (The marker/color scheme from peak assessment)
        peak_counts: Dict[float, int] = {}
        # Scheme: ["v", "^", "p", "d", "*", "D"] with ["w", "gray", "k"]
        MARKERS = ["v", "^", "p", "d", "*", "D"]
        COLORS = ["w", "gray", "k"]
        MARKER_STYLE = deque(product(MARKERS, COLORS))

        for ev in identified_evals:
            marker, color = MARKER_STYLE[0]
            currents_with_offset = []
            for mq, cur in zip(ev.m_over_q, ev.current):
                mq_key = round(float(mq), 2)
                count = peak_counts.get(mq_key, 0)
                currents_with_offset.append(cur + count * 0.02 * y_range)
                peak_counts[mq_key] = count + 1

            self.axes.plot(
                ev.m_over_q,
                currents_with_offset,
                marker,
                markerfacecolor=color,
                markeredgecolor="k",
                label=ev.symbol(),
                markersize=8,
                markeredgewidth=1,
            )

            # Missing peaks for identified elements (only show during candidate comparison)
            if candidate_eval and len(ev.missing_m_over_q) > 0:
                self.axes.plot(
                    ev.missing_m_over_q,
                    ev.missing_current,
                    "o",
                    fillstyle="none",
                    color=color,
                    markeredgecolor="k",
                    markersize=8,
                    alpha=0.5,
                )

            MARKER_STYLE.rotate(-1)

        self.axes.set_xlabel("m/q")
        self.axes.set_ylabel(r"Current ($\mu$A)")
        self.axes.legend(loc="upper right", frameon=True, fontsize="small")
        self.axes.grid(alpha=0.5, ls="--")
        self.draw()


class CandidateSelectionDialog(QDialog):
    """A dialog to review and select isotopic candidates for a peak."""

    def __init__(self, candidates, target_mq, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Candidates for m/q {target_mq:.3f}")
        self.setMinimumSize(600, 400)
        self.candidates = candidates
        self.selected_candidate = None
        self.action = None  # "accept", "maybe", "reject"

        layout = QVBoxLayout(self)

        self.table = QTableWidget(len(candidates), 4)
        self.table.setHorizontalHeaderLabels(["Symbol", "Score", "Abundance (%)", "Z (Max Q)"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, cand in enumerate(candidates):
            self.table.setItem(i, 0, QTableWidgetItem(cand.symbol()))
            self.table.setItem(i, 1, QTableWidgetItem(f"{cand.score(target_mq * 2):.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{cand.a:.1f}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(cand.z)))

        layout.addWidget(self.table)

        # Action Buttons
        btn_layout = QHBoxLayout()
        accept_btn = QPushButton("Accept (y)")
        accept_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        accept_btn.clicked.connect(self._accept)

        maybe_btn = QPushButton("Maybe (m)")
        maybe_btn.setStyleSheet("background-color: #ffc107; font-weight: bold;")
        maybe_btn.clicked.connect(self._maybe)

        reject_btn = QPushButton("Reject (n)")
        reject_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        reject_btn.clicked.connect(self._reject)

        btn_layout.addWidget(accept_btn)
        btn_layout.addWidget(maybe_btn)
        btn_layout.addWidget(reject_btn)
        layout.addLayout(btn_layout)

    def _get_selection(self):
        row = self.table.currentRow()
        if row >= 0:
            return self.candidates[row]
        return None

    def _accept(self):
        self.selected_candidate = self._get_selection()
        if self.selected_candidate:
            self.action = "accept"
            self.accept()

    def _maybe(self):
        self.selected_candidate = self._get_selection()
        if self.selected_candidate:
            self.action = "maybe"
            self.accept()

    def _reject(self):
        self.action = "reject"
        self.reject()


class CsdPeakIdentifierApp(QMainWindow):
    """The grand vessel for ECRIS CSD peak identification."""

    def __init__(self, csd_path):
        super().__init__()
        self.setWindowTitle("ECRIS CSD Peak Identifier")
        self.resize(1200, 800)

        # 1. Load Data
        self.isotopes = pd.read_csv(
            "/home/rehak/repos/ops/ecris.analysis/data/IsotopeData.txt",
            delimiter="\\s+",
            names=["s", "z", "a", "m"],
        )
        self.csd = read_csd_from_file_pair(Path(csd_path))

        # Initial fit for m/q estimation
        self.csd.m_over_q, _ = polynomial_fit_mq(
            self.csd, [Element("O", "Oxygen", 16, 8)], polynomial_order=4
        )

        # Detect all peaks using our refined parameters
        self.peaks, _ = find_peaks(self.csd.beam_current, height=0.2, prominence=0.2)

        self.identified_evals: List[ElementEvaluation] = []
        self.maybe_evals: List[ElementEvaluation] = []
        self.targeted_mq: Optional[float] = None

        # 2. UI Setup

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar
        sidebar = QVBoxLayout()
        main_layout.addLayout(sidebar, 1)

        info_box = QGroupBox("Instructions")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("1. Click on a peak in the plot."))
        info_layout.addWidget(QLabel("2. Review isotopic candidates."))
        info_layout.addWidget(QLabel("3. Accept to identify."))
        info_box.setLayout(info_layout)
        sidebar.addWidget(info_box)

        eval_box = QGroupBox("Identified Elements")
        eval_layout = QVBoxLayout()
        self.eval_list = QListWidget()
        eval_layout.addWidget(self.eval_list)
        eval_box.setLayout(eval_layout)
        sidebar.addWidget(eval_box)

        # Selection Buttons
        self.identify_btn = QPushButton("Identify Peak")
        self.identify_btn.setStyleSheet(
            "background-color: #17a2b8; color: white; font-weight: bold; font-size: 14px;"
        )
        self.identify_btn.clicked.connect(self.start_identification)
        sidebar.addWidget(self.identify_btn)

        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_element)
        sidebar.addWidget(self.remove_btn)

        # Buttons
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_identifications)
        sidebar.addWidget(self.clear_btn)

        # Plot Area
        self.canvas = MqPlotCanvas(self)
        self.canvas.on_mq_clicked = self.handle_peak_click
        main_layout.addWidget(self.canvas, 4)

        # Right Panel: Peak List
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 1)

        peak_box = QGroupBox("Detected Peaks")
        peak_layout = QVBoxLayout()
        self.peak_list = QListWidget()
        self.peak_list.itemClicked.connect(self.handle_peak_list_click)
        peak_layout.addWidget(self.peak_list)
        peak_box.setLayout(peak_layout)
        right_panel.addWidget(peak_box)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 3. Initial Setup: Persistent Elements
        self.setup_persistent_elements()

        # Initial draw
        self.update_view()

    def setup_persistent_elements(self, default_symbols=["O", "N", "C"]):
        """Automatically identify the most abundant isotopes of O, N, and C."""
        for item in default_symbols:
            matches = lookup_isotopes(item, self.isotopes)
            if matches.empty:
                continue

            # Find most abundant isotope
            most_abundant = matches.iloc[matches["a"].to_numpy().argmax()]
            ev = create_evaluation(most_abundant, self.csd, self.peaks)
            if len(ev.peak_indices) > 0:
                self.identified_evals.append(ev)

    def update_view(self, candidate=None, rebuild_evals=False):
        # Create a dummy evaluation for the target highlight if one exists
        target_eval = None
        if self.targeted_mq is not None:
            idx = np.argmin(np.abs(self.csd.m_over_q - self.targeted_mq))
            target_eval = ElementEvaluation(
                "TARGET",
                0,
                0,
                0.0,
                np.array([float(self.csd.m_over_q[idx])]),
                np.array([float(self.csd.beam_current[idx])]),
                np.array([idx]),
            )

        self.canvas.redraw_spectrum(self.csd, self.identified_evals, candidate, target_eval)

        if rebuild_evals or self.eval_list.count() != len(self.identified_evals):
            self.eval_list.blockSignals(True)
            self.eval_list.clear()
            for ev in self.identified_evals:
                self.eval_list.addItem(
                    f"{ev.symbol()} (Score: {ev.score(self.csd.m_over_q.max()):.2f})"
                )
            self.eval_list.blockSignals(False)

        self.update_peak_list()

    def update_peak_list(self):
        """Update the peak list on the right, prioritizing unidentified peaks."""
        self.peak_list.blockSignals(True)  # Prevent feedback loops
        self.peak_list.clear()

        # Map peak indices to identified elements
        peak_to_elements = {p: [] for p in self.peaks}
        for ev in self.identified_evals:
            for p_idx in ev.peak_indices:
                if p_idx in peak_to_elements:
                    peak_to_elements[p_idx].append(ev.symbol())

        unidentified = []
        identified = []

        for p_idx in self.peaks:
            mq = float(self.csd.m_over_q[p_idx])
            cur = float(self.csd.beam_current[p_idx])
            elems = peak_to_elements[p_idx]

            if elems:
                item_text = f"✓ m/q: {mq:5.2f} | {cur:6.2f} uA [{', '.join(elems)}]"
                identified.append((p_idx, mq, item_text))
            else:
                item_text = f"● m/q: {mq:5.2f} | {cur:6.2f} uA"
                unidentified.append((p_idx, mq, item_text))

        # Add items and track the one to select
        target_item = None

        for p_idx, mq, text in unidentified:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, mq)
            self.peak_list.addItem(item)
            if self.targeted_mq is not None and abs(mq - self.targeted_mq) < 0.001:
                target_item = item

        for p_idx, mq, text in identified:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, mq)
            item.setForeground(Qt.gray)
            self.peak_list.addItem(item)
            if self.targeted_mq is not None and abs(mq - self.targeted_mq) < 0.001:
                target_item = item

        if target_item:
            self.peak_list.setCurrentItem(target_item)
            self.peak_list.scrollToItem(target_item)

        self.peak_list.blockSignals(False)

    def handle_peak_list_click(self, item):
        """When a peak is clicked in the list, target it on the plot."""
        self.targeted_mq = item.data(Qt.UserRole)
        self.update_view()

    def handle_peak_click(self, x, y):
        """Target nearest peak and select it in the list."""
        peak_mqs = self.csd.m_over_q[self.peaks]
        nearest_peak_idx = self.peaks[np.argmin(np.abs(peak_mqs - x))]
        peak_mq = float(self.csd.m_over_q[nearest_peak_idx])

        self.targeted_mq = peak_mq

        # Select in list
        for i in range(self.peak_list.count()):
            item = self.peak_list.item(i)
            if abs(item.data(Qt.UserRole) - peak_mq) < 0.01:
                self.peak_list.setCurrentItem(item)
                self.peak_list.scrollToItem(item)
                break

        self.status_bar.showMessage(f"Targeted peak at m/q = {peak_mq:.3f}")
        self.update_view()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for fast operation."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.start_identification()
        elif event.key() == Qt.Key_Left:
            self._move_target(-1)
        elif event.key() == Qt.Key_Right:
            self._move_target(1)
        else:
            super().keyPressEvent(event)

    def _move_target(self, direction):
        """Cycle through peaks by m/q value using arrow keys."""
        if len(self.peaks) == 0:
            return

        # Get sorted list of peak m/q values
        peak_mqs = sorted([float(self.csd.m_over_q[p]) for p in self.peaks])

        if self.targeted_mq is None:
            new_mq = peak_mqs[0] if direction > 0 else peak_mqs[-1]
        else:
            # Find current index in sorted list
            idx = np.argmin(np.abs(np.array(peak_mqs) - self.targeted_mq))
            new_idx = (idx + direction) % len(peak_mqs)
            new_mq = peak_mqs[new_idx]

        self.targeted_mq = new_mq
        self.status_bar.showMessage(f"Targeted peak at m/q = {new_mq:.3f}")
        self.update_view()

    def start_identification(self):
        """Open candidates dialog for the currently targeted peak."""
        if self.targeted_mq is None:
            self.status_bar.showMessage("Select a peak first!", 3000)
            return

        peak_mq = self.targeted_mq
        peak_mqs = self.csd.m_over_q[self.peaks]
        nearest_peak_idx = self.peaks[np.argmin(np.abs(peak_mqs - peak_mq))]

        # Find Candidates logic from original script
        candidates = []
        for charge in range(1, 31):
            target_mass = peak_mq * charge
            matches = self.isotopes[
                (self.isotopes["m"] > target_mass - 0.5) & (self.isotopes["m"] < target_mass + 0.5)
            ]
            for _, isotope in matches.iterrows():
                if charge > int(isotope["z"]):
                    continue
                ev = create_evaluation(isotope, self.csd, self.peaks)
                if nearest_peak_idx in ev.peak_indices:
                    if not any(c.symbol() == ev.symbol() for c in candidates):
                        candidates.append(ev)

        if not candidates:
            self.status_bar.showMessage(f"No candidates found for m/q {peak_mq:.3f}", 5000)
            return

        # Sort by score and abundance
        max_mq = self.csd.m_over_q.max()
        candidates.sort(key=lambda c: (c.score(max_mq), c.a), reverse=True)

        # Show Candidate Dialog
        dialog = CandidateSelectionDialog(candidates, peak_mq, self)

        # Connect table selection change to plot preview
        dialog.table.itemSelectionChanged.connect(
            lambda: self.update_view(dialog._get_selection())
        )

        if dialog.exec():
            if dialog.action == "accept":
                if dialog.selected_candidate not in self.identified_evals:
                    self.identified_evals.append(dialog.selected_candidate)
            elif dialog.action == "maybe":
                self.maybe_evals.append(dialog.selected_candidate)

        self.update_view()

    def clear_identifications(self):
        self.identified_evals = []
        self.maybe_evals = []
        self.update_view()

    def remove_selected_element(self):
        """Remove the currently selected element in the list."""
        current_row = self.eval_list.currentRow()
        if 0 <= current_row < len(self.identified_evals):
            del self.identified_evals[current_row]
            self.update_view()


if __name__ == "__main__":
    # Ensure we have the package in path for mocks
    sys.path.append("/home/rehak/repos/ops/ecris.analysis")

    csd_path = "/home/rehak/repos/ops/ecris.analysis/data/csds/csd_1762894074"
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = CsdPeakIdentifierApp(csd_path)
    window.show()
    sys.exit(app.exec())
