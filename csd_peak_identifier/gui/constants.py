from pathlib import Path
from collections import deque
from itertools import product

# --- CONSTANTS ---
CURRENT_DIR = Path(__file__).parent.parent
DATA_PATH = CURRENT_DIR.parent / "data"
ISOTOPE_DATA = DATA_PATH / "IsotopeData.txt"
DEFAULT_CSD = DATA_PATH / "csds" / "csd_1762894074"

# Retro Cassette Futurism Palette
# Focused on utility, high contrast, and functional status indicators.

# --- Network / Server ---
API_URL = "http://ecris.lbl.gov:5000"
TEMP_FOLDER = Path("./tmp/")
# These follow a "Functional Action" philosophy for high-pressure technical environments.

COLOR_BG = "#f4f1ea"            # Primary enclosure/chassis
COLOR_PLOT_BG = "#fdfdfd"       # High-contrast readout area
COLOR_GRID = "#e0e0e0"          # Subtle grid lines
COLOR_TEXT = "#262626"          # Primary legend/data text

# Functional Status Colors
COLOR_ACTION = "#d55e00"        # Vermilion: Active targets, Primary actions (Search/Accept)
COLOR_INFO = "#0072b2"          # Dark Blue: Informational candidates, Browsing
COLOR_SUCCESS = "#009e73"       # Green: Confirmed/Identified data
COLOR_CAUTION = "#e69f00"       # Amber: "Maybe" status, Warnings
COLOR_MUTED = "#909090"         # Grey: Rejected data, Taken peaks, Background noise

# Legacy aliases for backward compatibility (to be phased out if needed, but keeping for now)
COLOR_TARGET = COLOR_ACTION
COLOR_CANDIDATE = COLOR_INFO
COLOR_IDENTIFIED = COLOR_SUCCESS
COLOR_MAYBE = COLOR_CAUTION
COLOR_REJECTED = COLOR_MUTED

# Styling
MARKERS = ["v", "^", "p", "d", "*", "D"]
SHADES = ["white", "#f0f0f0", "white"]
# Preferred font stack for maximum readability and cross-platform consistency.
FONT_MONO = "Consolas, 'Liberation Mono', Menlo, Monaco, 'DejaVu Sans Mono', monospace"
