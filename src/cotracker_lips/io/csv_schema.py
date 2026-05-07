"""Column schemas for the CSV files exchanged between pipeline stages.

Centralizing the column names removes the implicit coupling that previously
existed between ``5pt_average.py`` and ``calibration.py`` (where typos would
silently propagate through ``KeyError``).
"""

from __future__ import annotations

from typing import Final

# Number of lip points (5 lower + 5 upper) tracked per frame per camera.
NUM_LIP_PAIRS: Final = 5

# Total landmarks emitted by the upstream landmark detectors. Indices 1..8 are
# stable lip corners; 9 = upper-mid; 10 = lower-mid.
LANDMARKS_PER_FRAME: Final = 10


def cropped_landmark_columns() -> list[str]:
    """Header for ``first_5_avg.csv`` (``x{i}_mean_incrop`` / ``y{i}_mean_incrop``)."""
    cols: list[str] = []
    for i in range(1, LANDMARKS_PER_FRAME + 1):
        cols.append(f"x{i}_mean_incrop")
        cols.append(f"y{i}_mean_incrop")
    return cols


def triangulation_columns() -> list[str]:
    """Header for ``cotracker_pts.csv`` consumed by triangulation."""
    cols: list[str] = []
    for i in range(1, NUM_LIP_PAIRS + 1):
        suffix = "" if i == 1 else str(i)
        for cam in (1, 2):
            cols.append(f"f{cam}_lower_x{suffix}")
            cols.append(f"f{cam}_lower_y{suffix}")
            cols.append(f"f{cam}_upper_x{suffix}")
            cols.append(f"f{cam}_upper_y{suffix}")
    return cols
