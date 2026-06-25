"""
Mask 质量评估报告
=================

对分割结果进行量化评估，生成面积、连通域、孔洞数量、
边缘复杂度等关键指标，用于比较不同 prompt/参数的效果。

质量指标说明：
  - area_px: mask 总前景像素面积
  - connected_components: 连通域数量（1 为理想值，>1 表示碎片化）
  - largest_component_area_px: 最大连通域的面积
  - largest_area_ratio: 最大连通域占比（接近 1 表示 mask 紧凑）
  - hole_count: mask 内部的孔洞数量（0 为理想值）
  - edge_points: 边缘轮廓上的像素点数（越大表示边界越复杂）

数据流：
  mask [H, W] (bool) → mask_quality_report()
    → cv2.findContours(RETR_CCOMP) → 检测外部+内部轮廓（孔洞）
    → cv2.findContours(RETR_EXTERNAL) → 边缘复杂度
    → cv2.connectedComponentsWithStats() → 连通域分析
    → 返回 dict（6项指标）
"""

from __future__ import annotations

import cv2
import numpy as np


def mask_quality_report(mask: np.ndarray) -> dict:
    """
    生成 mask 质量报告：面积、连通域、孔洞、边缘复杂度。

    参数：
      mask: bool 类型 mask 数组，形状 (H, W)

    返回：
      {
        "area_px": int,                  # 总前景像素数
        "connected_components": int,      # 连通域个数（理想=1）
        "largest_component_area_px": int, # 最大连通域面积
        "hole_count": int,               # 孔洞个数（理想=0）
        "edge_points": int,              # 边缘轮廓点数
        "largest_area_ratio": float      # 最大域占比（理想≈1.0）
      }
    """
    if mask.dtype != np.bool_:
        mask = mask > 0

    mask_u8 = (mask.astype(np.uint8) * 255)

    # RETR_CCOMP: 检测所有轮廓并组织成两级层次结构
    # 外层轮廓 = mask 边界，内层轮廓 = 孔洞边界
    contours, hierarchy = cv2.findContours(
        mask_u8,
        cv2.RETR_CCOMP,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    # RETR_EXTERNAL: 仅检测最外层轮廓（用于计算边缘复杂度）
    external_contours, _ = cv2.findContours(
        mask_u8,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    connected_count, _, stats, _ = cv2.connectedComponentsWithStats(mask_u8)

    areas = [
        int(stats[i, cv2.CC_STAT_AREA])
        for i in range(1, connected_count)
    ]

    largest_area = max(areas) if areas else 0
    total_area = int(mask.sum())

    # 统计孔洞：在 RETR_CCOMP 层次结构中，
    # 有父轮廓（parent != -1）的轮廓即为孔洞
    hole_count = 0
    if hierarchy is not None:
        for h in hierarchy[0]:
            parent = h[3]
            if parent != -1:
                hole_count += 1

    edge_points = sum(len(c) for c in external_contours)

    return {
        "area_px": total_area,
        "connected_components": max(connected_count - 1, 0),
        "largest_component_area_px": largest_area,
        "hole_count": hole_count,
        "edge_points": int(edge_points),
        "largest_area_ratio": round(largest_area / total_area, 4) if total_area else 0,
    }