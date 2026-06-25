"""
YAML 配置加载器
=================

从 configs/*.yaml 读取配置，回退到空 dict（安全默认值）。

配置层次：
  .env (运行时覆盖) > config/*.yaml (项目默认) > code defaults (硬编码回退)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml(path: str) -> dict[str, Any]:
    """加载 YAML 配置文件。

    PyYAML 未安装或文件损坏时返回 {}（不阻断启动）。
    """
    target = Path(path)

    if not target.exists():
        return {}

    try:
        import yaml

        with target.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return {}
    except Exception:
        return {}


def get_config_dir() -> Path:
    """返回 configs/ 目录的绝对路径（相对于 utils 模块三级向上）。"""
    return Path(__file__).resolve().parents[3] / "configs"
