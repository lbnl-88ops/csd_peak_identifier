"""
consensus.py — Cross-Evaluation Agreement Analysis

Given a list of per-operator evaluations for a single CSD, computes which
isotopes each operator identified, the degree of agreement between operators,
and a labeled consensus level for each isotope.

This module contains pure data logic only. No UI, no science, no judgments.
The scientist interprets the results. This code only counts and categorizes.

Input format (from DatabaseManager.get_all_evaluations_for_csd):
    [
        {
            'operator': 'Alice',
            'isotopes': [
                (symbol, status, s, m, z),  # e.g. ('Fe-56', 'identified', 'Fe', 56, 10)
                ...
            ]
        },
        ...
    ]

Output format (from analyze_consensus):
    {
        (s, m, z): {
            'symbol': str,            # e.g. 'Fe-56'
            'accepted': [str, ...],   # operator names who marked 'identified'
            'maybe':    [str, ...],   # operator names who marked 'maybe'
            'absent':   [str, ...],   # operators present but who did NOT identify this isotope
            'consensus': str,         # 'FULL', 'MAJORITY', 'SPLIT', or 'UNIQUE'
        },
        ...
    }

Consensus level definitions:
    FULL     — All operators who were present agree on the same primary status
               (all 'identified', or all 'maybe'). Absent operators do not
               count against consensus — they simply didn't find it.
    MAJORITY — More than 50% of operators who did identify the isotope share
               the same status.
    SPLIT    — No single status holds a majority among those who identified it.
    UNIQUE   — Only one operator identified this isotope at all.
"""

from collections import defaultdict


# Status string constants as stored in the database.
STATUS_IDENTIFIED = "identified"
STATUS_MAYBE = "maybe"

# Consensus level labels.
CONSENSUS_FULL = "FULL"
CONSENSUS_MAJORITY = "MAJORITY"
CONSENSUS_SPLIT = "SPLIT"
CONSENSUS_UNIQUE = "UNIQUE"


def _make_isotope_key(s, m, z):
    """
    Build a hashable key for an isotope from its components.

    All three fields come from the database, which stores them as:
        s   TEXT  (element symbol, e.g. 'Fe')
        m   INTEGER (mass number, e.g. 56)
        z   INTEGER (charge state, e.g. 10)

    SQLite may return m and z as int or None; normalise defensively.
    """
    s_norm = str(s).strip() if s is not None else ""
    m_norm = int(m) if m is not None else None
    z_norm = int(z) if z is not None else None
    return (s_norm, m_norm, z_norm)


def _derive_symbol(s, m):
    """
    Reconstruct a human-readable symbol string from components.

    Prefers the database-stored symbol field when available; falls back to
    constructing 'S-M' from s and m.  The symbol column in the DB may carry
    the full string (e.g. 'Fe-56') or may be None/empty.
    """
    s_str = str(s).strip() if s else ""
    m_str = str(int(m)) if m is not None else "?"
    if s_str:
        return f"{s_str}-{m_str}"
    return f"?-{m_str}"


def _compute_consensus(accepted, maybe):
    """
    Derive a consensus label from the lists of accepting and maybe operators.

    Parameters
    ----------
    accepted : list[str]
        Operators who marked this isotope as 'identified'.
    maybe : list[str]
        Operators who marked this isotope as 'maybe'.

    Returns
    -------
    str
        One of CONSENSUS_FULL, CONSENSUS_MAJORITY, CONSENSUS_SPLIT,
        CONSENSUS_UNIQUE.
    """
    total = len(accepted) + len(maybe)

    if total == 0:
        # Defensive case: should not happen (absent-only isotopes are not created).
        return CONSENSUS_UNIQUE

    if total == 1:
        return CONSENSUS_UNIQUE

    # Both groups empty is handled above. Check if a single status dominates.
    # "All agree" means every operator who found it chose the same status.
    if len(maybe) == 0:
        # All finders said 'identified'.
        return CONSENSUS_FULL
    if len(accepted) == 0:
        # All finders said 'maybe'.
        return CONSENSUS_FULL

    # Mixed: check for majority (strictly > 50%).
    if len(accepted) > total / 2 or len(maybe) > total / 2:
        return CONSENSUS_MAJORITY

    # Exactly 50/50 — no majority.
    return CONSENSUS_SPLIT


