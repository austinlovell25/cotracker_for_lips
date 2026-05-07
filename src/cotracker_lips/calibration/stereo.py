"""Single-camera intrinsics and stereo-pair extrinsics.

The math here is unchanged from OpenCV's standard recipe (Zhang 2000); the
refactor consolidates duplicated intrinsics-calibration code that previously
ran twice inline and replaces module-level hardcoded paths with a typed
result object.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from cotracker_lips.errors import CalibrationError

logger = logging.getLogger(__name__)

_CORNER_REFINE_WINDOW = (11, 11)
_INTRINSIC_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)
_STEREO_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-4)


@dataclass(frozen=True)
class CameraCalibration:
    matrix: NDArray[np.float64]
    distortion: NDArray[np.float64]
    rmse: float


@dataclass(frozen=True)
class StereoCalibration:
    left: CameraCalibration
    right: CameraCalibration
    R: NDArray[np.float64]
    T: NDArray[np.float64]


def _build_object_points(rows: int, cols: int, world_scaling: float) -> NDArray[np.float32]:
    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:rows, 0:cols].T.reshape(-1, 2)
    return world_scaling * objp


def _detect_corners(image_paths: list[Path], rows: int, cols: int) -> tuple[
    list[NDArray[np.float32]], int, int
]:
    """Return per-image corner arrays plus the (width, height) of the first frame."""
    if not image_paths:
        raise CalibrationError("no calibration images found")

    width = height = 0
    corners_per_image: list[NDArray[np.float32]] = []
    for p in image_paths:
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is None:
            logger.warning("could not read calibration image %s", p)
            continue
        if width == 0:
            height, width = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ok, corners = cv2.findChessboardCorners(gray, (rows, cols), None)
        if not ok:
            continue
        corners = cv2.cornerSubPix(gray, corners, _CORNER_REFINE_WINDOW, (-1, -1),
                                   _INTRINSIC_CRITERIA)
        corners_per_image.append(corners)

    if not corners_per_image:
        raise CalibrationError(
            f"no images contained a detectable {rows}x{cols} checkerboard"
        )
    return corners_per_image, width, height


def calibrate_camera(
    images_dir: Path,
    *,
    rows: int,
    cols: int,
    world_scaling: float,
) -> CameraCalibration:
    """Solve intrinsics from a directory of single-camera checkerboard images."""
    image_paths = sorted(p for p in images_dir.iterdir() if p.is_file())
    corners, width, height = _detect_corners(image_paths, rows, cols)

    objp = _build_object_points(rows, cols, world_scaling)
    object_points = [objp for _ in corners]
    rmse, mtx, dist, _rvecs, _tvecs = cv2.calibrateCamera(
        object_points, corners, (width, height), None, None
    )
    logger.info("intrinsic RMSE for %s = %.4f", images_dir.name, rmse)
    return CameraCalibration(matrix=mtx, distortion=dist, rmse=float(rmse))


def stereo_calibrate(
    *,
    left: CameraCalibration,
    right: CameraCalibration,
    synced_dir: Path,
    rows: int,
    cols: int,
    world_scaling: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Solve the rotation + translation between two pre-calibrated cameras."""
    image_paths = sorted(p for p in synced_dir.iterdir() if p.is_file())
    if len(image_paths) % 2 != 0:
        raise CalibrationError(
            f"synced/ must contain pairs of images; found {len(image_paths)}"
        )

    half = len(image_paths) // 2
    left_paths, right_paths = image_paths[:half], image_paths[half:]

    objp = _build_object_points(rows, cols, world_scaling)
    object_points: list[NDArray[np.float32]] = []
    left_pts: list[NDArray[np.float32]] = []
    right_pts: list[NDArray[np.float32]] = []
    width = height = 0

    for lp, rp in zip(left_paths, right_paths):
        l_img = cv2.imread(str(lp), cv2.IMREAD_COLOR)
        r_img = cv2.imread(str(rp), cv2.IMREAD_COLOR)
        if l_img is None or r_img is None:
            continue
        if width == 0:
            height, width = l_img.shape[:2]
        l_gray = cv2.cvtColor(l_img, cv2.COLOR_BGR2GRAY)
        r_gray = cv2.cvtColor(r_img, cv2.COLOR_BGR2GRAY)
        ok_l, corners_l = cv2.findChessboardCorners(l_gray, (rows, cols), None)
        ok_r, corners_r = cv2.findChessboardCorners(r_gray, (rows, cols), None)
        if not (ok_l and ok_r):
            continue
        corners_l = cv2.cornerSubPix(l_gray, corners_l, _CORNER_REFINE_WINDOW, (-1, -1),
                                     _STEREO_CRITERIA)
        corners_r = cv2.cornerSubPix(r_gray, corners_r, _CORNER_REFINE_WINDOW, (-1, -1),
                                     _STEREO_CRITERIA)
        object_points.append(objp)
        left_pts.append(corners_l)
        right_pts.append(corners_r)

    if not object_points:
        raise CalibrationError("no synced image pairs yielded matched corners")

    rmse, _, _, _, _, R, T, _, _ = cv2.stereoCalibrate(
        object_points,
        left_pts,
        right_pts,
        left.matrix,
        left.distortion,
        right.matrix,
        right.distortion,
        (width, height),
        criteria=_STEREO_CRITERIA,
        flags=cv2.CALIB_FIX_INTRINSIC,
    )
    logger.info("stereo RMSE = %.4f", rmse)
    return R, T


