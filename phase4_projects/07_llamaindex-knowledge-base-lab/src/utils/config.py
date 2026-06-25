"""
YAML 配置加载器
=================

支持点号路径访问嵌套配置键（如 "embedding.model_name"）。

配置层次（优先级从高到低）：
  环境变量 (DEEPSEEK_API_KEY 等) > configs/settings.yaml > 代码硬编码默认值

用法：
    config = Config.load("configs/settings.yaml")
    model_name = config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5")
"""

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """配置管理器，支持点号路径访问嵌套键。

    例：
        cfg = Config.load("configs/settings.yaml")
        model = cfg.get("embedding.model_name")  # 等价于 cfg["embedding"]["model_name"]
    """

    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def load(cls, path: str) -> "Config":
        """从 YAML 文件加载配置。

        Raises:
            ValueError: 配置文件为空
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"配置文件为空: {path}")
        return cls(data)

    def get(self, key_path: str, default: Any = None) -> Any:
        """通过点号路径获取配置值。

        Args:
            key_path: 点号分隔的键路径，如 "embedding.model_name"
            default: 默认值

        Returns:
            配置值，路径中任一中间层不存在时返回 default
        """
        keys = key_path.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def to_dict(self) -> dict:
        """返回原始配置字典。"""
        return self._data


def get_project_root() -> Path:
    """获取项目根目录绝对路径（utils/config.py 向上三级）。"""
    return Path(__file__).resolve().parent.parent.parent


def ensure_dir(path: str) -> Path:
    """确保目录存在，不存在则递归创建。

    Args:
        path: 相对于项目根目录的路径

    Returns:
        目录的绝对 Path 对象
    """
    full_path = get_project_root() / path
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path
