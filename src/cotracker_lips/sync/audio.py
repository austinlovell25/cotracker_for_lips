"""Stereo video synchronization using a clapperboard impulse.

The pipeline assumes both cameras recorded a sharp audio impulse (clap, slate)
near the start. We extract the PCM signal from each, find the first sample to
exceed a threshold, and time-shift the trailing video so frame 0 of both
clips lines up.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pydub import AudioSegment

from cotracker_lips.config import Config
from cotracker_lips.errors import AudioSyncError
from cotracker_lips.io import ffmpeg
from cotracker_lips.io.paths import require_file

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StereoSync:
    """Result of detecting the clap frame in two videos."""

    left_clap_frame: int
    right_clap_frame: int
    threshold: int

    @property
    def left_offset_seconds(self) -> float:
        """Seconds to drop from the start of the left video to align it."""
        return 0.0  # actual shift is decided in :func:`align_stereo_videos`

    @property
    def lag_frames(self) -> int:
        return self.left_clap_frame - self.right_clap_frame


def extract_pcm(video: Path, *, range_end_sec: float) -> NDArray[np.int32]:
    """Decode the first ``range_end_sec`` seconds of audio as int16 samples."""
    video = require_file(video, what="video")
    audio = AudioSegment.from_file(str(video))
    audio = audio[: int(range_end_sec * 1000)]
    samples = np.frombuffer(audio.raw_data, dtype="<i2")
    return samples.astype(np.int32, copy=False)


def suggested_threshold(
    left: NDArray[np.int32],
    right: NDArray[np.int32],
    *,
    ratio: float,
) -> int:
    """Heuristic threshold = ``ratio * (max(left) + max(right))``."""
    return int((int(left.max()) + int(right.max())) * ratio)


def detect_clap_frames(
    left: NDArray[np.int32],
    right: NDArray[np.int32],
    *,
    fps: int,
    sample_rate_hz: int,
    threshold: int,
) -> tuple[int, int]:
    """Return the (left, right) video frames at which audio first exceeds ``threshold``."""
    if threshold <= 0:
        raise AudioSyncError(f"threshold must be positive, got {threshold}")

    def _first_crossing(signal: NDArray[np.int32], side: str) -> int:
        idx = np.argmax(signal > threshold)
        if signal[idx] <= threshold:
            raise AudioSyncError(
                f"no audio sample on {side} side exceeded threshold {threshold}; "
                "either the clap is outside the search window or the threshold is too high"
            )
        # Each video frame corresponds to (sample_rate_hz * 2 / fps) PCM samples
        # because the .raw_data buffer is interleaved stereo.
        return int(idx * fps / (sample_rate_hz * 2))

    return _first_crossing(left, "left"), _first_crossing(right, "right")


def align_stereo_videos(
    *,
    fps: int,
    left_video: Path,
    right_video: Path,
    sync: StereoSync,
    out_left: Path,
    out_right: Path,
) -> None:
    """Time-shift whichever video starts later so both share frame 0.

    The earlier-starting video is copied as-is; the later one is re-encoded
    from a non-zero start offset (without re-encoding video, to preserve
    quality).
    """
    lag = sync.lag_frames
    if lag == 0:
        ffmpeg.run(["-y", "-i", str(left_video), "-c", "copy", str(out_left)],
                   description="copy left")
        ffmpeg.run(["-y", "-i", str(right_video), "-c", "copy", str(out_right)],
                   description="copy right")
        return

    seconds = abs(lag) / fps
    if lag > 0:
        logger.info("right video starts %d frames (%.3fs) after left", lag, seconds)
        ffmpeg.shift(left_video, out_left, start_sec=seconds)
        ffmpeg.run(["-y", "-i", str(right_video), "-c", "copy", str(out_right)],
                   description="copy right")
    else:
        logger.info("left video starts %d frames (%.3fs) after right", -lag, seconds)
        ffmpeg.shift(right_video, out_right, start_sec=seconds)
        ffmpeg.run(["-y", "-i", str(left_video), "-c", "copy", str(out_left)],
                   description="copy left")


def sync_videos(
    *,
    cfg: Config,
    fps: int,
    left_video: Path,
    right_video: Path,
    range_end_sec: float = 60.0,
    threshold: int | None = None,
) -> StereoSync:
    """End-to-end: extract PCM, pick threshold, find claps, write aligned clips.

    Aligned outputs go to ``cfg.work_dir / left_sync.mp4`` and
    ``cfg.work_dir / right_sync.mp4``.
    """
    cfg.ensure_dirs()
    left_pcm = extract_pcm(left_video, range_end_sec=range_end_sec)
    right_pcm = extract_pcm(right_video, range_end_sec=range_end_sec)

    if threshold is None:
        threshold = suggested_threshold(left_pcm, right_pcm, ratio=cfg.clap_threshold_ratio)
        logger.info("auto-selected clap threshold = %d", threshold)

    left_frame, right_frame = detect_clap_frames(
        left_pcm,
        right_pcm,
        fps=fps,
        sample_rate_hz=cfg.audio_sample_rate_hz,
        threshold=threshold,
    )
    sync = StereoSync(
        left_clap_frame=left_frame,
        right_clap_frame=right_frame,
        threshold=threshold,
    )
    align_stereo_videos(
        fps=fps,
        left_video=left_video,
        right_video=right_video,
        sync=sync,
        out_left=cfg.work_dir / "left_sync.mp4",
        out_right=cfg.work_dir / "right_sync.mp4",
    )
    return sync