def _save_camera_yml(cam: CameraCalibration, path: Path) -> None:
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    fs.write("K", cam.matrix)
    fs.write("D", cam.distortion)
    fs.release()


def _save_stereo_yml(R: NDArray[np.float64], T: NDArray[np.float64], path: Path) -> None:
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    fs.write("R", R)
    fs.write("T", T)
    fs.release()


def _load_camera_yml(path: Path) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    try:
        return fs.getNode("K").mat(), fs.getNode("D").mat()
    finally:
        fs.release()


def _load_stereo_yml(path: Path) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    try:
        return fs.getNode("R").mat(), fs.getNode("T").mat()
    finally:
        fs.release()


def run_calibration(
    *,
    cam_config_dir: Path,
    rows: int,
    cols: int,
    world_scaling: float,
) -> StereoCalibration:
    """Calibrate both cameras and the stereo pair, persist results to disk.

    ``cam_config_dir`` must contain ``D2/``, ``J2/``, and ``synced/``
    subdirectories produced by :func:`extract_checkerboard_frames`. Outputs
    written: ``camera1.yml``, ``camera2.yml``, ``stereo_coeffs.yml``,
    ``rmse.json``.
    """
    cam_config_dir = cam_config_dir.expanduser().resolve()
    left_dir = cam_config_dir / "D2"
    right_dir = cam_config_dir / "J2"
    synced_dir = cam_config_dir / "synced"
    for d in (left_dir, right_dir, synced_dir):
        if not d.is_dir():
            raise CalibrationError(f"missing calibration directory: {d}")

    left = calibrate_camera(left_dir, rows=rows, cols=cols, world_scaling=world_scaling)
    right = calibrate_camera(right_dir, rows=rows, cols=cols, world_scaling=world_scaling)
    R, T = stereo_calibrate(
        left=left,
        right=right,
        synced_dir=synced_dir,
        rows=rows,
        cols=cols,
        world_scaling=world_scaling,
    )

    _save_camera_yml(left, cam_config_dir / "camera1.yml")
    _save_camera_yml(right, cam_config_dir / "camera2.yml")
    _save_stereo_yml(R, T, cam_config_dir / "stereo_coeffs.yml")
    with (cam_config_dir / "rmse.json").open("w", encoding="utf-8") as f:
        json.dump({"camera1_rmse": left.rmse, "camera2_rmse": right.rmse}, f, indent=2)

    return StereoCalibration(left=left, right=right, R=R, T=T)


def load_calibration(cam_config_dir: Path) -> StereoCalibration:
    """Reload a previously saved stereo calibration from disk."""
    cam_config_dir = cam_config_dir.expanduser().resolve()
    rmse_path = cam_config_dir / "rmse.json"
    rmses: dict[str, float] = {}
    if rmse_path.exists():
        with rmse_path.open("r", encoding="utf-8") as f:
            rmses = json.load(f)

    k1, d1 = _load_camera_yml(cam_config_dir / "camera1.yml")
    k2, d2 = _load_camera_yml(cam_config_dir / "camera2.yml")
    R, T = _load_stereo_yml(cam_config_dir / "stereo_coeffs.yml")
    return StereoCalibration(
        left=CameraCalibration(k1, d1, float(rmses.get("camera1_rmse", float("nan")))),
        right=CameraCalibration(k2, d2, float(rmses.get("camera2_rmse", float("nan")))),
        R=R,
        T=T,
    )
