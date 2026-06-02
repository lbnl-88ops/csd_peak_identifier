import numpy as np
import webbrowser
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStatusBar, QMessageBox, QLabel, QPushButton, QCheckBox
)
from PySide6.QtCore import Qt, QSettings, QThread, Signal
from PySide6.QtGui import QAction

from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_MUTED, FONT_SANS, VERSION, GITHUB_PAGE_URL, COLOR_ACTION
)
from csd_peak_identifier.gui.styles import (
    MODE_INDICATOR_STYLE, MENU_STYLE, add_label
)
from csd_peak_identifier.gui.canvas import MqPlotCanvas, NavigationToolbar
from csd_peak_identifier.gui.panels import IsotopePanel, PeakPanel, InfoPanel
from csd_peak_identifier.gui.preferences_dialog import PreferencesDialog
from csd_peak_identifier.gui.profile_dialog import ProfileDialog
from csd_peak_identifier.gui.evaluation_mode_dialog import EvaluationModeDialog
from csd_peak_identifier.gui.analysis_dashboard import AnalysisDashboard
from csd_peak_identifier.utils.updater import check_for_updates
from csd_peak_identifier.utils.database import DatabaseManager

class UpdateCheckerThread(QThread):
    finished = Signal(object, object)  # (latest_version, release_url)

    def run(self):
        latest_version, release_url = check_for_updates()
        self.finished.emit(latest_version, release_url)

class CsdPeakIdentifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"CSD Peak Identifier (v{VERSION})")
        self.resize(1200, 800)
        self.coordinator = None
        self.settings = QSettings("LBNL", "CsdPeakIdentifier")
        self.username = None
        
        use_remote = self.settings.value("use_remote_db", False, type=bool)
        self.db = DatabaseManager(use_remote=use_remote)
        
        self.create_widgets()
        self.update_db_status()
        
        # Check for updates automatically if enabled
        if self.settings.value("auto_update_check", True, type=bool):
            self.perform_update_check(quiet=True)

    def update_db_status(self):
        connected = self.db.is_connected_to_remote
        if self.db.use_remote:
            if connected:
                self.db_status_label.setText("DB: REMOTE")
                self.db_status_label.setStyleSheet("color: green; font-weight: bold; margin-right: 10px;")
            else:
                self.db_status_label.setText("DB: REMOTE (OFFLINE)")
                self.db_status_label.setStyleSheet("color: red; font-weight: bold; margin-right: 10px;")
        else:
            self.db_status_label.setText("DB: LOCAL")
            self.db_status_label.setStyleSheet(f"color: {COLOR_MUTED}; font-weight: bold; margin-right: 10px;")

    def create_widgets(self):
        self.setStyleSheet(f"background: {COLOR_BG};" + MENU_STYLE)
        
        # Central Widget and Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5) # Reduced margins to maximize plot area
        main_layout.setSpacing(5)

        # Menu Bar
        self.menu_bar = self.menuBar()
        self.menu_bar.setNativeMenuBar(False) # Ensures menu bar stays inside the window
        file_menu = self.menu_bar.addMenu("&File")
        
        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut("Ctrl+O")
        file_menu.addAction(self.open_action)
        
        file_menu.addSeparator()

        self.switch_user_action = QAction("&Switch Operator...", self)
        self.switch_user_action.triggered.connect(self.switch_user)
        file_menu.addAction(self.switch_user_action)
        
        file_menu.addSeparator()

        self.prefs_action = QAction("&Preferences...", self)
        self.prefs_action.triggered.connect(self.show_preferences)
        file_menu.addAction(self.prefs_action)
        
        file_menu.addSeparator()
        
        self.update_action = QAction("Check for &Updates...", self)
        self.update_action.triggered.connect(lambda: self.perform_update_check(quiet=False))
        file_menu.addAction(self.update_action)
        
        file_menu.addSeparator()

        self.save_eval_action = QAction("&Save Evaluation", self)
        self.save_eval_action.setShortcut("Ctrl+S")
        self.save_eval_action.triggered.connect(self.save_evaluation)
        file_menu.addAction(self.save_eval_action)
        
        file_menu.addSeparator()
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.triggered.connect(self.close)
        file_menu.addAction(self.exit_action)

        # Analysis Menu
        analysis_menu = self.menu_bar.addMenu("&Analysis")
        
        self.eval_mode_action = QAction("&Evaluation Mode...", self)
        self.eval_mode_action.triggered.connect(self.show_evaluation_mode)
        analysis_menu.addAction(self.eval_mode_action)

        self.review_csd_action = QAction("&Review Peer Evaluations...", self)
        self.review_csd_action.setEnabled(False)   # enabled once a CSD is loaded
        self.review_csd_action.triggered.connect(self.show_cross_eval_for_current_csd)
        analysis_menu.addAction(self.review_csd_action)

        self.dashboard_action = QAction("&Lab Analysis Dashboard...", self)
        self.dashboard_action.triggered.connect(self.show_analysis_dashboard)
        analysis_menu.addAction(self.dashboard_action)

        analysis_menu.addSeparator()

        self.peak_params_action = QAction("&Peak search parameters...", self)
        self.peak_params_action.triggered.connect(self.show_peak_params_dialog)
        analysis_menu.addAction(self.peak_params_action)

        # Left Sidebar (Isotopes)
        self.isotope_panel = IsotopePanel()
        main_layout.addWidget(self.isotope_panel, 1)

        # Center Area (Plot)
        center_layout = QVBoxLayout()
        center_layout.setSpacing(2) # Tighter spacing to maximize plot area
        
        self.mode_label = add_label(center_layout, "MODE: PEAK SELECTION")
        self.mode_label.setStyleSheet(
            MODE_INDICATOR_STYLE + f"background: {COLOR_MUTED};"
        )
        self.mode_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.mode_label)

        self.canvas = MqPlotCanvas(self)
        self.canvas.zoom_finished.connect(self.auto_deactivate_zoom)
        center_layout.addWidget(self.canvas, 1)

        self.timestamp_label = QLabel("")
        self.timestamp_label.setStyleSheet(f"font-family: 'monospace'; font-size: 11px; color: {COLOR_MUTED}; margin-top: 2px;")
        self.timestamp_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.timestamp_label)

        # Plot Controls Help
        self.help_label = QLabel("SCROLL: ZOOM | RIGHT-CLICK: PAN")
        self.help_label.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 9px; font-weight: bold; color: {COLOR_MUTED};")
        self.help_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.help_label)

        # Plot Controls
        plot_ctrl_layout = QHBoxLayout()

        self.pan_btn = QPushButton("PAN")
        self.pan_btn.setCheckable(True)
        self.pan_btn.setStyleSheet(
            f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px;"
        )
        self.pan_btn.clicked.connect(self.toggle_pan_mode)

        self.zoom_btn = QPushButton("ZOOM")
        self.zoom_btn.setCheckable(True)
        self.zoom_btn.setStyleSheet(
            f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px;"
        )
        self.zoom_btn.clicked.connect(self.toggle_zoom_mode)
        
        self.reset_btn = QPushButton("RESET VIEW")
        self.reset_btn.setStyleSheet(
            f"font-family: {FONT_SANS}; padding: 5px 15px;"
        )
        self.reset_btn.clicked.connect(self.reset_plot_view)
        
        self.log_y_cb = QCheckBox("LOG Y")
        self.log_y_cb.setStyleSheet(f"font-family: {FONT_SANS}; font-size: 10px; font-weight: bold; color: {COLOR_MUTED}; margin-left: 10px;")
        self.log_y_cb.toggled.connect(self.update_plot_scale)
        
        plot_ctrl_layout.addStretch()
        plot_ctrl_layout.addWidget(self.pan_btn)
        plot_ctrl_layout.addWidget(self.zoom_btn)
        plot_ctrl_layout.addWidget(self.reset_btn)
        plot_ctrl_layout.addWidget(self.log_y_cb)
        plot_ctrl_layout.addStretch()
        center_layout.addLayout(plot_ctrl_layout)

        self.info_panel = InfoPanel()
        center_layout.insertWidget(1, self.info_panel) # Move to top, above canvas
        main_layout.addLayout(center_layout, 8) # Increased stretch factor from 4 to 8

        # Right Sidebar (Peaks)
        self.peak_panel = PeakPanel()
        main_layout.addWidget(self.peak_panel, 1)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.db_status_label = QLabel("DB: LOCAL")
        self.db_status_label.setStyleSheet(f"font-family: {FONT_SANS}; font-weight: bold; margin-right: 10px;")
        self.status_bar.addPermanentWidget(self.db_status_label)

    def toggle_pan_mode(self):
        self.canvas.toggle_pan()
        if self.pan_btn.isChecked():
            # Deactivate zoom button visual state if active
            # We don't call toggle_zoom because Matplotlib's pan() 
            # already deactivated it internally.
            if self.zoom_btn.isChecked():
                self.zoom_btn.setChecked(False)
                self.zoom_btn.setStyleSheet(f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px;")

            self.pan_btn.setStyleSheet(
                f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px; background: {COLOR_ACTION}; color: white;"
            )
            self.status_bar.showMessage("PAN MODE ACTIVE: Click and drag to navigate.")
        else:
            self.pan_btn.setStyleSheet(
                f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px;"
            )
            self.status_bar.showMessage("PAN MODE DEACTIVATED", 2000)

    def toggle_zoom_mode(self):
        self.canvas.toggle_zoom()
        if self.zoom_btn.isChecked():
            # Deactivate pan button visual state if active
            # We don't call toggle_pan because Matplotlib's zoom() 
            # already deactivated it internally.
            if self.pan_btn.isChecked():
                self.pan_btn.setChecked(False)
                self.pan_btn.setStyleSheet(f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px;")

            self.zoom_btn.setStyleSheet(
                f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px; background: {COLOR_ACTION}; color: white;"
            )
            self.status_bar.showMessage("ZOOM MODE ACTIVE: Select a box on the plot to zoom in.")
        else:
            self.zoom_btn.setStyleSheet(
                f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px;"
            )
            self.status_bar.showMessage("ZOOM MODE DEACTIVATED", 2000)

    def auto_deactivate_zoom(self):
        if self.zoom_btn.isChecked():
            self.zoom_btn.setChecked(False)
            self.toggle_zoom_mode()

    def update_plot_scale(self):
        if self.coordinator:
            self.coordinator.update_view()

    def reset_plot_view(self):
        self.canvas.reset_view()
        if self.zoom_btn.isChecked():
            self.zoom_btn.setChecked(False)
            self.zoom_btn.setStyleSheet(f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px;")
        if self.pan_btn.isChecked():
            self.pan_btn.setChecked(False)
            self.pan_btn.setStyleSheet(f"font-family: {FONT_SANS}; font-weight: bold; padding: 5px 15px;")
        if self.coordinator:
            self.coordinator.update_view()
        self.status_bar.showMessage("VIEW RESET", 2000)

    def set_coordinator(self, coordinator):
        self.coordinator = coordinator
        self.open_action.triggered.connect(self.coordinator.open_csd_dialog)
        self.isotope_panel.save_btn.clicked.connect(self.save_evaluation)

    def set_username(self, username):
        self.username = username
        self.status_bar.showMessage(f"LOGGED IN AS: {self.username}")
        self.setWindowTitle(f"CSD Peak Identifier (v{VERSION}) - ECRIS Access: {self.username}")
        if self.coordinator:
            self.coordinator.load_user_parameters(username)

    def switch_user(self):
        users = self.db.get_all_users()
        
        dlg = ProfileDialog(users, last_username=self.username, parent=self)
        if dlg.exec() == ProfileDialog.Accepted:
            new_username = dlg.get_selected_username()
            self.db.add_user(new_username)
            self.db.update_last_used(new_username)
            self.settings.setValue("last_username", new_username)
            self.set_username(new_username)
            self.update_db_status()

    def show_evaluation_mode(self):
        if not self.coordinator:
            return
        
        eval_count, pending_count = self.db.get_user_stats(self.username)
        
        dlg = EvaluationModeDialog(self.username, eval_count, pending_count, parent=self)
        if dlg.exec() == EvaluationModeDialog.Accepted:
            action = dlg.get_action()
            if action == 'pending':
                timestamp = self.db.get_random_pending_timestamp(self.username)
                if timestamp:
                    self.coordinator.open_by_timestamp(timestamp)
            elif action == 'random':
                self.coordinator.open_random_csd()
            self.update_db_status()

    def save_evaluation(self):
        if not self.coordinator:
            return
        self.coordinator.save_current_evaluation()

    def show_peak_params_dialog(self):
        if not self.coordinator:
            return
        self.coordinator.show_peak_parameters_dialog()

    def show_preferences(self):
        dlg = PreferencesDialog(self)
        if dlg.exec() == PreferencesDialog.Accepted:
            use_remote = self.settings.value("use_remote_db", False, type=bool)
            if use_remote != self.db.use_remote:
                self.db.toggle_remote(use_remote)
                self.update_db_status()

    def perform_update_check(self, quiet=False):
        self.update_thread = UpdateCheckerThread(self)
        self.update_thread.finished.connect(lambda v, url: self.handle_update_result(v, url, quiet))
        self.update_thread.start()

    def handle_update_result(self, latest_version, release_url, quiet):
        if latest_version:
            reply = QMessageBox.information(
                self, 
                "Update Available",
                f"A new version (v{latest_version}) of CSD Peak Identifier is available.\n\n"
                "Would you like to visit the download page?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                webbrowser.open(release_url if release_url else GITHUB_PAGE_URL)
        elif not quiet:
            QMessageBox.information(
                self,
                "No Updates Found",
                f"You are running the latest version (v{VERSION})."
            )

    def notify_csd_loaded(self, csd_timestamp: str, display_name: str = ""):
        """
        Called by the Coordinator after a CSD is successfully loaded.
        Enables the 'Review Evaluations' menu action and updates the timestamp label.
        """
        self._current_csd_timestamp = csd_timestamp
        self.review_csd_action.setEnabled(True)
        if display_name:
            self.timestamp_label.setText(f"LOADED DATA: {display_name}")
        else:
            self.timestamp_label.setText(f"LOADED DATA: {csd_timestamp}")

    def show_cross_eval_for_current_csd(self):
        """Opens the CrossEvaluationDialog for whichever CSD is currently loaded."""
        ts = getattr(self, "_current_csd_timestamp", None)
        if not ts:
            return
        from csd_peak_identifier.gui.cross_eval_dialog import CrossEvaluationDialog
        evaluations = self.db.get_all_evaluations_for_csd(ts)
        dlg = CrossEvaluationDialog(ts, evaluations, parent=self)
        dlg.load_requested.connect(self._handle_load_from_cross_eval)
        dlg.exec()

    def show_analysis_dashboard(self):
        """Opens the lab-wide Analysis Dashboard dialog."""
        dlg = AnalysisDashboard(self.db, parent=self)
        dlg.load_csd_requested.connect(self._handle_load_from_cross_eval)
        dlg.exec()

    def _handle_load_from_cross_eval(self, csd_timestamp: str):
        """
        Triggered when the user clicks 'LOAD IN MAIN PLOT' inside a
        CrossEvaluationDialog (directly or forwarded from the dashboard).
        Delegates to the coordinator to locate and open the file.
        """
        if self.coordinator:
            self.coordinator.open_by_timestamp(csd_timestamp)

    def keyPressEvent(self, event):
        if not self.coordinator:
            return super().keyPressEvent(event)
            
        if self.isotope_panel.button_stack.currentIndex() == 1:  # ID Mode
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.coordinator.accept_candidate()
                return True
            elif event.key() == Qt.Key_M:
                self.coordinator.mark_as_maybe()
                return True
            elif event.key() == Qt.Key_N:
                self.coordinator.reject_candidate()
                return True
            elif event.key() == Qt.Key_Escape:
                self.coordinator.exit_identification()
                return True
            return super().keyPressEvent(event)

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.coordinator.start_identification()
        elif event.key() == Qt.Key_Left:
            self.coordinator.navigate_peaks(-1)
        elif event.key() == Qt.Key_Right:
            self.coordinator.navigate_peaks(1)
        else:
            super().keyPressEvent(event)
