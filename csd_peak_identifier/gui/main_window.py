import numpy as np
import webbrowser
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QSettings, QThread, Signal
from PySide6.QtGui import QAction

from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_MUTED, FONT_SANS, VERSION, GITHUB_PAGE_URL
)
from csd_peak_identifier.gui.styles import (
    MODE_INDICATOR_STYLE, MENU_STYLE, add_label
)
from csd_peak_identifier.gui.canvas import MqPlotCanvas, NavigationToolbar
from csd_peak_identifier.gui.panels import IsotopePanel, PeakPanel, InfoPanel
from csd_peak_identifier.gui.preferences_dialog import PreferencesDialog
from csd_peak_identifier.utils.updater import check_for_updates

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
        self.create_widgets()
        
        # Check for updates automatically if enabled
        if self.settings.value("auto_update_check", True, type=bool):
            self.perform_update_check(quiet=True)

    def create_widgets(self):
        self.setStyleSheet(f"background: {COLOR_BG};" + MENU_STYLE)
        
        # Central Widget and Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Menu Bar
        self.menu_bar = self.menuBar()
        self.menu_bar.setNativeMenuBar(False) # Ensures menu bar stays inside the window
        file_menu = self.menu_bar.addMenu("&File")
        
        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut("Ctrl+O")
        file_menu.addAction(self.open_action)
        
        file_menu.addSeparator()
        
        self.prefs_action = QAction("&Preferences...", self)
        self.prefs_action.triggered.connect(self.show_preferences)
        file_menu.addAction(self.prefs_action)
        
        file_menu.addSeparator()
        
        self.update_action = QAction("Check for &Updates...", self)
        self.update_action.triggered.connect(lambda: self.perform_update_check(quiet=False))
        file_menu.addAction(self.update_action)
        
        file_menu.addSeparator()
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.triggered.connect(self.close)
        file_menu.addAction(self.exit_action)

        # Left Sidebar (Isotopes)
        self.isotope_panel = IsotopePanel()
        main_layout.addWidget(self.isotope_panel, 1)

        # Center Area (Plot)
        center_layout = QVBoxLayout()
        
        self.mode_label = add_label(center_layout, "MODE: PEAK SELECTION")
        self.mode_label.setStyleSheet(
            MODE_INDICATOR_STYLE + f"background: {COLOR_MUTED};"
        )
        self.mode_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.mode_label)

        self.canvas = MqPlotCanvas(self)
        center_layout.addWidget(self.canvas, 1)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet(f"background: {COLOR_BG}; border: none; font-family: {FONT_SANS};")
        center_layout.addWidget(self.toolbar)

        self.info_panel = InfoPanel()
        center_layout.addWidget(self.info_panel, 0)
        main_layout.addLayout(center_layout, 4)

        # Right Sidebar (Peaks)
        self.peak_panel = PeakPanel()
        main_layout.addWidget(self.peak_panel, 1)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def set_coordinator(self, coordinator):
        self.coordinator = coordinator
        self.open_action.triggered.connect(self.coordinator.open_csd_dialog)

    def show_preferences(self):
        dlg = PreferencesDialog(self)
        dlg.exec()

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
