import numpy as np
import pandas as pd
from typing import Any, List, Set, cast, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path
from scipy.signal import find_peaks

from ops.ecris.analysis.io.read_csd_file import read_csd_from_file_pair
from ops.ecris.analysis.model.element import Element
from ops.ecris.analysis.csd.polynomial_fit import polynomial_fit_mq


@dataclass
class ElementEvaluation:
    s: str
    m: int
    z: int
    a: float
    m_over_q: np.ndarray
    current: np.ndarray
    peak_indices: np.ndarray
    missing_m_over_q: np.ndarray = field(default_factory=lambda: np.array([]))
    missing_current: np.ndarray = field(default_factory=lambda: np.array([]))

    def symbol(self):
        return f"{self.s}-{self.m}"

    def score(self, max_mq: float) -> float:
        """Calculate the fraction of expected peaks found."""
        expected_qs = [self.m / q for q in range(1, self.z + 1)]
        expected_count = len([mq for mq in expected_qs if mq <= max_mq])
        if expected_count == 0:
            return 0.0
        return len(self.peak_indices) / expected_count


def load_and_calibrate_csd(csd_path: Path) -> Any:
    """Load a CSD file pair and perform initial oxygen calibration."""
    csd = read_csd_from_file_pair(csd_path)
    # Default initial calibration using Oxygen-16 (Z=8, q=4 is common)
    csd.m_over_q, _ = polynomial_fit_mq(
        csd, [Element("O", "Oxygen", 16, 8)], 4
    )
    peaks, _ = find_peaks(csd.beam_current, height=0.2, prominence=0.2)
    return csd, peaks


def find_element_peaks(
    peaks: np.ndarray, csd: Any, m: float, z: int, mq_tolerance: float = 0.03
) -> np.ndarray:
    """Identify which peaks match potential m/q values for a given mass.

    Uses an absolute m/q tolerance for consistent matching across all charge states,
    and ensures only the closest peak is assigned to any given charge state.
    """
    if csd.m_over_q is None:
        return np.array([], dtype=int)

    mq_measured = csd.m_over_q[peaks]
    charge_float = m / mq_measured
    charge_int = np.round(charge_float).astype(int)

    # Valid physical charges (1 to Z)
    valid_q = (charge_int >= 1) & (charge_int <= z)
    mq_expected = np.zeros_like(mq_measured)
    np.divide(m, charge_int, out=mq_expected, where=valid_q)

    # Absolute tolerance check
    mq_diff = np.abs(mq_measured - mq_expected)
    within_tolerance = valid_q & (mq_diff <= mq_tolerance)

    # Prevent double-counting: pick the single best peak for each charge state
    best_peaks = []
    for q in np.unique(charge_int[within_tolerance]):
        q_mask = within_tolerance & (charge_int == q)
        candidate_indices = np.where(q_mask)[0]
        best_idx = candidate_indices[np.argmin(mq_diff[candidate_indices])]
        best_peaks.append(peaks[best_idx])

    return np.sort(np.array(best_peaks, dtype=int))


def create_evaluation(isotope: Any, csd: Any, peaks: np.ndarray) -> ElementEvaluation:
    """Create an ElementEvaluation for a given isotope based on detected peaks."""
    mass = float(cast(Any, isotope["m"]))
    z = int(isotope["z"])
    found_peaks = find_element_peaks(peaks, csd, mass, z)

    m_over_q_found = csd.m_over_q[found_peaks] if csd.m_over_q is not None else np.array([])
    current_found = csd.beam_current[found_peaks] if csd.beam_current is not None else np.array([])

    # Identify missing expected peaks within measured range
    missing_m_over_q = []
    missing_current = []
    if csd.m_over_q is not None:
        mq_min, mq_max = csd.m_over_q.min(), csd.m_over_q.max()
        found_qs = np.round(mass / m_over_q_found).astype(int) if len(m_over_q_found) > 0 else []

        for q in range(1, z + 1):
            mq_expected = mass / q
            if mq_min <= mq_expected <= mq_max and q not in found_qs:
                missing_m_over_q.append(mq_expected)
                # Find current at the missing peak location for plotting
                idx = np.argmin(np.abs(csd.m_over_q - mq_expected))
                missing_current.append(csd.beam_current[idx])

    return ElementEvaluation(
        str(isotope["s"]),
        int(np.round(mass)),
        z,
        float(cast(Any, isotope["a"])),
        m_over_q_found,
        current_found,
        found_peaks,
        np.array(missing_m_over_q),
        np.array(missing_current),
    )


def lookup_isotopes(query: str, isotopes_df: pd.DataFrame) -> Any:
    """Lookup isotopes for a given query like 'Ar' or 'Ar-40'."""
    query = query.strip()
    if "-" in query:
        parts = query.split("-")
        symbol = parts[0].capitalize()
        try:
            mass_num = int(parts[1])
            return isotopes_df[(isotopes_df["s"] == symbol) & (isotopes_df.index == mass_num)]
        except (ValueError, IndexError):
            return isotopes_df[0:0]
    else:
        symbol = query.capitalize()
        return isotopes_df[isotopes_df["s"] == symbol]
