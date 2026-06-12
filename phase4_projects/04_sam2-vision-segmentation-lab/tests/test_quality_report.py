import numpy as np

from sam2_lab.mask.quality import mask_quality_report


def test_mask_quality_report():
    # 创建一个模拟的 10x10 方块 Mask
    mask = np.zeros((20, 20), dtype=np.bool_)
    mask[5:15, 5:15] = True
    
    # 运行质量检测
    report = mask_quality_report(mask)
    
    # 验证报告输出的格式和计算准确性
    assert "area_px" in report
    assert report["area_px"] == 100  # 10 * 10 = 100 像素
    assert report["hole_count"] == 0 # 纯心方块，没有孔洞