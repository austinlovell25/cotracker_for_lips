"""Config loading, precedence, and coercion."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from cotracker_lips.config import load_config, with_overrides
from cotracker_lips.errors import ConfigError


def test_defaults_load(tmp_path, monkeypatch):
    monkeypatch.delenv("COTRACKER_LIPS_CONFIG", raising=False)
    cfg = load_config()
    assert cfg.cotracker_version in (2, 3)
    assert cfg.crop_width == 704
    assert cfg.crop_height == 512
    assert cfg.audio_sample_rate_hz == 48_000


def test_yaml_overrides_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("COTRACKER_LIPS_CONFIG", raising=False)
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text(
        "cotracker_version: 2\n"
        "crop_width: 800\n"
        "work_dir: " + str(tmp_path) + "\n",
        encoding="utf-8",
    )
    cfg = load_config(config_path=yaml_path)
    assert cfg.cotracker_version == 2
    assert cfg.crop_width == 800


def test_env_overrides_yaml(tmp_path, monkeypatch):
    yaml_path = tmp_path / "cfg.yaml"
    yaml_path.write_text("cotracker_version: 2\n", encoding="utf-8")
    monkeypatch.setenv("COTRACKER_LIPS_COTRACKER_VERSION", "3")
    cfg = load_config(config_path=yaml_path)
    assert cfg.cotracker_version == 3


def test_overrides_beat_env(tmp_path, monkeypatch):
    monkeypatch.setenv("COTRACKER_LIPS_CROP_WIDTH", "100")
    cfg = load_config(overrides={"crop_width": 999, "work_dir": tmp_path})
    assert cfg.crop_width == 999


def test_invalid_version_rejected(tmp_path):
    yaml_path = tmp_path / "bad.yaml"
    yaml_path.write_text("cotracker_version: 7\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config_path=yaml_path)


def test_with_overrides_returns_copy(tmp_path):
    cfg = load_config(overrides={"work_dir": tmp_path})
    cfg2 = with_overrides(cfg, cotracker_version=2)
    assert cfg2 is not cfg
    assert cfg2.cotracker_version == 2
    assert cfg.cotracker_version == 3
