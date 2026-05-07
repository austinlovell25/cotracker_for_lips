"""Stereo triangulation of 2D lip points to 3D.

Replaces the 7-mode ``calibration.py triangulate {tracker} {exp_name} ...``
dispatcher with a single, parameterized function. The tracker name only
affects the output directory, never the math.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy import linalg

from cotracker_lips.calibration.stereo import StereoCalibration, load_calibration
from cotracker_lips.errors import CalibrationError
from cotracker_lips.io.csv_schema import NUM_LIP_PAIRS

logger = logging.getLogger(__name__)

# Maximum frames to triangulate per call. The legacy code hardcoded 600 to
# guard against tracker drift on long clips; we preserve that as a soft cap.
_MAX_FRAMES = 600

TrackerName = Literal["spiga", "cotracker", "sapiens_cotracker"]
_OUTPUT_SUBDIR: dict[TrackerName, str] = {
    "spiga": "spiga_out",
    "cotracker": "cotracker_out",
    "sapiens_cotracker": "sapiens_cotracker",
}


@dataclass(frozen=True)
class TriangulationResult:
    upper_3d: NDArray[np.float64]
    lower_3d: NDArray[np.float64]
    distances_mm: NDArray[np.float64]
    output_dir: Path


def _projection_matrices(
    calib: StereoCalibration,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    rt1 = np.concatenate([np.eye(3), np.zeros((3, 1))], axis=-1)
    rt2 = np.concatenate([calib.R, calib.T], axis=-1)
    return calib.left.matrix @ rt1, calib.right.matrix @ rt2


def _dlt(
    p1: NDArray[np.float64],
    p2: NDArray[np.float64],
    pt1: NDArray[np.float64],
    pt2: NDArray[np.float64],
) -> NDArray[np.float64]:
    A = np.array(
        [
            pt1[1] * p1[2, :] - p1[1, :],
            p1[0, :] - pt1[0] * p1[2, :],
            pt2[1] * p2[2, :] - p2[1, :],
            p2[0, :] - pt2[0] * p2[2, :],
        ]
    )
    _, _, Vh = linalg.svd(A.T @ A, full_matrices=False)
    return Vh[3, 0:3] / Vh[3, 3]


def triangulate_points(
    calib: StereoCalibration,
    uvs1: NDArray[np.float64],
    uvs2: NDArray[np.float64],
) -> NDArray[np.float64]:
    """DLT-triangulate matched 2D point sets from two cameras."""
    if uvs1.shape != uvs2.shape:
        raise CalibrationError(f"uvs1 {uvs1.shape} and uvs2 {uvs2.shape} must match")
    p1, p2 = _projection_matrices(calib)
    return np.array([_dlt(p1, p2, a, b) for a, b in zip(uvs1, uvs2)])


def _flip_y(df: pd.DataFrame, image_height: int) -> pd.DataFrame:
    """Flip the OpenCV-origin y values into a bottom-origin frame."""
    df = df.copy()
    for cam in (1, 2):
        df[f"f{cam}_lower_y"] = image_height - df[f"f{cam}_lower_y"]
        df[f"f{cam}_upper_y"] = image_height - df[f"f{cam}_upper_y"]
    return df


def _euclid(a: NDArray[np.float64], b: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.linalg.norm(a - b, axis=1)


def _save_distance_plot(distances: NDArray[np.float64], path: Path) -> None:
    fig, ax = plt.subplots()
    ax.plot(np.arange(distances.size), distances, linewidth=2.0, c="r", label="3d euc. diff")
    ax.legend(loc="upper right", shadow=True, fontsize="x-large")
    ax.set_xlabel("frames")
    ax.set_ylabel("3d Euclidean distance (mm)")
    ax.set_title("Difference between upper lip and lower lip point estimation")
    fig.savefig(path)
    plt.close(fig)


def _save_stats(distances: NDArray[np.float64], path: Path) -> None:
    pd.DataFrame(
        {
            "stdv": [float(np.std(distances))],
            "min": [float(np.min(distances))],
            "max": [float(np.max(distances))],
            "mean": [float(np.mean(distances))],
            "median": [float(np.median(distances))],
        }
    ).to_csv(path, index=False)


def triangulate_pipeline(
    *,
    points_csv: Path,
    cam_config_dir: Path,
    save_dir: Path,
    experiment_name: str,
    tracker: TrackerName,
    image_height: int,
    max_frames: int = _MAX_FRAMES,
) -> TriangulationResult:
    """Triangulate the primary upper/lower lip points and dump artifacts.

    Reads ``points_csv`` (the merged ``cotracker_pts.csv``), loads the
    calibration from ``cam_config_dir``, and writes upper/lower 3D point
    clouds plus a per-frame distance array, summary stats, and a plot to
    ``save_dir / <tracker_subdir> / <experiment_name>``.
    """
    calib = load_calibration(cam_config_dir)
    df = pd.read_csv(points_csv)
    df = _flip_y(df, image_height)

    n = min(len(df), max_frames)
    uvs1_lower = df[["f1_lower_x", "f1_lower_y"]].to_numpy()[:n]
    uvs2_lower = df[["f2_lower_x", "f2_lower_y"]].to_numpy()[:n]
    uvs1_upper = df[["f1_upper_x", "f1_upper_y"]].to_numpy()[:n]
    uvs2_upper = df[["f2_upper_x", "f2_upper_y"]].to_numpy()[:n]

    lower_3d = triangulate_points(calib, uvs1_lower, uvs2_lower)
    upper_3d = triangulate_points(calib, uvs1_upper, uvs2_upper)
    distances = _euclid(upper_3d, lower_3d)

    out_dir = save_dir / _OUTPUT_SUBDIR[tracker] / experiment_name
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savetxt(out_dir / f"{tracker}_lower_3dpts.txt", lower_3d)
    np.savetxt(out_dir / f"{tracker}_upper_3dpts.txt", upper_3d)
    np.savetxt(out_dir / f"{tracker}_3dist.txt", distances)
    _save_stats(distances, out_dir / f"{tracker}_stats.csv")
    _save_distance_plot(distances, out_dir / f"{tracker}_3d_distance.png")

    logger.info(
        "triangulated %d frames; distance stats: mean=%.3f std=%.3f",
        n,
        float(distances.mean()),
        float(distances.std()),
    )
    return TriangulationResult(
        upper_3d=upper_3d,
        lower_3d=lower_3d,
        distances_mm=distances,
        output_dir=out_dir,
    )


# Public so the GUI refiner can re-triangulate a single combined CSV without
# the experiment-name plumbing. Equivalent to the legacy ``rerun_triangulate``.
def rerun_triangulate(
    *,
    points_csv: Path,
    cam_config_dir: Path,
    save_dir: Path,
    image_height: int,
    max_frames: int = _MAX_FRAMES,
) -> TriangulationResult:
    calib = load_calibration(cam_config_dir)
    df = pd.read_csv(points_csv)
    df = _flip_y(df, image_height)

    n = min(len(df), max_frames)
    uvs1_lower = df[["f1_lower_x", "f1_lower_y"]].to_numpy()[:n]
    uvs2_lower = df[["f2_lower_x", "f2_lower_y"]].to_numpy()[:n]
    uvs1_upper = df[["f1_upper_x", "f1_upper_y"]].to_numpy()[:n]
    uvs2_upper = df[["f2_upper_x", "f2_upper_y"]].to_numpy()[:n]

    lower_3d = triangulate_points(calib, uvs1_lower, uvs2_lower)
    upper_3d = triangulate_points(calib, uvs1_upper, uvs2_upper)
    distances = _euclid(upper_3d, lower_3d)

    save_dir.mkdir(parents=True, exist_ok=True)
    np.savetxt(save_dir / "cotracker_lower_3dpts.txt", lower_3d)
    np.savetxt(save_dir / "cotracker_upper_3dpts.txt", upper_3d)
    np.savetxt(save_dir / "cotracker_3dist.txt", distances)
    _save_stats(distances, save_dir / "cotracker_stats.csv")
    _save_distance_plot(distances, save_dir / "cotracker_3d_distance.png")

    return TriangulationResult(
        upper_3d=upper_3d,
        lower_3d=lower_3d,
        distances_mm=distances,
        output_dir=save_dir,
    )


# Suppress unused-import warnings while keeping the constant available to
# downstream code that wants to know how many lip-pair columns to write.
_ = NUM_LIP_PAIRS
