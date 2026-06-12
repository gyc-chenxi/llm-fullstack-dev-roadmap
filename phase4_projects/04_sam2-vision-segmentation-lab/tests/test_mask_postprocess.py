import numpy as np

from sam2_lab.mask.postprocess import postprocess_mask


def test_postprocess_mask():
    # 创建一个 20x20 的全黑背景
    mask = np.zeros((20, 20), dtype=np.bool_)
    # 在中间画一个 10x10 的白色方块作为模拟 Mask
    mask[5:15, 5:15] = True
    
    # 运行后处理（去噪、连通域过滤）
    result = postprocess_mask(mask, min_area=10, kernel_size=3)
    
    assert result.shape == (20, 20)
    assert result.any()  # 确保处理后并没有把正常的图形给误删掉