"""YAML config loader — reads configs/*.yaml into typed dataclasses."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml(path: str) -> dict[str, Any]:
    """Load a YAML config file, falling back to empty dict on error."""
    target = Path(path)

    if not target.exists():
        return {}

    try:
        import yaml

        with target.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # PyYAML not installed — return empty.
        return {}
    except Exception:
        return {}


def get_config_dir() -> Path:
    """Return the absolute path to the configs/ directory."""
    return Path(__file__).resolve().parents[3] / "configs"
