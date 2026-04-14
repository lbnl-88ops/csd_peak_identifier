import sys
from PySide6.QtWidgets import QApplication
from csd_peak_identifier.gui.main_window import CsdPeakIdentifierApp
from csd_peak_identifier.gui.constants import DEFAULT_CSD


def main():
    app = QApplication(sys.argv)
    app.setStyle("GTK")
    window = CsdPeakIdentifierApp(DEFAULT_CSD)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
