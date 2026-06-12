"""
YAML 配置加载器
--------------
从 configs/ 目录加载 YAML 配置文件，返回字典或可选的数据类实例。
支持嵌套 key 访问（如 "sam2.model.size"）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# 项目根目录（sam2_lab/config.py → src/sam2_lab/ → 项目根）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_DIR = _PROJECT_ROOT / "configs"


def load_config(name: str) -> dict[str, Any]:
    """加载指定配置文件为字典。

    Args:
        name: 配置文件名（不含 .yaml 后缀），如 "sam2"、"app"、"inpaint"。

    Returns:
        配置字典。文件不存在时返回空字典。
    """
    path = _CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        print(f"[config] 配置文件不存在: {path}")
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_nested(config: dict, key_path: str, default: Any = None) -> Any:
    """从嵌套字典中按点分隔路径取值。

    Args:
        config: 配置字典。
        key_path: 点分隔的 key 路径，如 "sam2.model.size"。
        default: 默认值。

    Returns:
        对应的值或 default。
    """
    keys = key_path.split(".")
    node = config
    for k in keys:
        if isinstance(node, dict) and k in node:
            node = node[k]
        else:
            return default
    return node
