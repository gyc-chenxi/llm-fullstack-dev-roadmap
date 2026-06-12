import os
import platform
import torch

def select_device(requested: str = "auto") -> str:
    if requested and requested != "auto":
        return requested

    if torch.cuda.is_available():
        return "cuda"

    if torch.backends.mps.is_available():
        return "mps"

    return "cpu"

def select_dtype(dtype_name: str, device: str):
    if dtype_name == "float16":
        return torch.float16
    if dtype_name == "float32":
        return torch.float32

    # Apple Silicon stable default for this project.
    if device == "mps":
        return torch.float32

    if device == "cuda":
        return torch.float16

    return torch.float32

def apply_runtime_env():
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

def device_report() -> dict:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "mps_built": torch.backends.mps.is_built(),
        "mps_available": torch.backends.mps.is_available(),
        "cuda_available": torch.cuda.is_available(),
        "mps_fallback": os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK"),
    }
