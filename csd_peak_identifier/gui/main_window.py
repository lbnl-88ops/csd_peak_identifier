import numpy as np
import pandas as pd
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStatusBar, QListWidget, QListWidgetItem, QStackedWidget,
    QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QAction

from csd_peak_identifier.logic import (
    ElementEvaluation, create_evaluation, lookup_isotopes, load_and_calibrate_csd
)
from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_PLOT_BG, COLOR_TARGET, ISOTOPE_DATA,
    COLOR_IDENTIFIED, COLOR_MAYBE, COLOR_REJECTED, FONT_MONO, COLOR_TEXT,
    COLOR_ACTION, COLOR_MUTED, COLOR_INFO, COLOR_GRID
)
from csd_peak_identifier.gui.canvas import MqPlotCanvas
from csd_peak_identifier.gui.open_dialog import CsdOpenDialog
from csd_peak_identifier.files.client import download_filepair

class CsdPeakIdentifierApp(QMainWindow):
    def __init__(self, csd_path):
        super().__init__()
        self.setWindowTitle("CSD Peak Identifier")
        self.resize(1200, 800)
        self.isotopes = pd.read_csv(
            ISOTOPE_DATA, delimiter="\\s+", names=["s", "z", "a", "m"]
        )
        self.csd, self.peaks = load_and_calibrate_csd(Path(csd_path))
        self.identified, self.targeted_mq = [], None
        self.maybe = []
        self.rejected_symbols = set()
        self.candidates = []

        self.setStyleSheet(f"background: {COLOR_BG};")
        self.setStyleSheet(f"""
            QMainWindow {{ background: {COLOR_BG}; }}
            QListWidget {{ 
                background: {COLOR_PLOT_BG}; 
                font-family: {FONT_MONO}; 
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_GRID};
            }}
            QListWidget::item:selected {{ 
                background: palette(highlight); 
                color: palette(highlightedText); 
            }}
            QPushButton {{
                font-family: {FONT_MONO};
                padding: 4px;
            }}
        """)
        main_layout = QHBoxLayout(QWidget(self))
        self.setCentralWidget(main_layout.parent())

        # Menu Bar
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("&File")
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_csd_dialog)
        file_menu.addAction(open_action)

        # UI Columns
        sidebar = QVBoxLayout()
        main_layout.addLayout(sidebar, 1)

        center_layout = QVBoxLayout()
        
        # Mode Indicator
        self.mode_label = QLabel("MODE: PEAK SELECTION")
        self.mode_label.setStyleSheet(
            f"background: {COLOR_MUTED}; color: white; padding: 4px; font-weight: bold; border-radius: 4px; font-family: {FONT_MONO};"
        )
        self.mode_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.mode_label)

        self.canvas = MqPlotCanvas(self)
        self.canvas.on_mq_clicked = self.handle_peak_click
        center_layout.addWidget(self.canvas, 1)

        self.info_label = QLabel("Select a candidate to see details")
        self.info_label.setStyleSheet(
            f"padding: 2px; font-size: 13px; font-family: {FONT_MONO}; color: {COLOR_TEXT};"
        )
        self.info_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.info_label, 0)
        main_layout.addLayout(center_layout, 4)

        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 1)

        # Elements List
        self.eval_list = QListWidget()
        self.eval_list.setStyleSheet(f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        sidebar.addWidget(QLabel("Identified Elements"))
        sidebar.addWidget(self.eval_list, 1)

        # Candidate List
        self.candidate_list = QListWidget()
        self.candidate_list.setStyleSheet(f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        self.candidate_list.itemSelectionChanged.connect(self.handle_candidate_selection)
        self.candidate_header = QLabel("Candidate Elements")
        sidebar.addWidget(self.candidate_header)
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
            btn.setStyleSheet(style + f"font-family: {FONT_MONO};")
            main_btn_layout.addWidget(btn)

        # ID Buttons Panel
        self.id_btn_panel = QWidget()
        id_btn_layout = QVBoxLayout(self.id_btn_panel)
        id_btn_layout.setContentsMargins(0, 0, 0, 0)
        id_btn_layout.setSpacing(0)
        id_btn_layout.addStretch()
        self.button_stack.addWidget(self.id_btn_panel)

        for txt, func, style in [
            ("Accept Candidate (Enter)", self.accept_candidate, f"background: {COLOR_ACTION}; color: white; font-weight: bold;"),
            ("Mark as Maybe", self.mark_as_maybe, ""),
            ("Reject Candidate", self.reject_candidate, ""),
            ("Exit Peak ID (Esc)", self.exit_identification, ""),
        ]:
            btn = QPushButton(txt)
            btn.clicked.connect(func)
            btn.setStyleSheet(style + f"font-family: {FONT_MONO};")
            id_btn_layout.addWidget(btn)

        self.button_stack.setCurrentIndex(0)

        # Peaks List
        self.peak_list = QListWidget()
        self.peak_list.setStyleSheet(f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        self.peak_list.itemClicked.connect(self.handle_peak_list_click)
        self.peak_list.itemSelectionChanged.connect(self.update_association_view)
        right_panel.addWidget(QLabel("Detected Peaks"))
        right_panel.addWidget(self.peak_list, 1)

        # Peak Associations List (Mirror of Sidebar structure)
        self.assoc_list = QListWidget()
        self.assoc_list.setStyleSheet(f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT};")
        right_panel.addWidget(QLabel("Peak Associations"))
        right_panel.addWidget(self.assoc_list, 1)

        self.remove_assoc_btn = QPushButton("Remove Association")
        self.remove_assoc_btn.clicked.connect(self.remove_selected_association)
        self.remove_assoc_btn.setStyleSheet(f"font-family: {FONT_MONO};")
        right_panel.addWidget(self.remove_assoc_btn, 0)

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
                f"<b style='color:{COLOR_INFO}'>Candidate:</b> {candidate.symbol()} | "
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
                item = QListWidgetItem(
                    f"{ev.symbol()} ({ev.score(self.csd.m_over_q.max()):.2f})"
                )
                item.setForeground(QColor(COLOR_IDENTIFIED))
                self.eval_list.addItem(item)
            for ev in self.maybe:
                item = QListWidgetItem(
                    f"{ev.symbol()} (maybe) ({ev.score(self.csd.m_over_q.max()):.2f})"
                )
                item.setForeground(QColor(COLOR_MAYBE))
                self.eval_list.addItem(item)
            self.eval_list.blockSignals(False)
        self.update_peak_list()
        self.update_association_view()

    def update_peak_list(self):
        self.peak_list.blockSignals(True)
        # Store current selection to restore it after clear if no new target
        current_mq = self.peak_list.currentItem().data(Qt.UserRole) if self.peak_list.currentItem() else None
        
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
                item.setForeground(QColor(COLOR_REJECTED))
            self.peak_list.addItem(item)
            
            # Prioritize the targeted_mq for selection and scrolling
            if self.targeted_mq and abs(mq - self.targeted_mq) < 0.0001:
                target_item = item
            elif not target_item and current_mq is not None and abs(mq - current_mq) < 0.0001:
                target_item = item

        if target_item:
            self.peak_list.setCurrentItem(target_item)
            # Scroll to the selected item to ensure visibility
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
        # update_view will call update_peak_list and update_association_view
        self.update_view()

    def handle_candidate_selection(self):
        self.update_view()

    def update_candidate_list(self):
        self.candidate_list.blockSignals(True)
        self.candidate_list.clear()
        for c in self.candidates:
            item = QListWidgetItem(c.symbol())
            if c.symbol() in self.rejected_symbols:
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(QColor(COLOR_REJECTED))
            self.candidate_list.addItem(item)
        if self.candidates:
            self.candidate_list.setCurrentRow(0)
        self.candidate_list.blockSignals(False)

    def keyPressEvent(self, event):
        if self.button_stack.currentIndex() == 1: # ID Mode
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.accept_candidate()
                return True
            elif event.key() == Qt.Key_Escape:
                self.exit_identification()
                return True
            return super().keyPressEvent(event)

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.start_identification()
        elif event.key() in (Qt.Key_Left, Qt.Key_Right):
            mqs = sorted([float(self.csd.m_over_q[p]) for p in self.peaks])
            idx = (
                np.argmin(np.abs(np.array(mqs) - self.targeted_mq))
                if self.targeted_mq is not None
                else 0
            )
            self.targeted_mq = mqs[
                (idx + (1 if event.key() == Qt.Key_Right else -1)) % len(mqs)
            ]
            self.update_view()
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
        self.mode_label.setText("MODE: PEAK IDENTIFICATION")
        self.mode_label.setStyleSheet(
            f"background: {COLOR_TARGET}; color: white; padding: 4px; font-weight: bold; border-radius: 4px; font-family: {FONT_MONO};"
        )
        self.candidate_header.setText("Candidate Elements (Sorted by Score)")
        self.eval_list.setEnabled(False)
        self.peak_list.setEnabled(False)
        self.update_candidate_list()
        self.update_view()

    def exit_identification(self):
        self.candidates = []
        self.button_stack.setCurrentIndex(0) # Main Mode
        self.mode_label.setText("MODE: PEAK SELECTION")
        self.mode_label.setStyleSheet(
            f"background: {COLOR_MUTED}; color: white; padding: 4px; font-weight: bold; border-radius: 4px; font-family: {FONT_MONO};"
        )
        self.candidate_header.setText("Candidate Elements")
        self.eval_list.setEnabled(True)
        self.peak_list.setEnabled(True)
        self.update_candidate_list()
        self.update_view()

    def accept_candidate(self):
        row = self.candidate_list.currentRow()
        if 0 <= row < len(self.candidates):
            selected = self.candidates[row]
            # remove from maybe if it was there (checking by symbol)
            self.maybe = [m for m in self.maybe if m.symbol() != selected.symbol()]
            if not any(i.symbol() == selected.symbol() for i in self.identified):
                self.identified.append(selected)
            self.exit_identification()
            self.update_view(rebuild=True)

    def mark_as_maybe(self):
        row = self.candidate_list.currentRow()
        if 0 <= row < len(self.candidates):
            selected = self.candidates[row]
            if not any(m.symbol() == selected.symbol() for m in self.maybe) and \
               not any(i.symbol() == selected.symbol() for i in self.identified):
                self.maybe.append(selected)
                self.update_view(rebuild=True)
            # auto-advance
            if row + 1 < self.candidate_list.count():
                self.candidate_list.setCurrentRow(row + 1)

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
            # auto-advance
            if row + 1 < self.candidate_list.count():
                self.candidate_list.setCurrentRow(row + 1)

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

    def update_association_view(self):
        self.assoc_list.blockSignals(True)
        self.assoc_list.clear()
        
        current_peak_item = self.peak_list.currentItem()
        if not current_peak_item:
            self.assoc_list.blockSignals(False)
            return

        mq_val = current_peak_item.data(Qt.UserRole)
        # Find the peak index corresponding to this mq
        p_idx = self.peaks[np.argmin(np.abs(self.csd.m_over_q[self.peaks] - mq_val))]
        
        combined = [(ev, "identified") for ev in self.identified] + \
                   [(ev, "maybe") for ev in self.maybe]
        
        for ev, category in combined:
            if p_idx in ev.peak_indices:
                txt = f"{ev.symbol()} ({category})"
                item = QListWidgetItem(txt)
                item.setData(Qt.UserRole, (ev.symbol(), category))
                if category == "identified":
                    item.setForeground(QColor(COLOR_IDENTIFIED))
                else:
                    item.setForeground(QColor(COLOR_MAYBE))
                self.assoc_list.addItem(item)
        
        self.assoc_list.blockSignals(False)

    def remove_selected_association(self):
        item = self.assoc_list.currentItem()
        if not item:
            return
            
        symbol, category = item.data(Qt.UserRole)
        
        # Get current peak index from peak_list
        peak_item = self.peak_list.currentItem()
        if not peak_item:
            return
        mq_val = peak_item.data(Qt.UserRole)
        p_idx = self.peaks[np.argmin(np.abs(self.csd.m_over_q[self.peaks] - mq_val))]

        # Find the evaluation and remove the peak index
        target_list = self.identified if category == "identified" else self.maybe
        for ev in target_list:
            if ev.symbol() == symbol:
                # Remove p_idx from ev.peak_indices, current, and m_over_q
                mask = ev.peak_indices != p_idx
                ev.peak_indices = ev.peak_indices[mask]
                ev.current = ev.current[mask]
                ev.m_over_q = ev.m_over_q[mask]
                
                # If no peaks left, remove the evaluation entirely
                if len(ev.peak_indices) == 0:
                    if category == "identified":
                        self.identified = [i for i in self.identified if i.symbol() != symbol]
                    else:
                        self.maybe = [m for m in self.maybe if m.symbol() != symbol]
                break
                
        self.update_view(rebuild=True)

    def open_csd_dialog(self):
        dialog = CsdOpenDialog(self)
        # Use dialog.exec() or dialog.exec_()
        from PySide6.QtWidgets import QDialog
        if dialog.exec() == QDialog.Accepted:
            filename = dialog.get_selected_file()
            if filename:
                self.download_and_open(filename)

    def download_and_open(self, csd_filename):
        self.status_bar.showMessage(f"Downloading {csd_filename} and its pair...")
        try:
            new_csd_path = download_filepair(csd_filename)
            if not new_csd_path:
                self.status_bar.showMessage(f"Failed to download {csd_filename}", 5000)
                return

            # Now load it
            self.status_bar.showMessage(f"Loading and calibrating {csd_filename}...")
            self.csd, self.peaks = load_and_calibrate_csd(new_csd_path)
            
            # Reset identification state for the new file
            self.clear_all()
            self.setup_persistent()
            self.update_view(rebuild=True)
            self.status_bar.showMessage(f"Successfully loaded {csd_filename}", 3000)
            
        except Exception as e:
            self.status_bar.showMessage(f"Error loading file: {str(e)}", 5000)
