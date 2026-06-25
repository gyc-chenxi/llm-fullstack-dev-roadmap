"""
单元测试：Mask 质量报告
=======================

测试范围：
  - mask_quality_report() 返回 dict 包含约定字段
  - 面积计算准确（10×10 = 100 px）
  - 纯方块无孔洞

测试策略：
  创建已知形状的 mask，验证质量报告的数值计算准确性。
"""

import numpy as np

from sam2_lab.mask.quality import mask_quality_report


def test_mask_quality_report():
    """创建一个 20x20 背景中的 10x10 方块 mask，验证质量和面积计算。"""
    mask = np.zeros((20, 20), dtype=np.bool_)
    mask[5:15, 5:15] = True

    report = mask_quality_report(mask)

    assert "area_px" in report
    assert report["area_px"] == 100  # 10 × 10 = 100 像素
    assert report["hole_count"] == 0  # 纯心方块，没有孔洞