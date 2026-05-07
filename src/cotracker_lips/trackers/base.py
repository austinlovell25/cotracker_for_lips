"""Tracker interface and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from cotracker_lips.config import Config

TrackerKind = Literal["spiga", "sapiens"]
Side = Literal["L", "R"]


@dataclass(frozen=True)
class PerSideLandmarks:
    """The two CSVs a single-camera detection produces.

    ``lip_csv`` is the 10-point ``x{i}/y{i}`` table; ``support_csv`` is the
    SPIGA support points used to seed CoTracker queries elsewhere on the face.
    Sapiens emits an empty ``support_csv`` because its dense pose output
    already covers the lip contour.
    """

    lip_csv: Path
    support_csv: Path


@dataclass(frozen=True)
class LandmarkResult:
    left: PerSideLandmarks
    right: PerSideLandmarks


class Tracker(ABC):
    """Detect 2D lip landmarks on each video of a stereo pair."""

    @abstractmethod
    def detect_landmarks(
        self,
        *,
        left_video: Path,
        right_video: Path,
        out_dir: Path,
    ) -> LandmarkResult: ...


def create_tracker(kind: TrackerKind, cfg: Config) -> Tracker:
    """Construct the tracker named by ``kind``.

    Imports are local so we do not pay the Sapiens import cost (and its
    Sapiens-only deps) when the user only wants SPIGA.
    """
    if kind == "spiga":
        from cotracker_lips.trackers.spiga import SpigaTracker

        return SpigaTracker(cfg)
    if kind == "sapiens":
        from cotracker_lips.trackers.sapiens import SapiensTracker

        return SapiensTracker(cfg)
    raise ValueError(f"unknown tracker kind: {kind!r}")
