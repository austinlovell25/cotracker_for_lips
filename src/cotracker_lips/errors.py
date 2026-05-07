"""Typed exceptions raised at module boundaries.

Internal helpers should raise the most specific subclass available so the CLI
layer can map them to clean user-facing messages without exposing tracebacks.
"""

from __future__ import annotations


class CotrackerLipsError(Exception):
    """Base class for all package-defined errors."""


class ConfigError(CotrackerLipsError):
    """Raised when configuration is missing, malformed, or self-inconsistent."""


class VideoError(CotrackerLipsError):
    """Raised when a video file cannot be opened or has unexpected properties."""


class AudioSyncError(CotrackerLipsError):
    """Raised when stereo audio sync (clap detection) fails."""


class CalibrationError(CotrackerLipsError):
    """Raised during stereo camera calibration or triangulation."""


class LandmarkDetectionError(CotrackerLipsError):
    """Raised when SPIGA / Sapiens / RetinaFace fails to produce landmarks."""


class FFmpegError(CotrackerLipsError):
    """Raised when an ffmpeg subprocess returns a non-zero exit code."""
