"""Typed runtime configuration for the lip-tracking pipeline.

Values resolve in order of precedence: explicit overrides > environment
variables > YAML file > built-in defaults. Loading is centralized in
:func:`load_config` so every module receives the same immutable object.

The default YAML lives at ``configs/default.yaml`` relative to the repository
root, but a user override can be supplied via ``--config`` on the CLI or the
``COTRACKER_LIPS_CONFIG`` environment variable.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

import yaml

from cotracker_lips.errors import ConfigError

logger = logging.getLogger(__name__)

_ENV_PREFIX = "COTRACKER_LIPS_"
_PACKAGE_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_ROOT.parent.parent.parent
_DEFAULT_YAML = _REPO_ROOT / "configs" / "default.yaml"

CotrackerVersion = Literal[2, 3]
Device = Literal["cuda", "cpu", "auto"]


@dataclass(frozen=True)
class Config:
    """Immutable runtime configuration shared across the pipeline.

    All paths are resolved to absolutes during :func:`load_config`.
    """

    work_dir: Path
    """Root directory for all intermediate and output files for a run."""

    cotracker_checkpoints: Path
    """Directory containing ``cotracker2.pth`` / ``scaled_online.pth``."""

    grid_configs_dir: Path
    """Directory containing the JSON grid configuration files."""

    repo_root: Path
    """Repository root — needed to locate the vendored SPIGA app."""

    sapiens_scripts_dir: Path | None = None
    """Optional path to the Sapiens torchscript scripts directory."""

    sapiens_conda_env: str = "sapiens_lite"
    spiga_model: str = "300wprivate"
    cotracker_version: CotrackerVersion = 3
    device: Device = "auto"
    crop_width: int = 704
    crop_height: int = 512
    sapiens_crop_size: int = 700
    audio_sample_rate_hz: int = 48_000
    clap_threshold_ratio: float = 6 / 16

    extras: dict[str, Any] = field(default_factory=dict)
    """Arbitrary keys from the YAML preserved verbatim."""

    @property
    def tmp_dir(self) -> Path:
        return self.work_dir / "tmp"

    def ensure_dirs(self) -> None:
        """Create directories that the pipeline expects to exist."""
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)


_DEFAULTS: dict[str, Any] = {
    "work_dir": ".",
    "cotracker_checkpoints": "./checkpoints",
    "grid_configs_dir": str(_REPO_ROOT / "configs" / "grid_configs"),
    "repo_root": str(_REPO_ROOT),
    "sapiens_scripts_dir": None,
    "sapiens_conda_env": "sapiens_lite",
    "spiga_model": "300wprivate",
    "cotracker_version": 3,
    "device": "auto",
    "crop_width": 704,
    "crop_height": 512,
    "sapiens_crop_size": 700,
    "audio_sample_rate_hz": 48_000,
    "clap_threshold_ratio": 6 / 16,
}

_PATH_KEYS = {
    "work_dir",
    "cotracker_checkpoints",
    "grid_configs_dir",
    "repo_root",
    "sapiens_scripts_dir",
}


def _coerce(key: str, value: Any) -> Any:
    if value is None:
        return None
    if key in _PATH_KEYS:
        return Path(value).expanduser().resolve()
    if key == "cotracker_version":
        v = int(value)
        if v not in (2, 3):
            raise ConfigError(f"cotracker_version must be 2 or 3, got {value!r}")
        return v
    if key == "device":
        v = str(value).lower()
        if v not in ("cuda", "cpu", "auto"):
            raise ConfigError(f"device must be cuda/cpu/auto, got {value!r}")
        return v
    if key in ("crop_width", "crop_height", "sapiens_crop_size", "audio_sample_rate_hz"):
        return int(value)
    if key == "clap_threshold_ratio":
        return float(value)
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except OSError as e:
        raise ConfigError(f"could not read config file {path}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"top level of {path} must be a YAML mapping")
    return data


def _read_env() -> dict[str, Any]:
    """Pull ``COTRACKER_LIPS_*`` environment variables into a dict."""
    out: dict[str, Any] = {}
    for name, value in os.environ.items():
        if not name.startswith(_ENV_PREFIX):
            continue
        key = name[len(_ENV_PREFIX) :].lower()
        if key in _DEFAULTS:
            out[key] = value
    return out


def load_config(
    config_path: Path | str | None = None,
    overrides: dict[str, Any] | None = None,
) -> Config:
    """Resolve a :class:`Config` from YAML, env, and explicit overrides.

    Parameters
    ----------
    config_path
        Path to a YAML file. If ``None``, falls back to
        ``$COTRACKER_LIPS_CONFIG`` and finally the bundled
        ``configs/default.yaml``.
    overrides
        Highest-precedence values, typically populated from CLI flags.
    """
    merged: dict[str, Any] = dict(_DEFAULTS)

    yaml_path: Path | None
    if config_path is not None:
        yaml_path = Path(config_path).expanduser().resolve()
    elif "COTRACKER_LIPS_CONFIG" in os.environ:
        yaml_path = Path(os.environ["COTRACKER_LIPS_CONFIG"]).expanduser().resolve()
    elif _DEFAULT_YAML.exists():
        yaml_path = _DEFAULT_YAML
    else:
        yaml_path = None

    if yaml_path is not None:
        if not yaml_path.exists():
            raise ConfigError(f"config file does not exist: {yaml_path}")
        logger.debug("loading config from %s", yaml_path)
        merged.update(_load_yaml(yaml_path))

    merged.update(_read_env())
    if overrides:
        merged.update({k: v for k, v in overrides.items() if v is not None})

    extras: dict[str, Any] = {}
    coerced: dict[str, Any] = {}
    for k, v in merged.items():
        if k in _DEFAULTS:
            coerced[k] = _coerce(k, v)
        else:
            extras[k] = v
    coerced["extras"] = extras

    try:
        return Config(**coerced)
    except TypeError as e:
        raise ConfigError(f"invalid config: {e}") from e


def with_overrides(cfg: Config, **kwargs: Any) -> Config:
    """Return a copy of ``cfg`` with the given fields replaced."""
    return replace(cfg, **kwargs)
