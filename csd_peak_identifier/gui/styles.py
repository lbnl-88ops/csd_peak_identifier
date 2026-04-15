from PySide6.QtWidgets import QLayout, QPushButton, QLabel
from csd_peak_identifier.gui.constants import (
    FONT_SANS, FONT_MONO, COLOR_TEXT, COLOR_GRID, COLOR_PLOT_BG
)

# --- GLOBAL STYLES ---
GROUP_BOX_STYLE = f"""
    QGroupBox {{ 
        font-family: {FONT_SANS}; 
        color: {COLOR_TEXT}; 
        font-weight: bold; 
        border: 1px solid {COLOR_GRID}; 
        margin-top: 1.2ex; 
    }}
    QGroupBox::title {{ 
        subcontrol-origin: margin; 
        left: 8px; 
        padding: 0 0px; 
    }}
"""

LABEL_STYLE = f"font-family: {FONT_SANS}; font-size: 11px; color: {COLOR_TEXT};"
LIST_STYLE = f"background: {COLOR_PLOT_BG}; font-family: {FONT_MONO}; color: {COLOR_TEXT}; border: 1px solid {COLOR_GRID};"
BUTTON_STYLE = f"font-family: {FONT_SANS};"

MODE_INDICATOR_STYLE = f"""
    padding: 4px; 
    font-weight: bold; 
    border-radius: 4px; 
    font-family: {FONT_SANS};
    color: white;
"""

# --- HELPER FUNCTIONS ---
def add_button(layout: QLayout, text: str) -> QPushButton:
    """Helper to create and add a styled button."""
    btn = QPushButton(text)
    btn.setStyleSheet(BUTTON_STYLE)
    layout.addWidget(btn)
    return btn

def add_label(layout: QLayout, text: str) -> QLabel:
    """Helper to create and add a styled label."""
    lbl = QLabel(text)
    lbl.setStyleSheet(LABEL_STYLE)
    layout.addWidget(lbl)
    return lbl
