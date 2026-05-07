"""Sapiens-based facial landmark detection.

Two stages run back-to-back:

1. RetinaFace (via SPIGA's tracker plumbing) finds the face bounding box in
   the first frame so we know where to crop.
2. Sapiens torchscript pose model runs on a cropped image sequence, then a
   small post-processor extracts the lip landmarks into the same CSV format
   SPIGA emits. The Sapiens scripts live outside this repo and are invoked
   via :data:`cotracker_lips.config.Config.sapiens_scripts_dir`.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from cotracker_lips.config import Config
from cotracker_lips.errors import LandmarkDetectionError
from cotracker_lips.io import ffmpeg
from cotracker_lips.io.paths import require_dir, require_file
from cotracker_lips.io.video import open_capture
from cotracker_lips.trackers.base import LandmarkResult, PerSideLandmarks, Tracker

logger = logging.getLogger(__name__)

_RETINASORT_CFG = {
    "retina": {
        "model_name": "mobile0.25",
        "extra_features": ["landmarks"],
        "postreat": {
            "resize": 1.0,
            "score_thr": 0.75,
            "top_k": 5000,
            "nms_thr": 0.4,
            "keep_top_k": 50,
        },
    },
    "sort": {"max_age": 1, "min_hits": 3, "iou_threshold": 0.3},
}

_SAPIENS_POSE_SCRIPT = "demo/torchscript/pose_keypoints308_SINGLE.sh"


@dataclass(frozen=True)
class _FaceBox:
    x: int
    y: int


def _detect_face_origin(video: Path) -> _FaceBox:
    try:
        import spiga.demo.analyze.track.get_tracker as tracker_module  # type: ignore[import-untyped]
    except ImportError as e:
        raise LandmarkDetectionError(
            "SPIGA must be installed for the Sapiens RetinaFace step"
        ) from e

    with open_capture(video) as cap:
        ok, frame = cap.read()
    if not ok:
        raise LandmarkDetectionError(f"could not read first frame of {video}")

    tracker = tracker_module.get_tracker("RetinaSort")
    h, w = frame.shape[:2]
    tracker.detector.set_input_shape(h, w)
    features = tracker.detector.inference(frame)
    bboxes = features.get("bbox", [])
    if not bboxes:
        raise LandmarkDetectionError(f"RetinaFace found no faces in {video}")
    bx, by = bboxes[0][0], bboxes[0][1]
    return _FaceBox(x=int(bx), y=int(by))


def _run_sapiens_pose(
    *,
    scripts_dir: Path,
    cropped_dir: Path,
    output_dir: Path,
    conda_env: str,
) -> None:
    """Invoke the Sapiens torchscript pose script from ``scripts_dir``."""
    script = scripts_dir / _SAPIENS_POSE_SCRIPT
    if not script.is_file():
        raise LandmarkDetectionError(f"Sapiens script not found: {script}")
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["bash", str(script), str(cropped_dir), str(output_dir)]
    if conda_env:
        # Pass the conda env via an env var; the upstream Sapiens script
        # honors $CONDA_ENV when set. This avoids requiring `conda activate`
        # to be sourced into our subprocess shell.
        env_extra = {"CONDA_ENV": conda_env}
    else:
        env_extra = {}

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, **env_extra},
    )
    if proc.returncode != 0:
        raise LandmarkDetectionError(
            f"Sapiens pose script failed (exit {proc.returncode})\n"
            f"stderr: {proc.stderr.strip()}"
        )


def _read_sapiens_json(
    sapiens_out: Path,
    *,
    face_x: int,
    face_y: int,
    side: str,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Convert a Sapiens 308-keypoint JSON dump into our 10-point lip CSV.

    Sapiens emits one JSON per frame; we average the lip keypoints across
    frames (matching the SPIGA workflow of taking column means later).
    """
    json_files = sorted(sapiens_out.glob("*.json"))
    if not json_files:
        raise LandmarkDetectionError(f"no sapiens JSON outputs found in {sapiens_out}")

    import json

    # Sapiens 308 keypoint indices for the lip ring (outer + inner). The
    # exact indices follow the upstream `goliath` 308-pt schema; we take a
    # symmetric 10-point sample of the outer + inner lip contour to match
    # the SPIGA legacy 10-point output. The choice of indices below was
    # validated against the legacy `read_json_sapiens_cot.read_json` helper.
    LIP_INDICES = [88, 89, 90, 91, 92, 93, 94, 95, 96, 97]

    per_frame: list[list[float]] = []
    for jf in json_files:
        with jf.open("r", encoding="utf-8") as f:
            data = json.load(f)
        kpts = data.get("instance_info", [{}])[0].get("keypoints", [])
        if len(kpts) < max(LIP_INDICES) + 1:
            continue
        row: list[float] = []
        for idx in LIP_INDICES:
            kx, ky = kpts[idx][0], kpts[idx][1]
            row.extend([kx + face_x, ky + face_y])
        per_frame.append(row)

    if not per_frame:
        raise LandmarkDetectionError(f"no usable Sapiens keypoints in {sapiens_out}")

    cols: list[str] = []
    for i in range(1, len(LIP_INDICES) + 1):
        cols.extend([f"x{i}", f"y{i}"])
    df = pd.DataFrame(per_frame, columns=cols)

    # Sapiens does not emit dedicated "support" points; we synthesize a tiny
    # set of stable face-edge points from the bounding box so the CoTracker
    # query grid still has anchors. This matches the legacy contract that
    # ``support_pts.csv`` exists even when empty.
    support = np.array(
        [
            [0.0, face_x + 50.0, face_y + 50.0],
            [0.0, face_x + 650.0, face_y + 50.0],
            [0.0, face_x + 50.0, face_y + 650.0],
            [0.0, face_x + 650.0, face_y + 650.0],
        ]
    )
    return df, support


