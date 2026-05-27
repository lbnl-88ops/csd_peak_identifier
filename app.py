import sys
import os
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSettings
from csd_peak_identifier.gui.main_window import CsdPeakIdentifierApp
from csd_peak_identifier.gui.welcome_dialog import WelcomeDialog
from csd_peak_identifier.coordinator import Coordinator
from csd_peak_identifier.gui.constants import DEFAULT_CSD, get_resource_path
from csd_peak_identifier.utils.database import DatabaseManager

def main():
    app = QApplication(sys.argv)
    
    # Set window icon
    icon_path = get_resource_path("icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    settings = QSettings("LBNL", "CsdPeakIdentifier")
    
    # 1. Create the visual shell (Hidden for now or shown?)
    # User said: "User opens application, it opens."
    # Then: "Welcome window pops up"
    window = CsdPeakIdentifierApp()
    
    # 2. Create the Conductor
    coordinator = Coordinator(window)
    
    # Attach widgets to the Conductor
    coordinator.attach(window.canvas)
    coordinator.attach(window.isotope_panel)
    coordinator.attach(window.peak_panel)
    coordinator.attach(window.info_panel)
    
    # Wire everything together
    window.set_coordinator(coordinator)
    
    # Initialize state
    coordinator.initialize()
    window.show()
    
    # 3. Handle Welcome flow
    use_remote = settings.value("use_remote_db", False, type=bool)
    db = DatabaseManager(use_remote=use_remote)
    users = db.get_all_users()
    last_user = settings.value("last_username", "")
    
    welcome_dlg = WelcomeDialog(db, users, last_username=last_user, parent=window)
    if welcome_dlg.exec() != QDialog.Accepted:
        sys.exit(0)
        
    username, action = welcome_dlg.get_action_details()
    db.add_user(username)
    db.update_last_used(username)
    settings.setValue("last_username", username)
    window.set_username(username)
    
    # 4. Execute Quick Start action
    if action == 'open':
        coordinator.open_csd_dialog()
    elif action == 'pending':
        timestamp = db.get_random_pending_timestamp(username)
        if timestamp:
            coordinator.open_by_timestamp(timestamp)
    elif action == 'random':
        coordinator.open_random_csd()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
