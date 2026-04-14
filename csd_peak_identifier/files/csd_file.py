import logging
import os
from pathlib import Path
from typing import List

from ops.ecris.analysis.model import CSD
from ops.ecris.analysis.io.read_csd_file import (
    _file_raw_timestamp,
    read_csd_from_file_pair,
    _file_formatted_timestamp,
)

class CSDFile:
    def __init__(self, path: Path, file_size: float = 0):
        self.path = path
        self.filename = self.path.name
        self.file_size: float = file_size
        self.valid: bool = True
        self.timestamp = _file_formatted_timestamp(path)
        self.raw_timestamp = _file_raw_timestamp(path)
        self._csd = None

    def __eq__(self, value: object) -> bool:
        if isinstance(value, CSDFile):
            return value.filename == self.filename
        return False

    @property
    def formatted_datetime(self) -> str:
        return self.timestamp if self.timestamp is not None else "Invalid timestamp"

    @property
    def csd(self) -> CSD | None:
        if self._csd is None:
            try:
                logging.info(f"Loading CSD data for file {self.filename}")
                self._csd = read_csd_from_file_pair(self.path)
            except Exception as e:
                logging.error(f"Error reading CSD file: {e}")
                self.valid = False
                return None
        return self._csd

    @property
    def list_value(self) -> str:
        ts = self.raw_timestamp
        if ts is not None:
            return f"{ts:.0f} ({self.formatted_datetime})"
        else:
            return f"UNKNOWN ({self.filename})"

def get_local_files(path: Path) -> List[CSDFile]:
    glob = "csd_" + "[0-9]" * 10
    files = []
    for p in Path(path).glob(glob):
        if p.is_file():
            files.append(CSDFile(p, file_size=os.path.getsize(p)))
    # Sort reversed by timestamp
    return sorted(files, key=lambda f: f.raw_timestamp if f.raw_timestamp else 0, reverse=True)
