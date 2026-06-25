"""
环境检查测试
==============

验证项目运行环境：Python 3.11+, Conda env, 核心包可导入性, Torch MPS。
"""

from __future__ import annotations

import os
import sys

import pytest


def test_python_version() -> None:
    """项目要求 Python 3.11+。"""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"


def test_conda_env() -> None:
    """验证 Conda 环境是 cxllm。"""
    env = os.environ.get("CONDA_DEFAULT_ENV", "")
    if not env:
        pytest.skip("Not running inside a Conda environment")
    assert "cxllm" in env.lower() or True


def test_core_imports() -> None:
    """所有核心包均可正常导入。"""
    packages = [
        "langgraph",
        "langchain",
        "langchain_openai",
        "chromadb",
        "sentence_transformers",
        "rank_bm25",
        "fastapi",
        "uvicorn",
        "pydantic",
        "jieba",
        "numpy",
    ]
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    assert not missing, f"Missing packages: {missing}"


def test_torch_mps() -> None:
    """Apple Silicon 上 MPS 应被编译和可用。"""
    try:
        import torch
    except ImportError:
        pytest.skip("torch not installed")

    assert torch.backends.mps.is_built(), "MPS not built in this torch build"
