"""Edge-snap a query point onto the nearest video edge.

The legacy ``quickstart.py`` had two near-identical 35-line functions for
snapping in opposite directions; this is the unified version.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import cv2
import numpy as np

from cotracker_lips.errors import VideoError
from cotracker_lips.io import ffmpeg

logger = logging.getLogger(__name__)

EDGE_RATIO = 3
EDGE_KERNEL = 3
EDGE_LOW_THRESHOLD = 10

Direction = Literal["up", "down"]


def _edge_mask(image_path: Path) -> np.ndarray:
    src = cv2.imread(str(image_path))
    if src is None:
        raise VideoError(f"could not open frame for edge detection: {image_path}")
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    blurred = cv2.blur(gray, (3, 3))
    edges = cv2.Canny(blurred, EDGE_LOW_THRESHOLD, EDGE_LOW_THRESHOLD * EDGE_RATIO,
                      apertureSize=EDGE_KERNEL)
    return edges != 0


def snap_to_edge(
    video: Path,
    *,
    point: tuple[float, float],
    direction: Direction,
    threshold_px: int,
    work_dir: Path,
) -> tuple[int, int]:
    """Walk ``point`` ``direction``-ward until it lands on an edge pixel.

    The first frame of ``video`` is decoded once and Canny-edge-filtered;
    starting from ``point`` we step a single pixel at a time toward
    ``direction`` (up or down) until the mask is non-zero or until we've
    moved ``threshold_px`` pixels.

    Returns the snapped ``(x, y)`` integer coordinate.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    edge_image = work_dir / "edge_out.png"
    ffmpeg.extract_first_frame(video, edge_image)

    mask = _edge_mask(edge_image)
    x = round(point[0])
    y = round(point[1])
    origin_y = y
    step = -1 if direction == "up" else 1

    while not mask[y, x]:
        y += step
        if abs(origin_y - y) >= threshold_px:
            return x, origin_y
    return x, y
