"""Centralised logging setup using loguru (falls back to standard logging)."""

from __future__ import annotations

import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru with a sensible default format.

    If loguru is not installed, falls back to standard logging.
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
