"""End-to-end pipeline that replaces the three shell scripts.

Given a stereo pair of cropped sample videos, this drives:

1. Landmark detection on each side (SPIGA or Sapiens).
2. Crop offset computation + per-camera ROI crop.
3. CoTracker tracking of the cropped videos.
4. Crop reversion → triangulation-ready CSV.
5. Stereo triangulation + statistics.

Each stage logs progress and isolates its intermediate files under
``cfg.work_dir / "tmp"`` so reruns are safe.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2

from cotracker_lips.calibration.triangulate import (
    TriangulationResult,
    triangulate_pipeline,
)
from cotracker_lips.config import Config
from cotracker_lips.io import ffmpeg
from cotracker_lips.io.paths import require_dir, require_file
from cotracker_lips.io.video import probe
from cotracker_lips.postprocess.crop import (
    apply_crop_offsets,
    build_lip_queries,
    compute_crop_offsets,
    revert_crop,
)
from cotracker_lips.trackers.base import LandmarkResult, TrackerKind, create_tracker
from cotracker_lips.trackers.cotracker_runner import CoTrackerRunner, load_grid_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SampleSpec:
    """One stereo pair to process."""

    name: str
    left_video: Path
    right_video: Path


@dataclass(frozen=True)
class PipelineResult:
    sample: SampleSpec
    triangulation: TriangulationResult


class Pipeline:
    """Orchestrates a single end-to-end run."""

    def __init__(
        self,
        cfg: Config,
        *,
        tracker_kind: TrackerKind,
        cam_config_dir: Path,
        save_dir: Path,
        grid_config_name: str = "global_lip.json",
        snap_middle: bool = False,
    ) -> None:
        cfg.ensure_dirs()
        self._cfg = cfg
        self._tracker_kind: TrackerKind = tracker_kind
        self._tracker = create_tracker(tracker_kind, cfg)
        self._runner = CoTrackerRunner(cfg)
        self._cam_config_dir = require_dir(cam_config_dir, what="camera config")
        self._save_dir = save_dir.expanduser().resolve()
        self._save_dir.mkdir(parents=True, exist_ok=True)
        self._grid_config_path = require_file(
            cfg.grid_configs_dir / grid_config_name, what="grid config"
        )
        self._grid_config = load_grid_config(self._grid_config_path)
        self._snap_middle = snap_middle

    @property
    def _triangulation_tracker(self) -> str:
        # Triangulation outputs go under different folders depending on the
        # tracker, matching the legacy directory layout.
        return "sapiens_cotracker" if self._tracker_kind == "sapiens" else "cotracker"

    def run(self, sample: SampleSpec) -> PipelineResult:
        logger.info("=== %s ===", sample.name)
        cfg = self._cfg
        sample_tmp = cfg.tmp_dir / sample.name
        sample_tmp.mkdir(parents=True, exist_ok=True)

        # 1. Landmark detection on each side.
        landmarks: LandmarkResult = self._tracker.detect_landmarks(
            left_video=sample.left_video,
            right_video=sample.right_video,
            out_dir=sample_tmp,
        )

        # 2. Crop offsets + per-camera ROI crop.
        offsets = compute_crop_offsets(
            left_landmarks=landmarks.left.lip_csv,
            right_landmarks=landmarks.right.lip_csv,
        )
        crop_left = sample_tmp / "vid_L_crop.mp4"
        crop_right = sample_tmp / "vid_R_crop.mp4"
        ffmpeg.crop(
            sample.left_video,
            crop_left,
            width=cfg.crop_width,
            height=cfg.crop_height,
            x=int(offsets.left_x),
            y=int(offsets.left_y),
        )
        ffmpeg.crop(
            sample.right_video,
            crop_right,
            width=cfg.crop_width,
            height=cfg.crop_height,
            x=int(offsets.right_x),
            y=int(offsets.right_y),
        )

        # 3. Translate support points into in-crop coords (overwrite in place,
        # matching legacy behavior — the originals are no longer needed).
        for csv_path, off in (
            (landmarks.left.support_csv, (offsets.left_x, offsets.left_y)),
            (landmarks.right.support_csv, (offsets.right_x, offsets.right_y)),
        ):
            if csv_path.exists():
                translated = apply_crop_offsets(csv_path, offsets_xy=off)
                import numpy as np

                np.savetxt(csv_path, translated, delimiter=",")

        # 4. Build the per-side query table consumed by CoTracker.
        queries = build_lip_queries(
            left_landmarks=landmarks.left.lip_csv,
            right_landmarks=landmarks.right.lip_csv,
            offsets=offsets,
        )

        # 5. Run CoTracker on each cropped side.
        cot_dir = sample_tmp / "cotracker"
        left_out = self._runner.run(
            crop_video=crop_left,
            side="L",
            side_idx=0,
            lip_queries=queries,
            grid_config=self._grid_config,
            support_csv=landmarks.left.support_csv,
            out_dir=cot_dir,
            snap_middle=self._snap_middle,
        )
        right_out = self._runner.run(
            crop_video=crop_right,
            side="R",
            side_idx=1,
            lip_queries=queries,
            grid_config=self._grid_config,
            support_csv=landmarks.right.support_csv,
            out_dir=cot_dir,
            snap_middle=self._snap_middle,
        )

        # 6. Revert crop to full-frame coordinates.
        triangulation_input = sample_tmp / "cotracker_pts.csv"
        revert_crop(
            upper_left_csv=left_out.upper_pts_csv,
            lower_left_csv=left_out.lower_pts_csv,
            upper_right_csv=right_out.upper_pts_csv,
            lower_right_csv=right_out.lower_pts_csv,
            offsets=offsets,
            out_csv=triangulation_input,
        )

        # 7. Triangulate. Image height comes from probing the source video so
        # we never hardcode the legacy 2988 constant.
        info = probe(sample.left_video)
        result = triangulate_pipeline(
            points_csv=triangulation_input,
            cam_config_dir=self._cam_config_dir,
            save_dir=self._save_dir,
            experiment_name=sample.name,
            tracker=self._triangulation_tracker,  # type: ignore[arg-type]
            image_height=info.height,
        )
        return PipelineResult(sample=sample, triangulation=result)


# ---------- module-level convenience entry point ---------- #


def run_pipeline(
    *,
    cfg: Config,
    samples: list[SampleSpec],
    tracker: TrackerKind,
    cam_config_dir: Path,
    save_dir: Path,
    grid_config_name: str = "global_lip.json",
    snap_middle: bool = False,
) -> list[PipelineResult]:
    pipeline = Pipeline(
        cfg,
        tracker_kind=tracker,
        cam_config_dir=cam_config_dir,
        save_dir=save_dir,
        grid_config_name=grid_config_name,
        snap_middle=snap_middle,
    )
    return [pipeline.run(s) for s in samples]


# Reference to keep cv2 imported (used transitively via probe()).
_ = cv2
