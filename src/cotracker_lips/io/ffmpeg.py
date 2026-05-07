"""Single chokepoint for ffmpeg invocations.

Every subprocess call uses ``shell=False`` with an argument list, captures
stderr, and raises :class:`FFmpegError` on non-zero exit. Callers never build
shell strings.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from cotracker_lips.errors import FFmpegError

logger = logging.getLogger(__name__)

_FFMPEG_QUIET = ("-hide_banner", "-nostats", "-loglevel", "error")


def _resolve_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe is None:
        raise FFmpegError("ffmpeg not found on PATH")
    return exe


def run(args: Sequence[str], *, description: str) -> None:
    """Run ``ffmpeg`` with the given args. Raises on failure."""
    exe = _resolve_ffmpeg()
    cmd = [exe, *_FFMPEG_QUIET, *args]
    logger.debug("ffmpeg %s: %s", description, " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise FFmpegError(
            f"ffmpeg failed during {description!r} (exit {proc.returncode})\n"
            f"stderr: {proc.stderr.strip()}"
        )


def trim(src: Path, dst: Path, *, start_sec: float, length_sec: float) -> None:
    """Copy a time slice from ``src`` to ``dst`` without re-encoding."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "-y",
            "-ss",
            f"{start_sec:.4f}",
            "-t",
            f"{length_sec:.4f}",
            "-i",
            str(src),
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            str(dst),
        ],
        description=f"trim {src.name}",
    )


def shift(src: Path, dst: Path, *, start_sec: float) -> None:
    """Drop the first ``start_sec`` seconds of ``src`` (used for stereo sync)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "-y",
            "-ss",
            f"{start_sec:.4f}",
            "-i",
            str(src),
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            str(dst),
        ],
        description=f"shift {src.name}",
    )


def crop(src: Path, dst: Path, *, width: int, height: int, x: int, y: int) -> None:
    """Crop a fixed-size window from ``src`` and write to ``dst``."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "-y",
            "-i",
            str(src),
            "-filter:v",
            f"crop={width}:{height}:{x}:{y}",
            str(dst),
        ],
        description=f"crop {src.name}",
    )


def extract_first_frame(src: Path, dst: Path) -> None:
    """Write frame 0 of ``src`` as a single image at ``dst``."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "-y",
            "-i",
            str(src),
            "-vf",
            "select=eq(n\\,0)",
            "-vframes",
            "1",
            str(dst),
        ],
        description=f"first-frame {src.name}",
    )


def extract_frames(src: Path, dst_dir: Path, *, pattern: str = "image%d.png") -> None:
    """Extract every frame of ``src`` into ``dst_dir`` using ``pattern``."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "-i",
            str(src),
            "-start_number",
            "0",
            str(dst_dir / pattern),
        ],
        description=f"extract-frames {src.name}",
    )


def crop_image_sequence(
    src_pattern: Path,
    dst_pattern: Path,
    *,
    width: int,
    height: int,
    x: int,
    y: int,
) -> None:
    """Crop a numbered image sequence (``imageN.png``) and write to ``dst``."""
    dst_pattern.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "-i",
            str(src_pattern),
            "-vf",
            f"crop={width}:{height}:{x}:{y}",
            "-c:a",
            "copy",
            str(dst_pattern),
        ],
        description=f"crop-sequence {src_pattern.name}",
    )
