from logging import getLogger
from pathlib import Path
from typing import List

import requests
from csd_peak_identifier.gui.constants import API_URL, TEMP_FOLDER
from csd_peak_identifier.files.csd_file import CSDFile

_log = getLogger(__name__)

def list_files() -> List[Path]:
    """Fetch the list of files from the server, as Path objects."""
    url = f"{API_URL}/files"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return [Path(filename) for filename in response.json()]
        else:
            _log.error(f"Failed to retrieve files from {url}")
            return []
    except Exception as e:
        _log.error(f"Error fetching file list: {e}")
        return []

def get_remote_files() -> List[CSDFile]:
    """Returns a list of CSDFile objects for all files found on the server."""
    file_paths = list_files()
    csd_files = []
    for p in file_paths:
        # Check name of the path (more robust if server returns full paths)
        if p.name.startswith("csd_"):
            csd_files.append(CSDFile(p))
    
    # Sort reversed by timestamp (derived from filename in CSDFile.__init__)
    return sorted(csd_files, key=lambda f: f.raw_timestamp if f.raw_timestamp else 0, reverse=True)

def download_filepair(csd_filename: str) -> Path | None:
    """Download the csd and dsht pair, returning the Path to the downloaded csd."""
    dsht_filename = csd_filename.replace("csd", "dsht")
    download_file(dsht_filename)
    return download_file(csd_filename)

def download_file(filename: str) -> Path | None:
    """Download a file from the API and save it as a temporary file."""
    _log.info(f"Attempting to download {filename}")
    TEMP_FOLDER.mkdir(exist_ok=True)
    try:
        # Use filename as provided to get the content
        response = requests.get(f"{API_URL}/download/{filename}", timeout=10)
        if response.status_code == 200:
            # We only save the filename part locally (in case filename is a path)
            local_filename = Path(filename).name
            temp_file = TEMP_FOLDER / local_filename
            with open(temp_file, "wb") as f:
                f.write(response.content)
            return temp_file
        else:
            _log.error(f"File {filename} not found on server.")
            return None
    except Exception as e:
        _log.error(f"Error downloading {filename}: {e}")
        return None

def clear_temp_files() -> None:
    if TEMP_FOLDER.exists():
        for file in TEMP_FOLDER.glob("*"):
            if file.is_file():
                file.unlink()
