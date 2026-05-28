import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSettings

# Fix Matplotlib font warnings by setting a clean font preference early
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Liberation Sans', 'sans-serif']
matplotlib.rcParams['font.family'] = 'sans-serif'

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
    app.processEvents()
    
    # 3. Handle Welcome flow
    # Use the database manager already initialized in the main window
    db = window.db
    users = db.get_all_users()
    last_user = settings.value("last_username", "")
    
    welcome_dlg = WelcomeDialog(db, users, last_username=last_user, parent=window)
    
    # Connect update checker result to the welcome dialog if it's still open
    def on_update_result(latest_version, release_url, quiet):
        if latest_version:
            welcome_dlg.set_update_status(f"CRITICAL SYSTEM UPDATE AVAILABLE: v{latest_version}", is_alert=True)
        else:
            welcome_dlg.set_update_status(f"SYSTEM VERSION v{VERSION} IS CURRENT")
            
    window.update_thread.finished.connect(on_update_result)
    
    # Pre-set if thread is already finished (unlikely but possible)
    if not window.update_thread.isRunning():
        # We can't easily get the result here without modification to CsdPeakIdentifierApp
        # but the signal will fire once it starts.
        pass

    if welcome_dlg.exec() != QDialog.Accepted:
        sys.exit(0)
        
    username, action, use_remote = welcome_dlg.get_action_details()
    db.add_user(username)
    db.update_last_used(username)
    settings.setValue("last_username", username)
    settings.setValue("use_remote_db", use_remote)
    window.set_username(username)
    window.update_db_status() # Update status bar to match final state
    
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
