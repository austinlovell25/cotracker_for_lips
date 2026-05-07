"""Tracker abstraction.

Two concrete implementations share a common interface so the pipeline
orchestrator does not branch on tracker type:

* :class:`cotracker_lips.trackers.spiga.SpigaTracker` — wraps SPIGA's
  ``app_2d.py`` (vendored under ``SPIGA/spiga/demo``).
* :class:`cotracker_lips.trackers.sapiens.SapiensTracker` — RetinaFace face
  detection + Sapiens torchscript pose estimation.

Plus a CoTracker runner that converts a cropped video + query points into
upper / lower lip CSVs (was ``quickstart.py``).
"""

from cotracker_lips.trackers.base import (
    LandmarkResult,
    PerSideLandmarks,
    Tracker,
    TrackerKind,
    create_tracker,
)
from cotracker_lips.trackers.cotracker_runner import (
    CoTrackerRunner,
    GridConfig,
    load_grid_config,
)

__all__ = [
    "CoTrackerRunner",
    "GridConfig",
    "LandmarkResult",
    "PerSideLandmarks",
    "Tracker",
    "TrackerKind",
    "create_tracker",
    "load_grid_config",
]
