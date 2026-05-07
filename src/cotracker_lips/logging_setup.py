"""Centralized logging configuration.

Library code uses module-level loggers (``logger = logging.getLogger(__name__)``)
without configuring handlers. The CLI and GUI entry points call
:func:`configure_logging` exactly once at startup.
"""

from __future__ import annotations

import logging
import os
import sys

_DEFAULT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def configure_logging(level: int | str | None = None) -> None:
    """Install a single stderr handler on the root logger.

    Resolution order: explicit ``level`` argument, then ``COTRACKER_LIPS_LOG``
    environment variable, then INFO.
    """
    if level is None:
        level = os.environ.get("COTRACKER_LIPS_LOG", "INFO")
    if isinstance(level, str):
        level = level.upper()

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, "%H:%M:%S"))
    root.addHandler(handler)
    root.setLevel(level)
