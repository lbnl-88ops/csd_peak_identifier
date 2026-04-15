import sys
from PySide6.QtWidgets import QApplication
from csd_peak_identifier.gui.main_window import CsdPeakIdentifierApp
from csd_peak_identifier.coordinator import Coordinator
from csd_peak_identifier.gui.constants import DEFAULT_CSD

def main():
    app = QApplication(sys.argv)
    app.setStyle("GTK")
    
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
    coordinator.initialize(DEFAULT_CSD)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