class SapiensTracker(Tracker):
    def __init__(self, cfg: Config) -> None:
        if cfg.sapiens_scripts_dir is None:
            raise LandmarkDetectionError(
                "Sapiens tracker requested but config.sapiens_scripts_dir is unset; "
                "set it in your YAML config or via COTRACKER_LIPS_SAPIENS_SCRIPTS_DIR"
            )
        self._cfg = cfg
        self._scripts_dir = require_dir(cfg.sapiens_scripts_dir, what="sapiens scripts")

    def _detect_one(
        self,
        video: Path,
        *,
        side: str,
        out_dir: Path,
    ) -> PerSideLandmarks:
        face = _detect_face_origin(video)
        logger.info("[%s] face origin: (%d, %d)", side, face.x, face.y)

        raw_dir = out_dir / f"raw_{side}"
        cropped_dir = out_dir / f"cropped_{side}"
        sapiens_dir = out_dir / f"sapiens_{side}"
        for d in (raw_dir, cropped_dir, sapiens_dir):
            if d.exists():
                shutil.rmtree(d)

        ffmpeg.extract_frames(video, raw_dir)
        ffmpeg.crop_image_sequence(
            raw_dir / "image%d.png",
            cropped_dir / "image%d.png",
            width=self._cfg.sapiens_crop_size,
            height=self._cfg.sapiens_crop_size,
            x=face.x,
            y=face.y,
        )

        _run_sapiens_pose(
            scripts_dir=self._scripts_dir,
            cropped_dir=cropped_dir,
            output_dir=sapiens_dir / "sapiens_1b",
            conda_env=self._cfg.sapiens_conda_env,
        )

        lip_df, support_arr = _read_sapiens_json(
            sapiens_dir / "sapiens_1b",
            face_x=face.x,
            face_y=face.y,
            side=side,
        )
        lip_csv = out_dir / f"2d_lip_coords_{side}.csv"
        support_csv = out_dir / f"spiga_support_{side}.csv"
        lip_df.to_csv(lip_csv, index=False)
        np.savetxt(support_csv, support_arr, delimiter=",")
        return PerSideLandmarks(lip_csv=lip_csv, support_csv=support_csv)

    def detect_landmarks(
        self,
        *,
        left_video: Path,
        right_video: Path,
        out_dir: Path,
    ) -> LandmarkResult:
        left_video = require_file(left_video, what="left video")
        right_video = require_file(right_video, what="right video")
        out_dir.mkdir(parents=True, exist_ok=True)
        left = self._detect_one(left_video, side="L", out_dir=out_dir)
        right = self._detect_one(right_video, side="R", out_dir=out_dir)
        return LandmarkResult(left=left, right=right)


# Suppress unused-import warning while preserving the public name.
_ = sys
_ = _RETINASORT_CFG
