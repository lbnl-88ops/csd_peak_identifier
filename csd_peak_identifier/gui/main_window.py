import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from csd_peak_identifier.gui.constants import (
    COLOR_BG, COLOR_MUTED, FONT_SANS
)
from csd_peak_identifier.gui.styles import MODE_INDICATOR_STYLE, add_label
from csd_peak_identifier.gui.canvas import MqPlotCanvas, NavigationToolbar
from csd_peak_identifier.gui.panels import IsotopePanel, PeakPanel, InfoPanel

class CsdPeakIdentifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSD Peak Identifier")
        self.resize(1200, 800)
        self.coordinator = None
        self.create_widgets()

    def create_widgets(self):
        self.setStyleSheet(f"background: {COLOR_BG};")
        
        # Central Widget and Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Menu Bar
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("&File")
        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut("Ctrl+O")
        file_menu.addAction(self.open_action)

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
