"""
环境信息检查脚本
==================

打印关键库的版本和设备可用性，用于快速诊断运行环境：
  - Python 版本（>=3.11 才能启用 MPS 全功能）
  - PyTorch / Transformers 版本
  - MPS is_available（是否可用）/ is_built（是否编译了 MPS 支持）

用法：PYTHONPATH=src python scripts/print_env.py
"""

import platform

import torch
import transformers

print("python:", platform.python_version())
print("platform:", platform.platform())
print("torch:", torch.__version__)
print("transformers:", transformers.__version__)
print("mps available:", torch.backends.mps.is_available())
print("mps built:", torch.backends.mps.is_built())
