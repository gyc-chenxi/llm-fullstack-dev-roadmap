"""
单元测试：设备与精度选择
========================

测试范围：
  - select_dtype() 在不同设备和请求精度下的正确返回值
  - 不测试 select_device()（因为测试环境 GPU 不可用时跳过）

测试策略：
  纯逻辑测试，不依赖硬件。只验证 select_dtype 的映射逻辑：
    - 显式指定 float32 → MPS 回退到 float32
    - 显式指定 float16 → CUDA 使用 float16
"""

from diffusers_lab.device import select_dtype
import torch


def test_mps_default_float32_when_requested():
    """MPS + float32 显式指定 → 返回 torch.float32"""
    assert select_dtype("float32", "mps") == torch.float32


def test_cuda_float16_when_requested():
    """CUDA + float16 显式指定 → 返回 torch.float16"""
    assert select_dtype("float16", "cuda") == torch.float16