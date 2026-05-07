"""Triangulation math against synthetic stereo geometry."""

from __future__ import annotations

import numpy as np

from cotracker_lips.calibration.stereo import CameraCalibration, StereoCalibration
from cotracker_lips.calibration.triangulate import triangulate_points


def _identity_camera(focal: float = 1000.0, principal: tuple[float, float] = (320.0, 240.0)) -> CameraCalibration:
    fx, fy = focal, focal
    cx, cy = principal
    K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float64)
    return CameraCalibration(matrix=K, distortion=np.zeros(5), rmse=0.0)


def test_triangulate_recovers_known_3d_point():
    """Project a point through two known cameras and recover it via DLT."""
    left = _identity_camera()
    right = _identity_camera()
    R = np.eye(3)
    T = np.array([[100.0], [0.0], [0.0]])  # 100mm translation along X
    calib = StereoCalibration(left=left, right=right, R=R, T=T)

    world_pt = np.array([10.0, 5.0, 1500.0])

    # Project to each camera. For the right camera, world coords are R·p + T.
    def project(K, R_, T_, p):
        cam = R_ @ p + T_.flatten()
        return np.array([
            K[0, 0] * cam[0] / cam[2] + K[0, 2],
            K[1, 1] * cam[1] / cam[2] + K[1, 2],
        ])

    uv1 = project(left.matrix, np.eye(3), np.zeros(3), world_pt).reshape(1, 2)
    uv2 = project(right.matrix, R, T, world_pt).reshape(1, 2)

    recovered = triangulate_points(calib, uv1, uv2)
    assert recovered.shape == (1, 3)
    assert np.allclose(recovered[0], world_pt, atol=1e-3)
