"""
日志工具
-------
基于 Python logging + YAML 配置的统一日志初始化。
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import yaml


def setup_logging(
    config_path: str | Path = "configs/logging.yaml",
    default_level: int = logging.INFO,
) -> logging.Logger:
    """初始化日志系统。

    优先从 configs/logging.yaml 加载配置，文件缺失时回退到控制台输出。

    Args:
        config_path: 日志配置文件路径。
        default_level: 回退默认日志级别。

    Returns:
        root logger。
    """
    path = Path(config_path)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if config:
            logging.config.dictConfig(config)
            logger = logging.getLogger("sam2_lab")
            logger.info("Logging configured from %s", path)
            return logger

    # 回退到简单控制台输出
    logger = logging.getLogger("sam2_lab")
    logger.setLevel(default_level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)
    return logger


def get_logger(name: str = "sam2_lab") -> logging.Logger:
    """获取已配置的 logger 实例。"""
    return logging.getLogger(name)
