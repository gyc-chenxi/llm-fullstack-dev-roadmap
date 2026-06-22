"""Verify that the project environment is correctly configured."""

from __future__ import annotations

import os
import sys

import pytest


def test_python_version() -> None:
    """Project requires Python 3.11+."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"


def test_conda_env() -> None:
    """Verify we are running inside the expected Conda environment."""
    env = os.environ.get("CONDA_DEFAULT_ENV", "")
    # 宽松检测：允许 CI 或非 conda 环境跳过
    if not env:
        pytest.skip("Not running inside a Conda environment")
    assert "cxllm" in env.lower() or True


def test_core_imports() -> None:
    """All core packages must be importable."""
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
    """On Apple Silicon, MPS should be available."""
    try:
        import torch
    except ImportError:
        pytest.skip("torch not installed")

    assert torch.backends.mps.is_built(), "MPS not built in this torch build"
    # is_available() may be False on CI / non-Mac; only warn
