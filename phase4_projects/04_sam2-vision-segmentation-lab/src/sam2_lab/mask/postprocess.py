"""
Mask 后处理工具
===============

对 SAM2 输出的原始 mask 进行后处理，提升质量：
  1. 二值化（将 logit/float mask 转为 bool）
  2. 形态学开运算（MORPH_OPEN = 腐蚀→膨胀）：移除小噪点
  3. 形态学闭运算（MORPH_CLOSE = 膨胀→腐蚀）：填充小孔洞
  4. 连通域过滤：移除面积小于 min_area 的孤立碎片

数据流：
  mask [H, W] (float/bool) → 二值化 [H, W] (bool)
    → MORPH_OPEN → MORPH_CLOSE → 连通域过滤
    → 输出 mask [H, W] (bool)
"""

from __future__ import annotations

import cv2
import numpy as np


def postprocess_mask(
    mask: np.ndarray,
    min_area: int = 500,
    kernel_size: int = 5,
) -> np.ndarray:
    """
    二值化、去噪、填孔、连通域过滤。

    参数：
      mask: 原始 mask 数组（float 或 bool 类型），形状 (H, W)
      min_area: 最小连通域面积（像素），小于此值的碎片被移除
      kernel_size: 形态学操作核大小，越大去噪/填孔力度越强

    返回：
      bool 类型后处理 mask，形状 (H, W)

    典型参数：
      - 简单场景: min_area=500, kernel_size=5
      - 复杂场景（更多噪点）: min_area=1000, kernel_size=7
    """
    if mask.dtype != np.bool_:
        mask = mask > 0

    mask_u8 = (mask.astype(np.uint8) * 255)

    # 椭圆结构元素：比矩形核更平滑，保留自然边界的细节
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )

    # 开运算：先腐蚀后膨胀 → 移除小噪点
    opened = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
    # 闭运算：先膨胀后腐蚀 → 填充小孔洞
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    # 连通域过滤：仅保留面积 ≥ min_area 的连通分量
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed)
    result = np.zeros_like(closed)

    for idx in range(1, num_labels):
        area = stats[idx, cv2.CC_STAT_AREA]
        if area >= min_area:
            result[labels == idx] = 255

    return result > 0