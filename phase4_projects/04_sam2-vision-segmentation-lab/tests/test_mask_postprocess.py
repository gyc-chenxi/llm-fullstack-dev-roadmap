"""
单元测试：Mask 后处理
======================

测试范围：
  - postprocess_mask() 能正确过滤同尺寸的模拟 mask
  - 确保后处理不会误删有效的大面积 mask

测试策略：
  创建一个 10×10 的方块模拟 mask，运行后处理：
  - 结果尺寸与原 mask 一致
  - 有效 mask 区域未被误删
"""

import numpy as np

from sam2_lab.mask.postprocess import postprocess_mask


def test_postprocess_mask():
    """创建一个 20x20 全黑背景，中间画 10x10 白色方块作为模拟 mask。"""
    mask = np.zeros((20, 20), dtype=np.bool_)
    mask[5:15, 5:15] = True

    result = postprocess_mask(mask, min_area=10, kernel_size=3)

    assert result.shape == (20, 20)
    assert result.any()  # 确保处理后没有把有效图形误删