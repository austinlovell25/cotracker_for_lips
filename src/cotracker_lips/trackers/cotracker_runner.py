"""Run CoTracker on a cropped video with a configurable query grid.

This module is the refactored core of the legacy ``quickstart.py``: it loads
the cropped video, builds the set of query points (lip landmarks plus
optional grid / contour / SPIGA-support points), runs CoTracker online,
visualizes results, and writes the per-frame upper / lower CSVs the
post-processor consumes.
"""

from __future__ import annotations

import contextlib
import csv
import json
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Literal

import imageio.v3 as iio
import numpy as np
import pandas as pd
import torch
from numpy.typing import NDArray

from cotracker_lips.config import Config
from cotracker_lips.errors import ConfigError, VideoError
from cotracker_lips.io.paths import require_file
from cotracker_lips.postprocess.snap import snap_to_edge

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GridConfig:
    """Mirror of the JSON files under ``configs/grid_configs``."""

    global_grid: bool = False
    local_grid: bool = False
    dense_local: bool = False
    lip_contour: bool = False
    spiga_support: bool = False
    x1: float = 0.0
    x2: float = 0.0
    x3: float = 0.0
    y1: float = 0.0
    y2: float = 0.0
    y3: float = 0.0


def load_grid_config(path: Path) -> GridConfig:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    fields = {f.name for f in GridConfig.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    return GridConfig(**{k: v for k, v in data.items() if k in fields})


# ---------- query-point grid construction ---------- #


def _global_grid(x_end: int, y_end: int, *, x_step: int = 70, y_step: int = 50) -> Iterable[list[float]]:
    for x in range(0, x_end, x_step):
        for y in range(0, y_end, y_step):
            yield [0.0, float(x), float(y)]


def _grid_loop(
    x: float,
    y: float,
    *,
    x_max: float,
    y_max: float,
    x_step: float,
    y_step: float,
) -> Iterable[list[float]]:
    x_iter = max(int(x_step), 1)
    y_iter = max(int(y_step), 1)
    for dx in range(1, max(int(x_max), 1), x_iter):
        for dy in range(1, max(int(y_max), 1), y_iter):
            yield [0.0, x + dx, y]
            yield [0.0, x - dx, y]
            yield [0.0, x, y + dy]
            yield [0.0, x, y - dy]
            yield [0.0, x + dx, y + dy]
            yield [0.0, x + dx, y - dy]
            yield [0.0, x - dx, y + dy]
            yield [0.0, x - dx, y - dy]


def _local_grid(x: float, y: float, gc: GridConfig) -> Iterable[list[float]]:
    if gc.dense_local:
        yield from _grid_loop(x, y, x_max=5, y_max=5, x_step=1, y_step=1)
    yield from _grid_loop(
        x, y, x_max=gc.x1, y_max=gc.y2, x_step=gc.y3, y_step=gc.y3
    )


def _contour_grid(x: float, y: float, *, is_upper: bool, size: int = 20, step: int = 5) -> Iterable[list[float]]:
    sign_y = -1 if is_upper else 1
    for i in range(0, size, step):
        for j in range(0, size, step):
            yield [0.0, x - i, y + sign_y * j]
            yield [0.0, x + i, y + sign_y * j]
            yield [0.0, x - i, y - sign_y * j]
            yield [0.0, x + i, y - sign_y * j]


def _read_support_csv(path: Path) -> Iterable[list[float]]:
    with path.open("r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            yield [0.0, float(row[1]), float(row[2])]


# ---------- public runner ---------- #


@dataclass(frozen=True)
class CoTrackerOutputs:
    upper_pts_csv: Path
    lower_pts_csv: Path
    overlay_video: Path


@contextlib.contextmanager
def _pushd(path: Path) -> Iterator[None]:
    """Temporarily change cwd. Used to redirect the vendored visualizer's
    hardcoded ``tmp/vid{N}/...`` outputs into our per-run work dir."""
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class CoTrackerRunner:
    """Stateful runner — owns the loaded model so multiple videos amortize the load."""

    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._model: object | None = None
        self._device = self._resolve_device(cfg.device)

    @staticmethod
    def _resolve_device(setting: str) -> str:
        if setting == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        if setting == "cuda" and not torch.cuda.is_available():
            logger.warning("device=cuda requested but no GPU available; falling back to cpu")
            return "cpu"
        return setting

    def _load_model(self) -> object:
        if self._model is not None:
            return self._model
        if self._cfg.cotracker_version == 3:
            from cotracker.predictor import CoTrackerOnlinePredictor  # type: ignore[import-untyped]

            ckpt = self._cfg.cotracker_checkpoints / "scaled_online.pth"
            if not ckpt.is_file():
                raise ConfigError(f"CoTracker3 checkpoint missing: {ckpt}")
            logger.info("loading CoTracker3 from %s", ckpt)
            model = CoTrackerOnlinePredictor(str(ckpt)).to(self._device)
        else:
            logger.info("loading CoTracker2 via torch.hub")
            model = torch.hub.load(
                "facebookresearch/co-tracker",
                "cotracker2_online",
                force_reload=False,
            ).to(self._device)
        self._model = model
        return model

    def _build_queries(
        self,
        *,
        lip_queries: pd.DataFrame,
        side_idx: int,
        grid_config: GridConfig,
        support_csv: Path | None,
        crop_video: Path,
        snap_middle: bool,
        snap_threshold_px: int = 10,
    ) -> torch.Tensor:
        # Start with the 10 lip landmarks for this side.
        pts: list[list[float]] = []
        for i in range(1, 11):
            pts.append([
                0.0,
                float(lip_queries[f"x{i}_mean_incrop"][side_idx]),
                float(lip_queries[f"y{i}_mean_incrop"][side_idx]),
            ])

        # Optional: snap upper-row points to the nearest edge so the tracker
        # locks onto the actual lip line.
        if snap_middle:
            for idx in (9, 1, 3, 5, 7):  # the upper-row indices
                x, y = snap_to_edge(
                    crop_video,
                    point=(pts[idx][1], pts[idx][2]),
                    direction="up",
                    threshold_px=snap_threshold_px,
                    work_dir=self._cfg.tmp_dir,
                )
                pts[idx][1] = float(x)
                pts[idx][2] = float(y)

        if grid_config.global_grid:
            pts.extend(_global_grid(700, 500))
        if grid_config.local_grid:
            pts.extend(_local_grid(
                float(lip_queries[f"x10_mean_incrop"][side_idx]),
                float(lip_queries[f"y10_mean_incrop"][side_idx]),
                grid_config,
            ))
            pts.extend(_local_grid(
                float(lip_queries[f"x9_mean_incrop"][side_idx]),
                float(lip_queries[f"y9_mean_incrop"][side_idx]),
                grid_config,
            ))
        if grid_config.lip_contour:
            pts.extend(_contour_grid(
                float(lip_queries[f"x10_mean_incrop"][side_idx]),
                float(lip_queries[f"y10_mean_incrop"][side_idx]),
                is_upper=True,
            ))
            pts.extend(_contour_grid(
                float(lip_queries[f"x9_mean_incrop"][side_idx]),
                float(lip_queries[f"y9_mean_incrop"][side_idx]),
                is_upper=False,
            ))
        if grid_config.spiga_support and support_csv is not None and support_csv.exists():
            pts.extend(list(_read_support_csv(support_csv)))

        queries = torch.tensor(pts, device=self._device)
        return queries

    def run(
        self,
        *,
        crop_video: Path,
        side: Literal["L", "R"],
        side_idx: int,
        lip_queries: pd.DataFrame,
        grid_config: GridConfig,
        support_csv: Path | None,
        out_dir: Path,
        snap_middle: bool,
    ) -> CoTrackerOutputs:
        """Run CoTracker on one cropped video and emit upper/lower CSVs."""
        crop_video = require_file(crop_video, what="cropped video")
        out_dir.mkdir(parents=True, exist_ok=True)

        from cotracker.utils.visualizer import Visualizer  # type: ignore[import-untyped]

        model = self._load_model()
        queries = self._build_queries(
            lip_queries=lip_queries,
            side_idx=side_idx,
            grid_config=grid_config,
            support_csv=support_csv,
            crop_video=crop_video,
            snap_middle=snap_middle,
        )

        frames = iio.imread(str(crop_video), plugin="FFMPEG")
        if frames.ndim != 4:
            raise VideoError(f"unexpected frame array shape from {crop_video}: {frames.shape}")

        video = (
            torch.tensor(frames).permute(0, 3, 1, 2)[None].float().to(self._device)
        )

        # CoTrackerOnlinePredictor convention: prime with is_first_step=True,
        # then iterate in `step`-frame chunks.
        model(video_chunk=video, is_first_step=True, queries=queries[None])
        pred_tracks: torch.Tensor | None = None
        pred_visibility: torch.Tensor | None = None
        for ind in range(0, video.shape[1] - model.step, model.step):
            pred_tracks, pred_visibility = model(
                video_chunk=video[:, ind : ind + model.step * 2],
                queries=queries[None],
            )
        if pred_tracks is None or pred_visibility is None:
            raise VideoError(f"CoTracker produced no output for {crop_video}")

        # The vendored Visualizer hardcodes a `tmp/vid{N}/` write path for
        # `upper_pts.csv` / `lower_pts.csv`. Run it from a scratch directory
        # so those files land somewhere we control.
        scratch = self._cfg.tmp_dir / f"cot_scratch_{side}"
        if scratch.exists():
            shutil.rmtree(scratch)
        scratch.mkdir(parents=True)

        side_num = 0 if side == "L" else 1
        with _pushd(scratch):
            vis = Visualizer(save_dir=str(out_dir), pad_value=0, linewidth=3)
            vis.visualize(
                video,
                pred_tracks,
                pred_visibility,
                filename=f"{side_num}_queries_notrace",
                video_num=side_num,
            )

        # Move the visualizer's `tmp/vid{N}/*.csv` into `out_dir/vid{N}/`.
        scratch_side = scratch / "tmp" / f"vid{side_num}"
        out_side = out_dir / f"vid{side_num}"
        out_side.mkdir(parents=True, exist_ok=True)
        upper = out_side / "upper_pts.csv"
        lower = out_side / "lower_pts.csv"
        for src_name, dst in (("upper_pts.csv", upper), ("lower_pts.csv", lower)):
            src = scratch_side / src_name
            if not src.is_file():
                raise VideoError(f"CoTracker visualizer did not emit {src}")
            shutil.move(str(src), dst)

        overlay_src = out_dir / f"{side_num}_queries_notrace.mp4"
        overlay_dst = out_side / f"{side_num}_queries_notrace.mp4"
        if overlay_src.is_file() and overlay_src != overlay_dst:
            shutil.move(str(overlay_src), overlay_dst)
        return CoTrackerOutputs(
            upper_pts_csv=upper,
            lower_pts_csv=lower,
            overlay_video=overlay_dst,
        )


# Keep numpy/numpy.typing imports referenced for API users that read this file.
_ = NDArray
