import sys
import os
from pathlib import Path
from collections import deque
from itertools import product

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not running in a bundle, use the project root
        # This assumes constants.py is in csd_peak_identifier/gui/
        base_path = Path(__file__).parent.parent.parent
        
    return Path(os.path.join(base_path, relative_path))

# --- CONSTANTS ---
VERSION = "0.1.3"
REPO_OWNER = "lbnl-88ops"
REPO_NAME = "csd_peak_identifier"
GITHUB_RELEASES_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
GITHUB_PAGE_URL = f"https://github.com/lbnl-88ops/csd_peak_identifier/releases"

DATA_PATH = get_resource_path("data")
ISOTOPE_DATA = DATA_PATH / "IsotopeData.txt"
DEFAULT_CSD = DATA_PATH / "csds" / "csd_1762894074"

# Retro Cassette Futurism Palette
# Focused on utility, high contrast, and functional status indicators.

# --- Network / Server ---
API_URL = "http://ecris.lbl.gov:5000"

# Temporary folder handling
# On Windows, we want to use the User's Local AppData to ensure write permissions
if sys.platform == "win32":
    TEMP_FOLDER = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "CSDPeakIdentifier" / "tmp"
else:
    # On Linux/macOS, we can stay local to the user home or current dir
    TEMP_FOLDER = Path.expanduser(Path("~/.cache/csd_peak_identifier/tmp"))

# Create the folder if it doesn't exist
try:
    TEMP_FOLDER.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create temp folder {TEMP_FOLDER}: {e}")
    # Fallback to current directory as a last resort
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
FONT_SANS = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Liberation Sans', sans-serif"
