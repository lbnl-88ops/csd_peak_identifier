import numpy as np
import pandas as pd
import random
from pathlib import Path
from typing import List, Any, Optional

from PySide6.QtCore import Qt, QObject
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QMainWindow, QListWidgetItem, QDialog, QInputDialog, QMessageBox

from csd_peak_identifier.files.csd_file import CSDFile
from csd_peak_identifier.logic import (
    ElementEvaluation,
    create_evaluation,
    lookup_isotopes,
    load_and_calibrate_csd,
    PeakParameters,
)
from csd_peak_identifier.gui.constants import (
    ISOTOPE_DATA,
    COLOR_INFO,
    COLOR_IDENTIFIED,
    COLOR_MAYBE,
    COLOR_REJECTED,
    COLOR_TARGET,
    COLOR_ACTION,
    FONT_MONO,
    FONT_SANS,
    COLOR_MUTED,
    COLOR_TEXT,
)
from csd_peak_identifier.gui.styles import MODE_INDICATOR_STYLE
from csd_peak_identifier.gui.panels import IsotopePanel, PeakPanel, InfoPanel
from csd_peak_identifier.gui.canvas import MqPlotCanvas
from csd_peak_identifier.gui.open_dialog import CsdOpenDialog
from csd_peak_identifier.files.client import download_filepair, get_remote_files
from csd_peak_identifier.utils.database import DatabaseManager


