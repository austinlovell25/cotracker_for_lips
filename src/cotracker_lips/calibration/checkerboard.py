"""Pull a pseudo-random sample of checkerboard frames from each video.

For OpenCV's ``stereoCalibrate`` we need matched left/right frames. The video
pair is already temporally synced (see :mod:`cotracker_lips.sync`), so picking
the *same* frame indices on both sides guarantees correspondence.

Output layout (rooted at ``out_dir``)::

    D2/      ← left frames  (camera 1)
    J2/      ← right frames (camera 2)
    synced/  ← both, used by stereoCalibrate
"""

from __future__ import annotations

import logging
import random
import shutil
from pathlib import Path

import cv2

from cotracker_lips.errors import VideoError
from cotracker_lips.io.video import open_capture

logger = logging.getLogger(__name__)

DEFAULT_NUM_FRAMES = 50
_LEFT_DIR = "D2"
_RIGHT_DIR = "J2"
_SYNCED_DIR = "synced"


def _write_frames(
    video: Path,
    indices: list[int],
    *,
    out_dir: Path,
    cam_num: int,
) -> list[Path]:
    """Decode ``video`` once, dumping requested frame indices as PNGs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with open_capture(video) as cap:
        wanted = sorted(set(indices))
        max_idx = wanted[-1]
        idx = 0
        count = 1
        ok, frame = cap.read()
        while ok and idx <= max_idx:
            if idx in wanted:
                dst = out_dir / f"camera-{cam_num}-{count:02d}.png"
                if not cv2.imwrite(str(dst), frame, [cv2.IMWRITE_PNG_COMPRESSION, 0]):
                    raise VideoError(f"failed to write {dst}")
                written.append(dst)
                count += 1
            ok, frame = cap.read()
            idx += 1
    if len(written) < len(wanted):
        raise VideoError(
            f"requested {len(wanted)} frames but only decoded {len(written)} from {video}"
        )
    return written


def extract_checkerboard_frames(
    *,
    left_video: Path,
    right_video: Path,
    start_frame: int,
    end_frame: int,
    out_dir: Path,
    num_frames: int = DEFAULT_NUM_FRAMES,
    seed: int | None = None,
) -> None:
    """Sample ``num_frames`` random indices in ``[start_frame, end_frame]`` from
    both videos and lay them out for OpenCV calibration.

    The same indices are used on both sides — combined with the audio-sync
    step that ran earlier, this gives time-matched stereo pairs.
    """
    if end_frame <= start_frame:
        raise ValueError(f"end_frame ({end_frame}) must be > start_frame ({start_frame})")

    rng = random.Random(seed)
    indices = [rng.randint(start_frame, end_frame) for _ in range(num_frames)]
    logger.info("sampling %d checkerboard frames in [%d, %d]", num_frames, start_frame, end_frame)

    out_dir = out_dir.expanduser().resolve()
    left_dir = out_dir / _LEFT_DIR
    right_dir = out_dir / _RIGHT_DIR
    synced_dir = out_dir / _SYNCED_DIR

    for d in (left_dir, right_dir, synced_dir):
        if d.exists():
            shutil.rmtree(d)
    left_frames = _write_frames(left_video, indices, out_dir=left_dir, cam_num=1)
    right_frames = _write_frames(right_video, indices, out_dir=right_dir, cam_num=2)

    synced_dir.mkdir(parents=True, exist_ok=True)
    for src in (*left_frames, *right_frames):
        shutil.copy2(src, synced_dir / src.name)

    logger.info("wrote %d frames to %s", len(left_frames) + len(right_frames), out_dir)
