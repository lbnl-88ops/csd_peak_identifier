from pathlib import Path
from collections import deque
from itertools import product

# --- CONSTANTS ---
CURRENT_DIR = Path(__file__).parent.parent
DATA_PATH = CURRENT_DIR.parent / "data"
ISOTOPE_DATA = DATA_PATH / "IsotopeData.txt"
DEFAULT_CSD = DATA_PATH / "csds" / "csd_1762894074"

# Colorblind-friendly Professional palette (Okabe-Ito)
COLOR_BG = "#f4f1ea"
COLOR_PLOT_BG = "#ffffff"
COLOR_GRID = "#d1d1d1"
COLOR_TARGET = "#d55e00"  # Vermilion (High contrast for colorblindness)
COLOR_CANDIDATE = "#0072b2"  # Dark Blue
COLOR_IDENTIFIED_OUTLINE = "#2f3640"
MARKERS = ["v", "^", "p", "d", "*", "D"]
SHADES = ["white", "gray", "white"]
