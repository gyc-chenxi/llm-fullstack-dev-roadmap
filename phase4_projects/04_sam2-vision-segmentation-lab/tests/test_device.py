import torch

from sam2_lab.device import get_device, get_torch_dtype


def test_get_device():
    device = get_device()
    # 验证设备返回的是支持的三种之一
    assert device in ["mps", "cuda", "cpu"]

def test_get_torch_dtype():
    # 验证在 Mac MPS 环境下默认使用 float32
    dtype = get_torch_dtype("mps")
    assert dtype == torch.float32