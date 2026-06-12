from __future__ import annotations

import torch


def get_device(preferred: str = "auto") -> str:
    if preferred != "auto":
        return preferred
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

def get_torch_dtype(device: str):
    if device == "cuda":
        return torch.float16
    # MPS 对部分 float16 算子支持仍可能不完整，学习项目默认 float32 更稳
    if device == "mps":
        return torch.float32
    return torch.float32