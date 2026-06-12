"""
常用图像 I/O 工具
----------------
封装 OpenCV / PIL 的读取和写入操作，统一 BGR↔RGB 转换。
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def load_image_rgb(path: str | Path) -> np.ndarray:
    """加载图片并转换为 RGB 格式。

    Args:
        path: 图片路径。

    Returns:
        RGB 格式 numpy 数组 (H, W, 3)。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 无法解码。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"图片不存在: {path}")

    img_bgr = cv2.imread(str(path))
    if img_bgr is None:
        raise ValueError(f"无法解码图片: {path}")

    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def load_image_bgr(path: str | Path) -> np.ndarray:
    """加载图片为 BGR 格式（OpenCV 原生格式）。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"图片不存在: {path}")

    img_bgr = cv2.imread(str(path))
    if img_bgr is None:
        raise ValueError(f"无法解码图片: {path}")

    return img_bgr


def save_mask(mask: np.ndarray, path: str | Path) -> None:
    """将 bool 或 uint8 mask 保存为 PNG 图片。

    Args:
        mask: bool 或 uint8 类型的 mask 数组。
        path: 输出路径。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if mask.dtype == bool:
        mask_u8 = (mask.astype(np.uint8)) * 255
    else:
        mask_u8 = mask

    cv2.imwrite(str(path), mask_u8)


def save_overlay(
    image_bgr: np.ndarray,
    mask: np.ndarray,
    path: str | Path,
    color: tuple[int, int, int] = (0, 255, 0),
    alpha: float = 0.5,
) -> None:
    """在 BGR 原图上叠加彩色半透明 mask 并保存。

    Args:
        image_bgr: BGR 格式原图。
        mask: bool 类型 mask。
        path: 输出路径。
        color: mask 覆盖颜色（BGR）。
        alpha: mask 透明度。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if mask.dtype != bool:
        mask_bool = mask > 127
    else:
        mask_bool = mask

    overlay = image_bgr.copy()
    color_arr = np.array(color, dtype=np.uint8)
    overlay[mask_bool] = (
        overlay[mask_bool] * (1 - alpha) + color_arr * alpha
    )

    cv2.imwrite(str(path), overlay)


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """PIL RGB → OpenCV BGR。"""
    rgb = np.array(pil_image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def cv2_to_pil(img_bgr: np.ndarray) -> Image.Image:
    """OpenCV BGR → PIL RGB。"""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)
