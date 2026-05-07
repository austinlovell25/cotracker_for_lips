"""Lip-region cropping and offset bookkeeping.

The legacy pipeline ran landmark detection on the full-resolution video, then
cropped a 704×512 window centered roughly on the lips before feeding it to
CoTracker (CoTracker is much faster on a small ROI). This module owns:

1. :func:`compute_crop_offsets` — given the per-camera lip landmark CSVs that
   SPIGA / Sapiens emit, decide where to anchor the crop window.
2. :func:`build_lip_queries` — turn those landmarks into the 10-row
   ``(x{i}, y{i})_mean_incrop`` table that CoTracker's grid loader consumes.
3. :func:`apply_crop_offsets` to support points and :func:`revert_crop` to
   convert tracked points back into full-frame coordinates.

Behavior matches the legacy ``5pt_average.py`` modes ``reduce`` / ``revert``
(``rerun`` / ``rerun_revert`` collapse into the same code paths).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from cotracker_lips.errors import CotrackerLipsError
from cotracker_lips.io.csv_schema import LANDMARKS_PER_FRAME, NUM_LIP_PAIRS

logger = logging.getLogger(__name__)

# Hardcoded in the legacy pipeline (5pt_average.py:14-15) and not exposed.
# The crop is anchored such that landmark x1 sits at column ``CROP_LEFT`` and
# y1 sits at row ``CROP_UP`` inside the cropped frame.
CROP_LEFT_INSET = 300
CROP_UP_INSET = 270


@dataclass(frozen=True)
class CropOffsets:
    """Pixel offsets used to translate full-frame coordinates into the crop."""

    left_x: float
    left_y: float
    right_x: float
    right_y: float

    def as_ints(self) -> tuple[int, int, int, int]:
        return (int(self.left_x), int(self.left_y), int(self.right_x), int(self.right_y))


@dataclass(frozen=True)
class LandmarkSet:
    """The 10 landmark points produced for a single video by SPIGA / Sapiens.

    ``df`` has columns ``x1..x10`` and ``y1..y10`` and one row per detection
    sample. The pipeline averages across rows for crop offset calculation.
    """

    df: pd.DataFrame

    def column_mean(self, kind: str, idx: int) -> float:
        return float(self.df[f"{kind}{idx}"].mean())


@dataclass(frozen=True)
class LipQueries:
    """In-crop lip query points and the offsets needed to revert them."""

    queries: pd.DataFrame  # columns from cotracker_lips.io.csv_schema.cropped_landmark_columns
    offsets: CropOffsets


def _read_landmark_csv(path: Path) -> LandmarkSet:
    df = pd.read_csv(path, header=0)
    expected = {f"x{i}" for i in range(1, LANDMARKS_PER_FRAME + 1)}
    if not expected.issubset(df.columns):
        missing = expected - set(df.columns)
        raise CotrackerLipsError(
            f"landmark CSV {path} missing columns: {sorted(missing)}"
        )
    return LandmarkSet(df=df)


def compute_crop_offsets(
    *,
    left_landmarks: Path,
    right_landmarks: Path,
) -> CropOffsets:
    """Anchor each crop so landmark 1 lands at (CROP_LEFT, CROP_UP) inside it."""
    left = _read_landmark_csv(left_landmarks)
    right = _read_landmark_csv(right_landmarks)
    return CropOffsets(
        left_x=left.column_mean("x", 1) - CROP_LEFT_INSET,
        left_y=left.column_mean("y", 1) - CROP_UP_INSET,
        right_x=right.column_mean("x", 1) - CROP_LEFT_INSET,
        right_y=right.column_mean("y", 1) - CROP_UP_INSET,
    )


def build_lip_queries(
    *,
    left_landmarks: Path,
    right_landmarks: Path,
    offsets: CropOffsets,
) -> pd.DataFrame:
    """Produce the per-camera in-crop landmark table consumed by CoTracker.

    Returns a DataFrame with rows ``[left, right]`` and 20 columns
    (``x{i}_mean_incrop``, ``y{i}_mean_incrop`` for ``i`` in 1..10).
    """
    left = _read_landmark_csv(left_landmarks)
    right = _read_landmark_csv(right_landmarks)

    rows: list[dict[str, float]] = [{}, {}]
    for i in range(1, LANDMARKS_PER_FRAME + 1):
        rows[0][f"x{i}_mean_incrop"] = left.column_mean("x", i) - offsets.left_x
        rows[0][f"y{i}_mean_incrop"] = left.column_mean("y", i) - offsets.left_y
        rows[1][f"x{i}_mean_incrop"] = right.column_mean("x", i) - offsets.right_x
        rows[1][f"y{i}_mean_incrop"] = right.column_mean("y", i) - offsets.right_y
    return pd.DataFrame(rows)


def apply_crop_offsets(
    csv_path: Path,
    *,
    offsets_xy: tuple[float, float],
) -> NDArray[np.float64]:
    """Translate a SPIGA support-points CSV into in-crop coordinates.

    The legacy CSV format is ``[0., x, y]`` per row (the leading zero is a
    placeholder for the CoTracker query timestamp).
    """
    rows: list[list[float]] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = pd.read_csv(f, header=None).values
    for row in reader:
        rows.append([0.0, float(row[1]) - offsets_xy[0], float(row[2]) - offsets_xy[1]])
    return np.asarray(rows)


def _stack_points(points_per_landmark: Sequence[NDArray[np.float64]]) -> NDArray[np.float64]:
    """Stack 2-row [x;y] arrays into a single (n_landmarks, 2, frames) tensor."""
    return np.stack(points_per_landmark, axis=0)


def _read_per_frame_points(csv_path: Path) -> NDArray[np.float64]:
    """Read the CoTracker upper/lower CSV (rows = [x_landmark1, y_landmark1, ...])."""
    return np.genfromtxt(csv_path, delimiter=",")


def revert_crop(
    *,
    upper_left_csv: Path,
    lower_left_csv: Path,
    upper_right_csv: Path,
    lower_right_csv: Path,
    offsets: CropOffsets,
    out_csv: Path,
) -> Path:
    """Translate per-frame tracked points back into full-frame coordinates.

    Inputs are the four CoTracker-produced CSVs (``upper_pts.csv`` and
    ``lower_pts.csv`` for each video). Each has 2 × N rows where N is the
    number of lip pairs tracked, alternating ``x_i`` and ``y_i``. We add the
    crop offset back to every row so downstream triangulation works in the
    full-frame coordinate system.
    """
    arrs = {
        "f1_lower": _read_per_frame_points(lower_left_csv),
        "f1_upper": _read_per_frame_points(upper_left_csv),
        "f2_lower": _read_per_frame_points(lower_right_csv),
        "f2_upper": _read_per_frame_points(upper_right_csv),
    }
    end_frame = arrs["f1_upper"].shape[1]

    cam_offsets = {
        "f1": (offsets.left_x, offsets.left_y),
        "f2": (offsets.right_x, offsets.right_y),
    }

    out: dict[str, NDArray[np.float64]] = {}
    for key, mat in arrs.items():
        cam = key.split("_")[0]
        ox, oy = cam_offsets[cam]
        for i in range(NUM_LIP_PAIRS):
            suffix = "" if i == 0 else str(i + 1)
            out[f"{key}_x{suffix}"] = mat[2 * i, :end_frame] + ox
            out[f"{key}_y{suffix}"] = mat[2 * i + 1, :end_frame] + oy

    df = pd.DataFrame(out)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    logger.info("wrote %d frames of triangulation input to %s", end_frame, out_csv)
    return out_csv
