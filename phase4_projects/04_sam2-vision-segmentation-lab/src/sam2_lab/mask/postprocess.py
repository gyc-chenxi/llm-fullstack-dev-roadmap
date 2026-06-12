from __future__ import annotations

import cv2
import numpy as np


def postprocess_mask(
    mask: np.ndarray,
    min_area: int = 500,
    kernel_size: int = 5,
) -> np.ndarray:
    """二值化、去噪、填孔、连通域过滤。"""
    if mask.dtype != np.bool_:
        mask = mask > 0

    mask_u8 = (mask.astype(np.uint8) * 255)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )

    opened = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed)
    result = np.zeros_like(closed)

    for idx in range(1, num_labels):
        area = stats[idx, cv2.CC_STAT_AREA]
        if area >= min_area:
            result[labels == idx] = 255

    return result > 0