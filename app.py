import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSettings
from csd_peak_identifier.gui.main_window import CsdPeakIdentifierApp
from csd_peak_identifier.gui.profile_dialog import ProfileDialog
from csd_peak_identifier.coordinator import Coordinator
from csd_peak_identifier.gui.constants import DEFAULT_CSD, get_resource_path
from csd_peak_identifier.utils.database import DatabaseManager

def main():
    app = QApplication(sys.argv)
    
    # Set window icon
    icon_path = get_resource_path("icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Initialize Database and handle Profile Selection
    db = DatabaseManager()
    settings = QSettings("LBNL", "CsdPeakIdentifier")
    
    users = db.get_all_users()
    last_user = settings.value("last_username", "")
    
    profile_dlg = ProfileDialog(users, last_username=last_user)
    if profile_dlg.exec() != ProfileDialog.Accepted:
        sys.exit(0)
        
    username = profile_dlg.get_selected_username()
    db.add_user(username)
    db.update_last_used(username)
    settings.setValue("last_username", username)
    
    # Create the visual shell
    window = CsdPeakIdentifierApp()
    window.set_username(username)
    
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
