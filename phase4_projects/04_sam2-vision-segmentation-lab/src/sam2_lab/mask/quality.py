from __future__ import annotations

import cv2
import numpy as np


def mask_quality_report(mask: np.ndarray) -> dict:
    """生成 mask 质量报告：面积、连通域、孔洞、边缘复杂度。"""
    if mask.dtype != np.bool_:
        mask = mask > 0

    mask_u8 = (mask.astype(np.uint8) * 255)

    contours, hierarchy = cv2.findContours(
        mask_u8,
        cv2.RETR_CCOMP,
        cv2.CHAIN_APPROX_SIMPLE,
    )

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