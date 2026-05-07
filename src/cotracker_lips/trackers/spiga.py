"""SPIGA-based facial landmark detection.

SPIGA is vendored at ``<repo>/SPIGA``. The original pipeline shelled out to
``python SPIGA/spiga/demo/app_2d.py`` and harvested the ``2d_lip_coordinates.csv``
and ``support_pts.csv`` files from the working directory. We preserve that
contract because the SPIGA fork has been locally modified — but we move the
result files into per-side locations under the run's work dir, which lets the
pipeline run twice without files clobbering each other.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from cotracker_lips.config import Config
from cotracker_lips.errors import LandmarkDetectionError
from cotracker_lips.io.paths import require_file
from cotracker_lips.trackers.base import LandmarkResult, PerSideLandmarks, Tracker

logger = logging.getLogger(__name__)

_SPIGA_REL_PATH = "SPIGA/spiga/demo/app_2d.py"
_LIP_CSV_NAME = "2d_lip_coordinates.csv"
_SUPPORT_CSV_NAME = "support_pts.csv"


class SpigaTracker(Tracker):
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._app_2d = (cfg.repo_root / _SPIGA_REL_PATH).resolve()
        if not self._app_2d.is_file():
            raise LandmarkDetectionError(
                f"SPIGA app_2d.py not found at {self._app_2d}; "
                "the vendored SPIGA copy is required"
            )

    def _run_once(
        self,
        video: Path,
        *,
        cwd: Path,
        crop_shift_iter: int | None = None,
    ) -> tuple[Path, Path]:
        env = os.environ.copy()
        if crop_shift_iter is not None:
            shake_path = (
                self._cfg.repo_root
                / "SPIGA/spiga/demo/analyze/track/retinasort/shake_opt.txt"
            )
            shake_path.parent.mkdir(parents=True, exist_ok=True)
            shake_path.write_text(f"{crop_shift_iter}\n")

        cmd = [
            sys.executable,
            str(self._app_2d),
            "-i",
            str(video),
            "-d",
            self._cfg.spiga_model,
        ]
        if crop_shift_iter is not None:
            cmd += ["--shake", "True"]

        logger.debug("running SPIGA: %s (cwd=%s)", " ".join(cmd), cwd)
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise LandmarkDetectionError(
                f"SPIGA app_2d.py failed (exit {proc.returncode})\nstderr: {proc.stderr.strip()}"
            )

        lip = cwd / _LIP_CSV_NAME
        support = cwd / _SUPPORT_CSV_NAME
        if not lip.is_file() or not support.is_file():
            raise LandmarkDetectionError(
                f"SPIGA did not emit expected CSVs in {cwd}; "
                f"found lip={lip.is_file()}, support={support.is_file()}"
            )
        return lip, support

    def _detect_one(
        self,
        video: Path,
        *,
        out_dir: Path,
        side_name: str,
        crop_shift_iters: int = 0,
    ) -> PerSideLandmarks:
        cwd = self._cfg.repo_root
        if crop_shift_iters > 0:
            for i in range(crop_shift_iters):
                self._run_once(video, cwd=cwd, crop_shift_iter=i)
        # Final detection — when crop_shift is on, this is the last iteration
        # whose CSVs we keep.
        lip_src, support_src = self._run_once(
            video,
            cwd=cwd,
            crop_shift_iter=crop_shift_iters - 1 if crop_shift_iters > 0 else None,
        )

        out_dir.mkdir(parents=True, exist_ok=True)
        lip_dst = out_dir / f"2d_lip_coords_{side_name}.csv"
        support_dst = out_dir / f"spiga_support_{side_name}.csv"
        shutil.move(str(lip_src), lip_dst)
        shutil.move(str(support_src), support_dst)
        return PerSideLandmarks(lip_csv=lip_dst, support_csv=support_dst)

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

        left = self._detect_one(left_video, out_dir=out_dir, side_name="L")
        right = self._detect_one(right_video, out_dir=out_dir, side_name="R")

        # Reset shake_opt.txt to 0 so future invocations start clean.
        shake_path = (
            self._cfg.repo_root / "SPIGA/spiga/demo/analyze/track/retinasort/shake_opt.txt"
        )
        if shake_path.parent.exists():
            shake_path.write_text("0\n")
        return LandmarkResult(left=left, right=right)
