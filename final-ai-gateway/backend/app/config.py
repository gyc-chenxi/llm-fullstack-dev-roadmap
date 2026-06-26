"""
Application configuration loaded from YAML files and env vars.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class Config:
    def __init__(self, config_dir: str | None = None):
        load_dotenv()
        if config_dir is None:
            config_dir = os.getenv("CONFIG_DIR", str(Path(__file__).parent.parent.parent / "configs"))
        self._config_dir = Path(config_dir)
        self._data: dict[str, Any] = {}
        self._load_all()

    def _load_all(self):
        for name in ["app", "model", "rag", "logging"]:
            path = self._config_dir / f"{name}.yaml"
            if path.exists():
                with open(path) as f:
                    self._data[name] = yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    @property
    def app_config(self) -> dict:
        return self._data.get("app", {})

    @property
    def model_config(self) -> dict:
        return self._data.get("model", {})

    @property
    def rag_config(self) -> dict:
        return self._data.get("rag", {})

    @property
    def default_model(self) -> str:
        return self.get("model.model_selection.default", "qwen2.5-7b-instruct-q4_k_m")

    @property
    def redis_url(self) -> str:
        host = os.getenv("REDIS_HOST", "localhost")
        port = os.getenv("REDIS_PORT", "6379")
        db = os.getenv("REDIS_DB", "0")
        password = os.getenv("REDIS_PASSWORD", "")
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"


config = Config()
