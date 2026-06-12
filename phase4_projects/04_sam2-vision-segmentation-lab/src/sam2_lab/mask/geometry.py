"""
Mask 几何计算工具
----------------
计算 mask 的几何属性：质心、边界框、紧凑度等。
"""
from __future__ import annotations

import cv2
import numpy as np


def mask_centroid(mask: np.ndarray) -> tuple[float, float]:
    """计算 mask 的质心坐标。

    Args:
        mask: bool 类型 mask 数组 (H, W)。

    Returns:
        (cx, cy) 质心坐标。
    """
    if mask.dtype != bool:
        mask = mask > 0

    moments = cv2.moments(mask.astype(np.uint8))
    if moments["m00"] == 0:
        return (0.0, 0.0)

    cx = moments["m10"] / moments["m00"]
    cy = moments["m01"] / moments["m00"]
    return (float(cx), float(cy))


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    """计算 mask 的轴对齐边界框。

    Args:
        mask: bool 类型 mask 数组。

    Returns:
        (x, y, w, h) 左上角坐标 + 宽高。
    """
    if mask.dtype != bool:
        mask = mask > 0

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any():
        return (0, 0, 0, 0)

    ymin, ymax = np.where(rows)[0][[0, -1]]
    xmin, xmax = np.where(cols)[0][[0, -1]]
    return (int(xmin), int(ymin), int(xmax - xmin + 1), int(ymax - ymin + 1))


def mask_compactness(mask: np.ndarray) -> float:
    """计算 mask 紧凑度：4π·面积 / 周长²。

    Args:
        mask: bool 类型 mask 数组。

    Returns:
        紧凑度分数（0~1，圆形=1）。
    """
    if mask.dtype != bool:
        mask = mask > 0

    mask_u8 = (mask.astype(np.uint8)) * 255
    contours, _ = cv2.findContours(
        mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    area = float(mask.sum())
    perimeter = sum(cv2.arcLength(c, True) for c in contours)

    if perimeter == 0:
        return 0.0

    return float((4 * np.pi * area) / (perimeter * perimeter))
