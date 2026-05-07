"""Audio-based stereo synchronization (clapperboard detection)."""

from cotracker_lips.sync.audio import (
    StereoSync,
    align_stereo_videos,
    detect_clap_frames,
    extract_pcm,
    suggested_threshold,
)

__all__ = [
    "StereoSync",
    "align_stereo_videos",
    "detect_clap_frames",
    "extract_pcm",
    "suggested_threshold",
]
