"""
设备选择与精度管理
================

关注点（面试问答）：
  1. Apple Silicon (MPS) 上 float16 支持不完整——
    某些算子（如 GroupNorm）在 float16 下会崩溃，
    所以 MPS 默认回退到 float32。
  2. CUDA 设备上 float16 通常又快又省显存，
    是生产环境的首选。

设备选择优先级：
  auto → CUDA (优先) → MPS (Apple Silicon) → CPU (兜底)

数据类型选择逻辑：
  显式指定 → 使用指定的类型
  auto:
    - MPS → float32（兼容性优先）
    - CUDA → float16（性能优先）
    - CPU → float32
"""

import os
import platform
import torch


def select_device(requested: str = "auto") -> str:
    """
    自动选择最佳可用计算设备。

    优先级策略：
      cuda > mps > cpu

    参数：
      requested: "auto" 或具体设备名（如 "cuda", "mps", "cpu"）

    返回：
      str — 设备名，如 "cuda"、"mps"、"cpu"
    """
    if requested and requested != "auto":
        return requested

    if torch.cuda.is_available():
        return "cuda"

    if torch.backends.mps.is_available():
        return "mps"

    return "cpu"


def select_dtype(dtype_name: str, device: str):
    """
    根据设备和配置选择 torch 数据类型。

    参数：
      dtype_name: "float16"、"float32" 或 "auto"
      device: 当前计算设备（"cuda"、"mps"、"cpu"）

    返回：
      torch.dtype — 推理使用的数据类型

    注意：
      MPS + float16 在 Apple Silicon 上存在算子兼容性问题，
      因此 MPS 默认使用 float32 确保稳定性。
    """
    if dtype_name == "float16":
        return torch.float16
    if dtype_name == "float32":
        return torch.float32

    # Apple Silicon 稳定默认值
    if device == "mps":
        return torch.float32

    if device == "cuda":
        return torch.float16

    return torch.float32


def apply_runtime_env():
    """
    设置运行时环境变量。
    在构建模型前调用，确保各后端兼容性。

    PYTORCH_ENABLE_MPS_FALLBACK=1：
      允许 MPS 上不支持的算子回退到 CPU 执行，
      避免因缺少算子导致崩溃。
    """
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")


def device_report() -> dict:
    """
    生成本地设备能力报告（调试/日志用途）。

    返回：
      {
        "python": "3.11.5",
        "platform": "macOS-14.0-arm64-arm-64bit",
        "torch": "2.3.0",
        "mps_built": true,
        "mps_available": true,
        "cuda_available": false,
        "mps_fallback": "1"
      }
    """
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "mps_built": torch.backends.mps.is_built(),
        "mps_available": torch.backends.mps.is_available(),
        "cuda_available": torch.cuda.is_available(),
        "mps_fallback": os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK"),
    }