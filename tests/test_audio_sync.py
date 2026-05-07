"""Pure-Python pieces of the audio sync algorithm."""

from __future__ import annotations

import numpy as np
import pytest

from cotracker_lips.errors import AudioSyncError
from cotracker_lips.sync.audio import detect_clap_frames, suggested_threshold


def test_suggested_threshold_uses_ratio_of_max_sum():
    left = np.array([0, 100, 50], dtype=np.int32)
    right = np.array([0, 60, 20], dtype=np.int32)
    # ratio 0.5 ⇒ (100 + 60) * 0.5 = 80
    assert suggested_threshold(left, right, ratio=0.5) == 80


def test_detect_clap_frames_basic():
    # clap at sample 96 in left, sample 192 in right.
    # With fps=30 and sample_rate_hz=48_000, frame index =
    #   sample * 30 / (48000 * 2)  →  sample / 3200
    # So 96 ≈ frame 0 (rounds down), 192 ≈ frame 0 too — pick larger samples.
    left = np.zeros(100_000, dtype=np.int32)
    right = np.zeros(100_000, dtype=np.int32)
    left[6400] = 1000   # frame 1
    right[19200] = 1000  # frame 3
    lf, rf = detect_clap_frames(
        left, right, fps=30, sample_rate_hz=48_000, threshold=500,
    )
    assert lf == 2
    assert rf == 6


def test_detect_clap_frames_raises_when_below_threshold():
    left = np.zeros(10, dtype=np.int32)
    right = np.zeros(10, dtype=np.int32)
    left[0] = 5
    right[0] = 5
    with pytest.raises(AudioSyncError):
        detect_clap_frames(
            left, right, fps=30, sample_rate_hz=48_000, threshold=10_000
        )


def test_detect_clap_frames_rejects_non_positive_threshold():
    left = np.array([0, 1], dtype=np.int32)
    with pytest.raises(AudioSyncError):
        detect_clap_frames(left, left, fps=30, sample_rate_hz=48_000, threshold=0)
