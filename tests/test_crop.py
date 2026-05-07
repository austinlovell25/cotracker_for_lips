"""Crop-offset math (no I/O)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cotracker_lips.io.csv_schema import LANDMARKS_PER_FRAME
from cotracker_lips.postprocess.crop import (
    CROP_LEFT_INSET,
    CROP_UP_INSET,
    build_lip_queries,
    compute_crop_offsets,
)


def _write_landmarks(path, *, base_x: float, base_y: float):
    rows = []
    for _ in range(3):  # several rows so .mean() is exercised
        row = {}
        for i in range(1, LANDMARKS_PER_FRAME + 1):
            row[f"x{i}"] = base_x + i
            row[f"y{i}"] = base_y + i
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)


def test_compute_crop_offsets_anchors_landmark1(tmp_path):
    left = tmp_path / "l.csv"
    right = tmp_path / "r.csv"
    _write_landmarks(left, base_x=1000, base_y=800)
    _write_landmarks(right, base_x=1500, base_y=850)
    offsets = compute_crop_offsets(left_landmarks=left, right_landmarks=right)
    # base + 1 (because x1 = base_x + 1) minus the inset.
    assert offsets.left_x == pytest.approx(1001 - CROP_LEFT_INSET)
    assert offsets.left_y == pytest.approx(801 - CROP_UP_INSET)
    assert offsets.right_x == pytest.approx(1501 - CROP_LEFT_INSET)
    assert offsets.right_y == pytest.approx(851 - CROP_UP_INSET)


def test_build_lip_queries_table_shape(tmp_path):
    left = tmp_path / "l.csv"
    right = tmp_path / "r.csv"
    _write_landmarks(left, base_x=1000, base_y=800)
    _write_landmarks(right, base_x=1500, base_y=850)
    offsets = compute_crop_offsets(left_landmarks=left, right_landmarks=right)
    df = build_lip_queries(left_landmarks=left, right_landmarks=right, offsets=offsets)
    assert df.shape == (2, LANDMARKS_PER_FRAME * 2)
    # x1_mean_incrop must equal CROP_LEFT_INSET by construction (anchor).
    assert df["x1_mean_incrop"][0] == pytest.approx(CROP_LEFT_INSET)
    assert df["y1_mean_incrop"][0] == pytest.approx(CROP_UP_INSET)


def test_compute_crop_offsets_missing_columns(tmp_path):
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"x1": [1], "y1": [1]}).to_csv(bad, index=False)
    with pytest.raises(Exception):
        compute_crop_offsets(left_landmarks=bad, right_landmarks=bad)
