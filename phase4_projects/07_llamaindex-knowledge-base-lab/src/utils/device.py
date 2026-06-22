"""Apple Silicon MPS 设备检测与内存监控."""

import torch
import platform
import subprocess


def detect_device() -> str:
    """检测最优可用设备，优先 MPS。

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

    Returns:
        {"total_gb": float, "used_gb": float, "pressure": str}
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
    """打印设备信息摘要。"""
    device = detect_device()
    print(f"Compute Device : {device.upper()}")

    if device == "mps":
        print(f"PyTorch MPS    : built={torch.backends.mps.is_built()}, "
              f"available={torch.backends.mps.is_available()}")

    mem = get_memory_info()
    print(f"Unified Memory : {mem['total_gb']} GB total, {mem['used_gb']} GB used")
    print(f"Memory Pressure: {mem['pressure']}")
