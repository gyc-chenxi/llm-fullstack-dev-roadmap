"""
单元测试：设备检测
===================

测试范围：
  - get_device() 返回三种合法设备之一
  - get_torch_dtype("mps") 默认返回 float32

测试策略：
  纯逻辑测试，不依赖特定硬件。只验证返回值的类型合法性。
"""

import torch

from sam2_lab.device import get_device, get_torch_dtype


def test_get_device():
    """验证设备返回的是支持的三种值之一。"""
    device = get_device()
    assert device in ["mps", "cuda", "cpu"]


def test_get_torch_dtype():
    """
    验证 MPS 环境下默认使用 float32。
    Apple Silicon 上 float16 存在算子兼容性风险。
    """
    dtype = get_torch_dtype("mps")
    assert dtype == torch.float32