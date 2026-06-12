from pathlib import Path
from typing import Any
import yaml

def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")

    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {p}")

    return data

def runtime_flag(cfg: dict, key: str, default: bool = False) -> bool:
    runtime = cfg.get("runtime") or {}
    return bool(runtime.get(key, default))