def analyze_consensus(evaluations):
    """
    Compute cross-operator consensus for every isotope found in any evaluation.

    Parameters
    ----------
    evaluations : list[dict]
        Each dict has keys:
            'operator' : str          — operator username
            'isotopes' : list[tuple]  — (symbol, status, s, m, z) tuples
                                        as returned by get_all_evaluations_for_csd.

    Returns
    -------
    dict
        Keyed by (s, m, z) tuples (strings/ints/None as stored in the DB).
        Each value is a dict with:
            'symbol'    : str         — human-readable label, e.g. 'Fe-56'
            'accepted'  : list[str]   — operators who said 'identified'
            'maybe'     : list[str]   — operators who said 'maybe'
            'absent'    : list[str]   — operators present but who did not
                                        identify this isotope at all
            'consensus' : str         — FULL / MAJORITY / SPLIT / UNIQUE

    Notes
    -----
    - Isotope rows where s, m, and z are all None are skipped; they represent
      legacy data saved before the coordinate columns were added and cannot be
      meaningfully grouped.
    - Operators with zero isotopes in their evaluation are still counted as
      "present" and will appear in the 'absent' list for every isotope found
      by other operators.
    - Status comparison is case-insensitive to tolerate minor DB inconsistencies.
    """
    if not evaluations:
        return {}

    # Collect all operator names in evaluation order (preserves insertion order
    # in Python 3.7+, which gives a stable, predictable display order).
    all_operators = []
    seen_operators = set()
    for ev in evaluations:
        op = ev.get("operator", "")
        if op and op not in seen_operators:
            all_operators.append(op)
            seen_operators.add(op)

    # Build a mapping: isotope_key -> {operator: status}
    # status is 'identified', 'maybe', or absent (key not present).
    isotope_operator_status = defaultdict(dict)   # key -> {op: status}
    isotope_symbol_cache    = {}                  # key -> human symbol string

    for ev in evaluations:
        op = ev.get("operator", "")
        if not op:
            continue
        for row in ev.get("isotopes", []):
            # Unpack safely — the tuple is (symbol, status, s, m, z).
            if len(row) < 5:
                continue
            db_symbol, status, s, m, z = row[0], row[1], row[2], row[3], row[4]

            # Skip rows with no usable coordinate data.
            if s is None and m is None and z is None:
                continue

            key = _make_isotope_key(s, m, z)

            # Cache the display symbol from the first time we see this key.
            if key not in isotope_symbol_cache:
                # Prefer the database symbol column if it is a populated string;
                # otherwise build it from components.
                if db_symbol and str(db_symbol).strip():
                    isotope_symbol_cache[key] = str(db_symbol).strip()
                else:
                    isotope_symbol_cache[key] = _derive_symbol(s, m)

            # Normalise status to lowercase for robust comparison.
            status_norm = str(status).strip().lower() if status else ""
            isotope_operator_status[key][op] = status_norm

    # Build the result dict.
    result = {}

    for key, op_status_map in isotope_operator_status.items():
        accepted = sorted(
            op for op, st in op_status_map.items() if st == STATUS_IDENTIFIED
        )
        maybe = sorted(
            op for op, st in op_status_map.items() if st == STATUS_MAYBE
        )
        # Operators present in the evaluation set but not in this isotope's map.
        absent = sorted(
            op for op in all_operators if op not in op_status_map
        )

        consensus = _compute_consensus(accepted, maybe)

        result[key] = {
            "symbol":    isotope_symbol_cache[key],
            "accepted":  accepted,
            "maybe":     maybe,
            "absent":    absent,
            "consensus": consensus,
        }

    return result
