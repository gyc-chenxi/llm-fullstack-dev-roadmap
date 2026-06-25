"""
日志系统（loguru / logging fallback）
======================================

统一日志格式：
  [时间] [级别] [模块名] 消息

双后端策略：
  - loguru 可用时：colorized 格式，更好的人类可读性
  - loguru 不可用时：标准 logging.basicConfig，兼容性最佳
"""

from __future__ import annotations

import sys


def setup_logging(level: str = "INFO") -> None:
    """配置 loguru 或回退到标准 logging。

    日志输出到 stderr（不干扰 stdout 的数据流如 JSON/SSE）。
    """
    try:
        from loguru import logger

        logger.remove()
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <7}</level> | "
                "<cyan>{name}</cyan> | "
                "<level>{message}</level>"
            ),
            level=level,
            colorize=True,
        )
    except ImportError:
        import logging

        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stderr,
        )
