"""3D markerless lip tracking from stereo video.

The public entry points are:

* :func:`cotracker_lips.run_pipeline` — programmatic orchestrator.
* The ``cotracker-lips`` console script (see :mod:`cotracker_lips.cli`).
"""

from __future__ import annotations

from cotracker_lips._version import __version__
from cotracker_lips.config import Config, load_config
from cotracker_lips.pipeline.orchestrator import Pipeline, PipelineResult, run_pipeline

__all__ = [
    "Config",
    "Pipeline",
    "PipelineResult",
    "__version__",
    "load_config",
    "run_pipeline",
]
