"""
SAM 2 全自动 Mask 生成
---------------------
封装 SAM2AutomaticMaskGenerator，为调用方提供简化的全自动分割接口。
"""
from __future__ import annotations

import numpy as np
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator


def generate_masks(
    image_rgb: np.ndarray,
    mask_generator: SAM2AutomaticMaskGenerator,
    top_k: int | None = 10,
    sort_by_area: bool = True,
) -> list[dict]:
    """对一张图片执行全自动分割。

    Args:
        image_rgb: RGB 格式的 numpy 数组 (H, W, 3)。
        mask_generator: 已初始化的 SAM2AutomaticMaskGenerator。
        top_k: 返回前 k 个最大的 mask（None 表示返回全部）。
        sort_by_area: 是否按面积降序排列。

    Returns:
        mask 字典列表，每个字典包含:
            - segmentation: bool numpy 数组 (H, W)
            - area: int 面积（像素）
            - bbox: [x, y, w, h]
            - predicted_iou: float
            - stability_score: float
            - point_coords: [x, y] 生成该 mask 的采样点
    """
    masks = mask_generator.generate(image_rgb)

    if sort_by_area:
        masks = sorted(masks, key=lambda m: m["area"], reverse=True)

    if top_k is not None:
        masks = masks[:top_k]

    return masks
