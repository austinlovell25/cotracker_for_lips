"""Thin wrappers around OpenCV's ``VideoCapture``/``VideoWriter``."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import cv2

from cotracker_lips.errors import VideoError


@dataclass(frozen=True)
class VideoInfo:
    fps: float
    width: int
    height: int
    frame_count: int


def probe(video: Path) -> VideoInfo:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise VideoError(f"could not open video: {video}")
    try:
        return VideoInfo(
            fps=float(cap.get(cv2.CAP_PROP_FPS)),
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        )
    finally:
        cap.release()


@contextmanager
def open_capture(video: Path) -> Iterator[cv2.VideoCapture]:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise VideoError(f"could not open video: {video}")
    try:
        yield cap
    finally:
        cap.release()


def first_frame(video: Path) -> "cv2.typing.MatLike":
    with open_capture(video) as cap:
        ok, frame = cap.read()
    if not ok:
        raise VideoError(f"could not read first frame of {video}")
    return frame