class Coordinator(QObject):
    def __init__(self, main_window: QMainWindow):
        super().__init__()
        self._main_window = main_window

        # State
        self.isotopes = pd.read_csv(
            ISOTOPE_DATA, delimiter="\\s+", names=["s", "z", "a", "m"]
        )
        self.csd_file: Optional[CSDFile] = None
        self.csd = None
        self.peaks = None
        self.identified: List[ElementEvaluation] = []
        self.maybe: List[ElementEvaluation] = []
        self.rejected_symbols = set()
        self.candidates: List[ElementEvaluation] = []
        self.targeted_mq: Optional[float] = None
        self.peak_parameters = PeakParameters()

        # UI Objects (to be attached)
        self._isotope_panel: Optional[IsotopePanel] = None
        self._peak_panel: Optional[PeakPanel] = None
        self._info_panel: Optional[InfoPanel] = None
        self._plot: Optional[MqPlotCanvas] = None

    def attach(self, obj: Any):
        if isinstance(obj, IsotopePanel):
            self._isotope_panel = obj
        elif isinstance(obj, PeakPanel):
            self._peak_panel = obj
        elif isinstance(obj, InfoPanel):
            self._info_panel = obj
        elif isinstance(obj, MqPlotCanvas):
            self._plot = obj
            self._plot.on_mq_clicked = self.handle_peak_click
        else:
            raise RuntimeError(f"Coordinator passed bad object {obj}")

    def initialize(self, csd_path: Optional[Path] = None):
        self._configure_signals()
        if csd_path:
            self.load_csd(CSDFile(csd_path))
        else:
            self.update_view(rebuild=True)

    def _configure_signals(self):
        # Isotope Panel Signals
        self._isotope_panel.remove_btn.clicked.connect(self.remove_selected)
        self._isotope_panel.clear_btn.clicked.connect(self.clear_all)
        self._isotope_panel.candidate_list.itemSelectionChanged.connect(
            self.handle_candidate_selection
        )
        self._isotope_panel.eval_list.itemSelectionChanged.connect(
            self.handle_isotope_selection
        )
        self._isotope_panel.add_isotope_btn.clicked.connect(self.manual_add_isotope)

        # ID Mode buttons
        self._isotope_panel.accept_btn.clicked.connect(self.accept_candidate)
        self._isotope_panel.maybe_btn.clicked.connect(self.mark_as_maybe)
        self._isotope_panel.reject_btn.clicked.connect(self.reject_candidate)
        self._isotope_panel.exit_btn.clicked.connect(self.exit_identification)

        # Peak Panel Signals
        self._peak_panel.search_btn.clicked.connect(self.start_identification)
        self._peak_panel.peak_list.itemClicked.connect(self.handle_peak_list_click)
        self._peak_panel.peak_list.itemSelectionChanged.connect(
            self.update_association_view
        )
        self._peak_panel.remove_assoc_btn.clicked.connect(
            self.remove_selected_association
        )
        self._peak_panel.assoc_list.itemSelectionChanged.connect(
            self.update_button_states
        )

    def manual_add_isotope(self):
        if self.csd is None:
            return
        text, ok = QInputDialog.getText(
            self._main_window,
            "Manual Isotope Entry",
            "Enter isotope (e.g., 'Ar' or 'Ar-40'):",
        )
        if ok and text:
            matches = lookup_isotopes(text, self.isotopes)
            if matches.empty:
                self._main_window.statusBar().showMessage(
                    f"No isotope found for '{text}'", 3000
                )
                return

            # If multiple isotopes found (like for just "Ar"), take the most abundant stable one
            best_iso = matches.iloc[matches["a"].argmax()]
            ev = create_evaluation(best_iso, self.csd, self.peaks)

            # Check if already identified
            if any(i.symbol() == ev.symbol() for i in self.identified):
                self._main_window.statusBar().showMessage(
                    f"{ev.symbol()} already identified.", 3000
                )
                return

            self.identified.append(ev)
            # Remove from maybe if it was there
            self.maybe = [m for m in self.maybe if m.symbol() != ev.symbol()]
            self.update_view(rebuild=True)
            self._main_window.statusBar().showMessage(f"Added {ev.symbol()}.", 3000)

    def load_csd(self, csd_file: CSDFile):
        self.csd_file = csd_file
        self.csd, self.peaks = load_and_calibrate_csd(csd_file, peak_parameters=self.peak_parameters)
        if self._plot:
            self._plot.reset_view()
        self.clear_all(update=False)
        self.setup_persistent()
        self.update_view(rebuild=True)
        # Notify the main window so the 'Review Evaluations' menu action is enabled.
        if hasattr(self._main_window, "notify_csd_loaded"):
            self._main_window.notify_csd_loaded(self.csd_file.timestamp, self.csd_file.formatted_datetime)

    def setup_persistent(self):
        found = []
        for s in ["O", "N", "C"]:
            matches = lookup_isotopes(s, self.isotopes)
            if not matches.empty:
                ev = create_evaluation(
                    matches.iloc[matches["a"].argmax()], self.csd, self.peaks
                )
                if len(ev.peak_indices) > 0:
                    self.identified.append(ev)
                    found.append(ev.symbol())
        if found:
            print(f"Auto-identified: {', '.join(found)}")

    def update_view(self, candidate=None, rebuild=False):
        target_ev = None
        if self.targeted_mq and self.csd is not None:
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

        # highlight_ev is what we'll draw with the blue lines/markers
        highlight_ev = candidate
        if highlight_ev is None and self._isotope_panel:
            # Only highlight if an item is actually selected
            if self._isotope_panel.eval_list.selectedItems():
                row = self._isotope_panel.eval_list.currentRow()
                if 0 <= row < len(self.identified):
                    highlight_ev = self.identified[row]
                elif (
                    len(self.identified)
                    <= row
                    < (len(self.identified) + len(self.maybe))
                ):
                    highlight_ev = self.maybe[row - len(self.identified)]

            if (
                highlight_ev is None
                and self._isotope_panel.candidate_list.selectedItems()
            ):
                row = self._isotope_panel.candidate_list.currentRow()
                if 0 <= row < len(self.candidates):
                    highlight_ev = self.candidates[row]

        if highlight_ev:
            score = highlight_ev.score(self.csd.m_over_q.max()) if self.csd is not None else 0.0
            self._info_panel.set_candidate_data(highlight_ev, score)
        else:
            self._info_panel.set_candidate_data(None)

        if self._plot:
            title = self.csd_file.formatted_datetime if self.csd_file else None
            use_log_y = self._main_window.log_y_cb.isChecked()
            self._plot.redraw(
                self.csd,
                self.identified + self.maybe,
                highlight_ev,
                target_ev,
                title=title,
                use_log_y=use_log_y,
            )

        if rebuild:
            self.update_candidate_list()
            self.update_identified_list()

        self.update_peak_list()
        self.update_association_view()
        self.update_button_states()

    def update_identified_list(self):
        self._isotope_panel.eval_list.blockSignals(True)
        self._isotope_panel.eval_list.clear()
        max_mq = self.csd.m_over_q.max() if self.csd is not None else 0.0
        for ev in self.identified:
            item = QListWidgetItem(
                f"{ev.symbol()} ({ev.score(max_mq):.2f})"
            )
            item.setForeground(QColor(COLOR_IDENTIFIED))
            self._isotope_panel.eval_list.addItem(item)
        for ev in self.maybe:
            item = QListWidgetItem(
                f"{ev.symbol()} (maybe) ({ev.score(max_mq):.2f})"
            )
            item.setForeground(QColor(COLOR_MAYBE))
            self._isotope_panel.eval_list.addItem(item)
        self._isotope_panel.eval_list.blockSignals(False)

    def update_peak_list(self):
        self._peak_panel.peak_list.blockSignals(True)
        current_mq = (
            self._peak_panel.peak_list.currentItem().data(Qt.UserRole)
            if self._peak_panel.peak_list.currentItem()
            else None
        )

        self._peak_panel.peak_list.clear()
        if self.csd is None or self.peaks is None:
            self._peak_panel.peak_list.blockSignals(False)
            return

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
            txt = f"{'✓' if elems else '●'} {mq:5.2f} | {cur:6.2f}"
            item = QListWidgetItem(txt)
            item.setData(Qt.UserRole, mq)
            if elems:
                item.setForeground(QColor(COLOR_REJECTED))
            self._peak_panel.peak_list.addItem(item)

            if self.targeted_mq and abs(mq - self.targeted_mq) < 0.0001:
                target_item = item
            elif (
                not target_item
                and current_mq is not None
                and abs(mq - current_mq) < 0.0001
            ):
                target_item = item

        if target_item:
            self._peak_panel.peak_list.setCurrentItem(target_item)
            self._peak_panel.peak_list.scrollToItem(target_item)

        self._peak_panel.peak_list.blockSignals(False)

    def handle_peak_click(self, x, y):
        if self.csd is None or self._isotope_panel.button_stack.currentIndex() == 1:
            return
        # Deselect isotope
        self._isotope_panel.eval_list.blockSignals(True)
        self._isotope_panel.eval_list.clearSelection()
        self._isotope_panel.eval_list.blockSignals(False)

        self.targeted_mq = float(
            self.csd.m_over_q[
                self.peaks[np.argmin(np.abs(self.csd.m_over_q[self.peaks] - x))]
            ]
        )
        self.update_view()
        
        # Shift focus to the peak list so arrow keys work immediately
        self._peak_panel.peak_list.setFocus()

    def handle_peak_list_click(self, item):
        if self._isotope_panel.button_stack.currentIndex() == 1:
            return
        # Deselect isotope
        self._isotope_panel.eval_list.blockSignals(True)
        self._isotope_panel.eval_list.clearSelection()
        self._isotope_panel.eval_list.blockSignals(False)

        self.targeted_mq = item.data(Qt.UserRole)
        self.update_view()

    def navigate_peaks(self, direction: int):
        if self.targeted_mq is None or self.csd is None or self._isotope_panel.button_stack.currentIndex() == 1:
            return
        mqs = sorted([float(self.csd.m_over_q[p]) for p in self.peaks])
        idx = np.argmin(np.abs(np.array(mqs) - self.targeted_mq))
        self.targeted_mq = mqs[(idx + direction) % len(mqs)]

        # Also clear isotope selection when navigating peaks
        self._isotope_panel.eval_list.blockSignals(True)
        self._isotope_panel.eval_list.clearSelection()
        self._isotope_panel.eval_list.blockSignals(False)

        self.update_view()

    def handle_candidate_selection(self):
        self.update_view()

    def handle_isotope_selection(self):
        if self._isotope_panel.eval_list.currentRow() < 0:
            return
        # Deselect peak
        self._peak_panel.peak_list.blockSignals(True)
        self._peak_panel.peak_list.clearSelection()
        self._peak_panel.peak_list.blockSignals(False)
        self.targeted_mq = None
        self.update_view()

    def update_button_states(self):
        # 1. Main Mode vs ID Mode
        is_id_mode = self._isotope_panel.button_stack.currentIndex() == 1

        # 2. Identify Peak button (Peak Panel)
        self._peak_panel.search_btn.setEnabled(
            not is_id_mode and self.targeted_mq is not None
        )

        # 3. Remove Identified / Clear All (Sidebar)
        self._isotope_panel.remove_btn.setEnabled(
            not is_id_mode and self._isotope_panel.eval_list.currentRow() >= 0
        )
        self._isotope_panel.clear_btn.setEnabled(
            not is_id_mode and (len(self.identified) > 0 or len(self.maybe) > 0)
        )

        # 4. Add Isotope (Sidebar)
        self._isotope_panel.add_isotope_btn.setEnabled(
            not is_id_mode and self.csd is not None
        )

        # 5. Remove association (Peak Panel)
        self._peak_panel.remove_assoc_btn.setEnabled(
            not is_id_mode and self._peak_panel.assoc_list.currentRow() >= 0
        )

        # 7. Save Evaluation (Sidebar)
        self._isotope_panel.save_btn.setEnabled(
            not is_id_mode and self.csd is not None and (len(self.identified) > 0 or len(self.maybe) > 0)
        )

        # 8. List deactivation during ID mode
        self._isotope_panel.eval_list.setEnabled(not is_id_mode)
        self._peak_panel.peak_list.setEnabled(not is_id_mode)
        self._peak_panel.assoc_list.setEnabled(not is_id_mode)
        self._isotope_panel.candidate_list.setEnabled(is_id_mode)

    def update_candidate_list(self):
        self._isotope_panel.candidate_list.blockSignals(True)
        self._isotope_panel.candidate_list.clear()
        for c in self.candidates:
            item = QListWidgetItem(c.symbol())
            if c.symbol() in self.rejected_symbols:
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(QColor(COLOR_REJECTED))
            self._isotope_panel.candidate_list.addItem(item)
        if self.candidates:
            self._isotope_panel.candidate_list.setCurrentRow(0)
            # Ensure it is selected so update_view picks it up as highlight_ev
            self._isotope_panel.candidate_list.item(0).setSelected(True)
        self._isotope_panel.candidate_list.blockSignals(False)

    def start_identification(self):
        if not self.targeted_mq or self.csd is None:
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
            self._main_window.statusBar().showMessage(
                f"No isotopic matches for m/q {mq:.2f}", 3000
            )
            self.update_candidate_list()
            return

        self.candidates.sort(
            key=lambda c: (c.score(self.csd.m_over_q.max()), c.a), reverse=True
        )

        # Disable peak selection while in ID mode to prevent accidental target changes
        self._peak_panel.peak_list.setEnabled(False)
        self._saved_click_handler = self._plot.on_mq_clicked
        self._plot.on_mq_clicked = None
        
        self._isotope_panel.button_stack.setCurrentIndex(1)  # ID Mode
        self._main_window.mode_label.setText("MODE: PEAK IDENTIFICATION")
        self._main_window.mode_label.setStyleSheet(
            MODE_INDICATOR_STYLE + f"background: {COLOR_TARGET};"
        )
        self._isotope_panel.candidate_header.setText(
            "Candidate isotopes (sorted by score)"
        )
        self._isotope_panel.eval_list.setEnabled(False)
        
        self.update_candidate_list()
        self.update_view()

    def exit_identification(self):
        self.candidates = []
        
        # Re-enable interaction
        self._peak_panel.peak_list.setEnabled(True)
        if hasattr(self, "_saved_click_handler"):
            self._plot.on_mq_clicked = self._saved_click_handler
            del self._saved_click_handler

        self._isotope_panel.button_stack.setCurrentIndex(0)  # Main Mode
        self._main_window.mode_label.setText("MODE: PEAK SELECTION")
        self._main_window.mode_label.setStyleSheet(
            MODE_INDICATOR_STYLE + f"background: {COLOR_MUTED};"
        )
        self._isotope_panel.candidate_header.setText("Candidate isotopes")
        self._isotope_panel.eval_list.setEnabled(True)
        self.update_candidate_list()
        self.update_view()

    def accept_candidate(self):
        row = self._isotope_panel.candidate_list.currentRow()
        if 0 <= row < len(self.candidates):
            selected = self.candidates[row]
            self.maybe = [m for m in self.maybe if m.symbol() != selected.symbol()]
            if not any(i.symbol() == selected.symbol() for i in self.identified):
                self.identified.append(selected)
            self.exit_identification()
            self.update_view(rebuild=True)

    def mark_as_maybe(self):
        row = self._isotope_panel.candidate_list.currentRow()
        if 0 <= row < len(self.candidates):
            selected = self.candidates[row]
            if not any(m.symbol() == selected.symbol() for m in self.maybe) and not any(
                i.symbol() == selected.symbol() for i in self.identified
            ):
                self.maybe.append(selected)
                self.update_view(rebuild=True)
            if row + 1 < self._isotope_panel.candidate_list.count():
                self._isotope_panel.candidate_list.setCurrentRow(row + 1)

    def reject_candidate(self):
        row = self._isotope_panel.candidate_list.currentRow()
        if 0 <= row < len(self.candidates):
            selected = self.candidates[row]
            self.rejected_symbols.add(selected.symbol())
            self.identified = [
                i for i in self.identified if i.symbol() != selected.symbol()
            ]
            self.maybe = [m for m in self.maybe if m.symbol() != selected.symbol()]
            self.update_candidate_list()
            self.update_view(rebuild=True)
            if row + 1 < self._isotope_panel.candidate_list.count():
                self._isotope_panel.candidate_list.setCurrentRow(row + 1)

    def clear_all(self, update=True):
        self.identified, self.maybe, self.candidates = [], [], []
        self.rejected_symbols = set()
        if self._isotope_panel:
            self._isotope_panel.candidate_list.clear()
        if update:
            self.update_view(rebuild=True)

    def remove_selected(self):
        row = self._isotope_panel.eval_list.currentRow()
        if 0 <= row < (len(self.identified) + len(self.maybe)):
            if row < len(self.identified):
                del self.identified[row]
            else:
                del self.maybe[row - len(self.identified)]
            self.update_view(rebuild=True)

    def update_association_view(self):
        self._peak_panel.assoc_list.blockSignals(True)
        self._peak_panel.assoc_list.clear()

        if self.csd is None or self.peaks is None:
            self._peak_panel.assoc_list.blockSignals(False)
            return

        current_peak_item = self._peak_panel.peak_list.currentItem()
        if not current_peak_item:
            self._peak_panel.assoc_list.blockSignals(False)
            return

        mq_val = current_peak_item.data(Qt.UserRole)
        p_idx = self.peaks[np.argmin(np.abs(self.csd.m_over_q[self.peaks] - mq_val))]
        combined = [(ev, "identified") for ev in self.identified] + [
            (ev, "maybe") for ev in self.maybe
        ]

        for ev, category in combined:
            if p_idx in ev.peak_indices:
                txt = f"{ev.symbol()} ({category})"
                item = QListWidgetItem(txt)
                item.setData(Qt.UserRole, (ev.symbol(), category))
                if category == "identified":
                    item.setForeground(QColor(COLOR_IDENTIFIED))
                else:
                    item.setForeground(QColor(COLOR_MAYBE))
                self._peak_panel.assoc_list.addItem(item)
        self._peak_panel.assoc_list.blockSignals(False)

    def remove_selected_association(self):
        item = self._peak_panel.assoc_list.currentItem()
        if not item:
            return
        symbol, category = item.data(Qt.UserRole)
        peak_item = self._peak_panel.peak_list.currentItem()
        if not peak_item:
            return
        mq_val = peak_item.data(Qt.UserRole)
        p_idx = self.peaks[np.argmin(np.abs(self.csd.m_over_q[self.peaks] - mq_val))]

        target_list = self.identified if category == "identified" else self.maybe
        for ev in target_list:
            if ev.symbol() == symbol:
                mask = ev.peak_indices != p_idx
                ev.peak_indices = ev.peak_indices[mask]
                ev.current = ev.current[mask]
                ev.m_over_q = ev.m_over_q[mask]
                if len(ev.peak_indices) == 0:
                    if category == "identified":
                        self.identified = [
                            i for i in self.identified if i.symbol() != symbol
                        ]
                    else:
                        self.maybe = [m for m in self.maybe if m.symbol() != symbol]
                break
        self.update_view(rebuild=True)

    def open_csd_dialog(self):
        dialog = CsdOpenDialog(self._main_window)
        if dialog.exec() == QDialog.Accepted:
            filename = dialog.get_selected_file()
            if filename:
                self.download_and_open(filename)

    def open_by_timestamp(self, timestamp):
        """Finds a remote file matching the timestamp and opens it."""
        try:
            remote_files = get_remote_files()
            for f in remote_files:
                if f.timestamp == timestamp:
                    self.download_and_open(f.filename)
                    return
            QMessageBox.warning(self._main_window, "OPEN ERROR", f"Could not find remote file for {timestamp}")
        except Exception as e:
            QMessageBox.critical(self._main_window, "ERROR", f"Failed to fetch file list: {e}")

    def open_random_csd(self):
        """Opens a random CSD from the server."""
        try:
            remote_files = get_remote_files()
            if not remote_files:
                QMessageBox.warning(self._main_window, "OPEN ERROR", "No files found on server.")
                return
            
            # Optional: filter out already evaluated files?
            # For now, just pick any random one as requested.
            choice = random.choice(remote_files)
            self.download_and_open(choice.filename)
        except Exception as e:
            QMessageBox.critical(self._main_window, "ERROR", f"Failed to fetch file list: {e}")

    def download_and_open(self, csd_filename):
        sb = self._main_window.statusBar()
        sb.showMessage(f"Downloading {csd_filename} and its pair...")
        try:
            new_csd_path = download_filepair(csd_filename)
            if not new_csd_path:
                sb.showMessage(f"Failed to download {csd_filename}", 5000)
                return
            sb.showMessage(f"Loading and calibrating {csd_filename}...")
            self.load_csd(CSDFile(new_csd_path))
            sb.showMessage(f"Successfully loaded {csd_filename}", 3000)
        except Exception as e:
            sb.showMessage(f"Error loading file: {str(e)}", 5000)

    def show_peak_parameters_dialog(self):
        from csd_peak_identifier.gui.peak_parameters_dialog import PeakParametersDialog
        dlg = PeakParametersDialog(self.peak_parameters, parent=self._main_window)
        if dlg.exec() == QDialog.Accepted:
            new_params = dlg.get_params()
            if new_params != self.peak_parameters:
                self.peak_parameters = new_params
                # Save to DB
                username = self._main_window.username
                self._main_window.db.save_peak_parameters(username, {
                    'min_height': self.peak_parameters.min_height,
                    'max_height': self.peak_parameters.max_height,
                    'threshold': self.peak_parameters.threshold,
                    'distance': self.peak_parameters.distance,
                    'prominence': self.peak_parameters.prominance
                })
                
                # Ask to reload
                if self.csd_file:
                    reply = QMessageBox.question(
                        self._main_window,
                        "RELOAD DATA?",
                        "Peak search parameters have changed.\n\nWould you like to reload and re-calibrate the current CSD?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if reply == QMessageBox.Yes:
                        self.load_csd(self.csd_file)

    def load_user_parameters(self, username):
        """Loads user-specific peak parameters from the database."""
        params_row = self._main_window.db.get_peak_parameters(username)
        if params_row:
            self.peak_parameters = PeakParameters(
                min_height=params_row.get('min_height', 0.2),
                max_height=params_row.get('max_height'),
                threshold=params_row.get('threshold'),
                distance=params_row.get('distance'),
                prominance=params_row.get('prominence')
            )
        else:
            self.peak_parameters = PeakParameters() # Default

    def save_current_evaluation(self):
        if not self.csd_file:
            QMessageBox.warning(self._main_window, "SAVE ERROR", "NO CSD FILE LOADED")
            return

        username = self._main_window.username
        timestamp = self.csd_file.timestamp
        
        # Collect isotopes with granular data
        isotopes = []
        for ev in self.identified:
            # Ensure we are passing native Python types (str, int) for SQLite
            isotopes.append((str(ev.symbol()), str(ev.s), int(ev.m), int(ev.z), "identified"))
        for ev in self.maybe:
            isotopes.append((str(ev.symbol()), str(ev.s), int(ev.m), int(ev.z), "maybe"))

        if not isotopes:
            QMessageBox.warning(self._main_window, "SAVE ERROR", "NO ISOTOPES IDENTIFIED")
            return

        success = self._main_window.db.save_evaluation(username, timestamp, isotopes)
        
        if success:
            self._main_window.statusBar().showMessage(f"Evaluation for {timestamp} saved successfully.", 5000)
            
            # Prompt for another review
            reply = QMessageBox.question(
                self._main_window,
                "EVALUATION SAVED",
                "Evaluation saved successfully.\n\nWould you like to evaluate another CSD?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self._main_window.show_evaluation_mode()
        else:
            QMessageBox.critical(self._main_window, "SAVE ERROR", "FAILED TO SAVE EVALUATION TO DATABASE")
