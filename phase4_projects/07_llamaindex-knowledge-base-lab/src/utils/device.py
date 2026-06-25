"""
Apple Silicon MPS 设备检测与内存监控
======================================

设备选择策略（Apple Silicon 优先）：
  MPS (Metal Performance Shaders) > CUDA > CPU

内存监控（仅 macOS）：
  通过 vm_stat 获取统一内存页使用情况，计算压力等级：
    - normal (<50%): 正常
    - warning (50-75%): 建议减少 batch_size
    - critical (>75%): 内存紧张，可能触发 swap

Apple Silicon 页大小：16KB（统一内存架构特有）
"""

import platform
import subprocess

import torch


def detect_device() -> str:
    """按 MPS > CUDA > CPU 优先级返回可用计算设备。

    Returns:
        "mps" / "cuda" / "cpu"
    """
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_memory_info() -> dict:
    """获取统一内存使用情况（仅 macOS）。

    通过解析 vm_stat 输出计算内存压力。
    非 macOS 平台返回 unknown。
    """
    if platform.system() != "Darwin":
        return {"total_gb": 0, "used_gb": 0, "pressure": "unknown"}

    try:
        result = subprocess.run(
            ["vm_stat"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        info = {}
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                val = val.strip().rstrip(".")
                try:
                    info[key.strip()] = int(val)
                except ValueError:
                    pass

        page_size = 16384  # Apple Silicon 页大小 16KB
        free_pages = info.get("Pages free", 0)
        total_pages = sum(
            v for k, v in info.items()
            if k in ("Pages free", "Pages active", "Pages inactive",
                      "Pages speculative", "Pages wired down")
        )
        used_pages = total_pages - free_pages
        total_gb = (total_pages * page_size) / (1024**3)
        used_gb = (used_pages * page_size) / (1024**3)

        ratio = used_pages / total_pages if total_pages > 0 else 0
        if ratio < 0.5:
            pressure = "normal"
        elif ratio < 0.75:
            pressure = "warning"
        else:
            pressure = "critical"

        return {"total_gb": round(total_gb, 1), "used_gb": round(used_gb, 1), "pressure": pressure}
    except Exception:
        return {"total_gb": 32.0, "used_gb": 0, "pressure": "unknown"}


def print_device_info():
    """打印设备信息摘要（用于构建/查询脚本启动时）。"""
    device = detect_device()
    print(f"Compute Device : {device.upper()}")

    if device == "mps":
        print(f"PyTorch MPS    : built={torch.backends.mps.is_built()}, "
              f"available={torch.backends.mps.is_available()}")

    mem = get_memory_info()
    print(f"Unified Memory : {mem['total_gb']} GB total, {mem['used_gb']} GB used")
    print(f"Memory Pressure: {mem['pressure']}")
