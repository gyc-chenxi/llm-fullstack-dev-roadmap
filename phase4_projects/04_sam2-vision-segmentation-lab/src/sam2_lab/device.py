"""
设备与精度选择
==============

检测并返回最佳可用计算设备（mps > cuda > cpu），
以及对应设备推荐的 torch 数据类型。

设备选择优先级：
  user specified → mps (Apple Silicon) → cuda (NVIDIA) → cpu (兜底)

数据类型说明：
  - CUDA: float16 更快且节省显存，是默认选型
  - MPS: float32 更稳定（Apple Silicon 上 float16 某些算子不兼容）
  - CPU: float32（float16 在 CPU 上无加速优势）

数据流：
  get_device("auto") → 自动检测 → 返回 "mps" / "cuda" / "cpu"
    ↓
  get_torch_dtype(device) → 返回 torch.float16 / torch.float32
    ↓
  传递给 SAM2 模型的 .to(device) 和 from_pretrained(torch_dtype=...)
"""

from __future__ import annotations

import torch


def get_device(preferred: str = "auto") -> str:
    """
    自动选择最佳推理设备。

    参数：
      preferred: "auto" 或具体设备名

    返回：
      str — "mps"、"cuda" 或 "cpu"
    """
    if preferred != "auto":
        return preferred
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_torch_dtype(device: str):
    """
    根据设备返回推荐的 torch 数据类型。

    参数：
      device: 目标设备（"cuda"、"mps"、"cpu"）

    返回：
      torch.dtype — float16 (CUDA) 或 float32 (MPS/CPU)
    """
    if device == "cuda":
        return torch.float16
    # MPS 对部分 float16 算子支持仍可能不完整，学习项目默认 float32 更稳
    if device == "mps":
        return torch.float32
    return torch.float32