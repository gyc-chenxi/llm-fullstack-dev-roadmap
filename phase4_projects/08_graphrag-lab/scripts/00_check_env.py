#!/usr/bin/env python3
"""P8 GraphRAG Lab — Environment Self-Check.

Run before any other step to verify:
- Python 3.11+, Conda cxllm, PyTorch MPS, GraphRAG installed
- .env with real API key (not placeholder)
- HuggingFace mirror configured
- Required directories exist
"""

import os
import sys
import shutil
import platform


def check(desc: str, ok: bool, detail: str = "") -> bool:
    symbol = "\033[92mPASS\033[0m" if ok else "\033[91mFAIL\033[0m"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{symbol}] {desc}{suffix}")
    return ok


def main() -> int:
    print("=" * 60)
    print("P8 GraphRAG Lab — Environment Check")
    print(f"Platform: {platform.platform()}")
    print(f"Time:     {__import__('datetime').datetime.now().isoformat()}")
    print("=" * 60)

    all_ok = True

    # --- Python ---
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    all_ok &= check(f"Python {py_ver}", sys.version_info >= (3, 11))

    # --- Conda ---
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "?")
    all_ok &= check(f"Conda env: {conda_env}", conda_env == "cxllm",
                    detail="OK" if conda_env == "cxllm" else f"expected=cxllm, got={conda_env}")

    # --- PyTorch + MPS ---
    try:
        import torch
        all_ok &= check(f"PyTorch {torch.__version__}", True)
        mps_ok = torch.backends.mps.is_available()
        all_ok &= check("MPS available", mps_ok)
        if mps_ok:
            try:
                x = torch.randn(2, 2).to("mps")
                y = x @ x
                all_ok &= check("MPS matmul", True, f"device={x.device}, shape={y.shape}")
            except Exception as e:
                all_ok &= check("MPS matmul", False, str(e)[:60])
    except ImportError:
        all_ok &= check("PyTorch", False, "not installed — run: conda run -n cxllm pip install torch")

    # --- GraphRAG ---
    try:
        import graphrag
        all_ok &= check(f"GraphRAG {graphrag.__version__}", True)
    except ImportError:
        all_ok &= check("GraphRAG", False, "not installed — run: conda run -n cxllm pip install graphrag")

    # --- sentence-transformers ---
    try:
        import sentence_transformers
        all_ok &= check(f"sentence-transformers {sentence_transformers.__version__}", True)
    except ImportError:
        all_ok &= check("sentence-transformers", False)

    # --- chromadb ---
    try:
        import chromadb
        all_ok &= check(f"chromadb {chromadb.__version__}", True)
    except ImportError:
        all_ok &= check("chromadb", False)

    # --- fastapi + uvicorn ---
    try:
        import fastapi
        import uvicorn
        all_ok &= check(f"fastapi {fastapi.__version__}", True)
    except ImportError:
        all_ok &= check("fastapi/uvicorn", False)

    # --- .env + API key ---
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_file = os.path.abspath(env_file)
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)
        key = os.environ.get("GRAPHRAG_API_KEY", "")
        has_key = len(key) > 10 and "your-deepseek" not in key.lower()
        all_ok &= check(".env GRAPHRAG_API_KEY", has_key,
                        "set" if has_key else "placeholder — edit .env with real key")
    else:
        all_ok &= check(".env file", False, f"not found at {env_file} — run: cp .env.example .env")

    # --- HF_ENDPOINT ---
    hf = os.environ.get("HF_ENDPOINT", "")
    all_ok &= check("HF_ENDPOINT", "hf-mirror.com" in hf, hf or "not set")

    # --- disk ---
    total, used, free = shutil.disk_usage(".")
    free_gb = free / (1024 ** 3)
    all_ok &= check(f"Disk free: {free_gb:.1f} GB", free_gb > 10,
                    "OK" if free_gb > 10 else "WARNING: <10GB free")

    # --- directories ---
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for d in ["data/raw", "data/input", "data/output", "data/vector_store",
              "configs", "scripts", "src/graphrag_lab", "tests", "prompts", "docs", "logs"]:
        full = os.path.join(project_root, d)
        exists = os.path.isdir(full)
        n = 0
        if exists:
            try:
                n = len([f for f in os.listdir(full) if not f.startswith(".")])
            except Exception:
                n = -1
        all_ok &= check(f"Directory: {d}/", exists, f"{n} files" if n else "empty")

    # --- verdict ---
    print("=" * 60)
    if all_ok:
        print("\033[92mALL CHECKS PASSED — ready to proceed.\033[0m")
    else:
        print("\033[91mSOME CHECKS FAILED — fix issues above before continuing.\033[0m")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
