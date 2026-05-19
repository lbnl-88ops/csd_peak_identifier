import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from csd_peak_identifier.gui.main_window import CsdPeakIdentifierApp
from csd_peak_identifier.coordinator import Coordinator
from csd_peak_identifier.gui.constants import DEFAULT_CSD

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    app.setStyle("GTK")
    
    # Set window icon
    icon_path = get_resource_path("icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create the visual shell
    window = CsdPeakIdentifierApp()
    
    # Create the Conductor
    coordinator = Coordinator(window)
    
    # Attach widgets to the Conductor
    coordinator.attach(window.canvas)
    coordinator.attach(window.isotope_panel)
    coordinator.attach(window.peak_panel)
    coordinator.attach(window.info_panel)
    
    # Wire everything together
    window.set_coordinator(coordinator)
    
    # Initialize state and show
    coordinator.initialize()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
