from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


def main() -> None:
    print("=" * 80)
    print("[env] Python / Conda / Apple Silicon check")
    print("=" * 80)

    print("Python:", sys.version.replace("\n", " "))
    print("Executable:", sys.executable)
    print("Platform:", platform.platform())
    print("Machine:", platform.machine())
    print("Conda env:", os.environ.get("CONDA_DEFAULT_ENV"))
    print("Project root:", Path.cwd())

    assert os.environ.get("CONDA_DEFAULT_ENV") == "cxllm", (
        "必须在 cxllm 环境中运行：conda activate cxllm"
    )

    print("\n" + "=" * 80)
    print("[env] Tooling check")
    print("=" * 80)

    for name in ["cmake", "ninja", "hf"]:
        path = shutil.which(name)
        print(f"{name}:", path or "NOT FOUND")

    print("\n" + "=" * 80)
    print("[env] Python package check")
    print("=" * 80)

    try:
        import torch

        print("Torch:", torch.__version__)
        print("MPS available:", torch.backends.mps.is_available())
        print("MPS built:", torch.backends.mps.is_built())
    except Exception as exc:
        print("Torch check failed:", repr(exc))

    packages = [
        "langgraph",
        "langchain",
        "langchain_openai",
        "chromadb",
        "sentence_transformers",
        "rank_bm25",
        "fastapi",
        "uvicorn",
    ]

    for pkg in packages:
        try:
            __import__(pkg)
            print(f"{pkg}: OK")
        except Exception as exc:
            print(f"{pkg}: FAILED -> {exc!r}")

    print("\n[done] environment check completed")


if __name__ == "__main__":
    main()