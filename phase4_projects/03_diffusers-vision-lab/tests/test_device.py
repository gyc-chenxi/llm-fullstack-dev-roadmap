from diffusers_lab.device import select_dtype
import torch

def test_mps_default_float32_when_requested():
    assert select_dtype("float32", "mps") == torch.float32

def test_cuda_float16_when_requested():
    assert select_dtype("float16", "cuda") == torch.float16
