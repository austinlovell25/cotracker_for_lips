"""Convenience helpers for resolving and validating paths."""

from __future__ import annotations

from pathlib import Path

from cotracker_lips.errors import ConfigError


def require_file(path: Path, *, what: str) -> Path:
    """Return ``path`` resolved to an absolute, or raise :class:`ConfigError`."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise ConfigError(f"{what} not found: {p}")
    return p


def require_dir(path: Path, *, what: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_dir():
        raise ConfigError(f"{what} directory not found: {p}")
    return p


def ensure_dir(path: Path) -> Path:
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p
