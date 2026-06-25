"""
设备检测与运行时配置
======================

设备选择策略（Apple Silicon MBP 优先）：
  1. MPS (Metal Performance Shaders) — Apple Silicon GPU 推理
     优点：利用统一内存，省去 CPU↔GPU 数据搬运开销
     局限：部分算子不支持 float16（如 CUDA 特有的 flash_attn），需开启 MPS_FALLBACK
  2. CUDA — NVIDIA GPU，支持 float16 + flash_attention
  3. CPU — 纯推理保底，使用 float32 以保证数值精度

dtype 选择：
  - MPS/CUDA → float16（速度优先，显存/统一内存减半）
  - CPU      → float32（精度优先，CPU 上 float16 无明显加速）

运行时环境变量：
  - PYTORCH_ENABLE_MPS_FALLBACK=1：MPS 不支持的算子自动回退 CPU
  - TOKENIZERS_PARALLELISM=false：避免 fork 子进程导致 MPS 共享内存冲突
"""

from __future__ import annotations

import os

import torch


def get_best_device() -> str:
    """按 MPS > CUDA > CPU 优先级返回可用计算设备。"""
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_dtype(device: str) -> torch.dtype:
    """根据设备选择推理精度：GPU/MPS 用 float16 加速，CPU 用 float32 保精度。"""
    if device == "mps":
        return torch.float16
    if device == "cuda":
        return torch.float16
    return torch.float32


def configure_runtime() -> None:
    """设置 MPS 推理的安全运行环境，避免算子和多进程冲突。"""
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
