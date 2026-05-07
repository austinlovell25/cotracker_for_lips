"""Stereo camera calibration and triangulation.

Three top-level operations:

* :func:`extract_checkerboard_frames` — sample N random frames from each video
  and write them into the OpenCV-friendly ``D2/`` (left), ``J2/`` (right), and
  ``synced/`` (combined) subdirectories.
* :func:`run_calibration` — solve intrinsics for each camera, then stereo
  extrinsics; write ``camera{1,2}.yml``, ``stereo_coeffs.yml``, ``rmse.json``.
* :func:`triangulate_pipeline` — load 2D lip points + saved calibration and
  emit 3D point clouds plus upper/lower distance statistics.
"""

from cotracker_lips.calibration.checkerboard import extract_checkerboard_frames
from cotracker_lips.calibration.stereo import (
    StereoCalibration,
    load_calibration,
    run_calibration,
)
from cotracker_lips.calibration.triangulate import (
    TriangulationResult,
    triangulate_pipeline,
)

__all__ = [
    "StereoCalibration",
    "TriangulationResult",
    "extract_checkerboard_frames",
    "load_calibration",
    "run_calibration",
    "triangulate_pipeline",
]
