"""
Mask 可视化工具
--------------
生成 mask 的多种可视化：彩色 overlay、轮廓绘制、多 mask 分色显示等。
"""
from __future__ import annotations

import cv2
import numpy as np


def draw_contours(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """在 BGR 原图上绘制 mask 的轮廓线。

    Args:
        image_bgr: BGR 格式原图。
        mask: bool 类型 mask。
        color: 轮廓颜色（BGR）。
        thickness: 线宽。

    Returns:
        带轮廓的 BGR 图像。
    """
    if mask.dtype != bool:
        mask_bool = mask > 127
    else:
        mask_bool = mask

    mask_u8 = (mask_bool.astype(np.uint8)) * 255
    contours, _ = cv2.findContours(
        mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    result = image_bgr.copy()
    cv2.drawContours(result, contours, -1, color, thickness)
    return result


def colorize_masks(
    masks: list[np.ndarray],
    colors: list[tuple[int, int, int]] | None = None,
) -> np.ndarray:
    """将多个 mask 渲染为不同颜色的单张图像（用于全自动分割可视化）。

    Args:
        masks: bool mask 列表。
        colors: 对应的 BGR 颜色列表（不提供则自动生成 10 种颜色）。

    Returns:
        BGR 彩色 mask 图像。
    """
    if not masks:
        return np.zeros((1, 1, 3), dtype=np.uint8)

    if colors is None:
        colors = [
            (0, 0, 255),    # 红
            (0, 255, 0),    # 绿
            (255, 0, 0),    # 蓝
            (0, 255, 255),  # 黄
            (255, 0, 255),  # 紫
            (255, 255, 0),  # 青
            (128, 0, 255),  # 橙
            (0, 128, 255),  # 天蓝
            (255, 128, 0),  # 蓝绿
            (128, 255, 0),  # 黄绿
        ]

    h, w = masks[0].shape[:2]
    result = np.zeros((h, w, 3), dtype=np.uint8)

    for i, mask in enumerate(masks):
        if mask.dtype != bool:
            mask_bool = mask > 127
        else:
            mask_bool = mask
        color = colors[i % len(colors)]
        result[mask_bool] = color

    return result


def overlay_mask(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    color: tuple[int, int, int] = (0, 255, 0),
    alpha: float = 0.5,
) -> np.ndarray:
    """在 BGR 原图上叠加彩色半透明 mask。

    Args:
        image_bgr: BGR 格式原图。
        mask: bool 类型 mask。
        color: mask 填充颜色（BGR）。
        alpha: 透明度（0=完全透明, 1=完全不透明）。

    Returns:
        叠加后的 BGR 图像。
    """
    if mask.dtype != bool:
        mask_bool = mask > 127
    else:
        mask_bool = mask

    overlay = image_bgr.copy()
    color_arr = np.array(color, dtype=np.uint8)
    overlay[mask_bool] = (
        overlay[mask_bool] * (1 - alpha) + color_arr * alpha
    )
    return overlay
