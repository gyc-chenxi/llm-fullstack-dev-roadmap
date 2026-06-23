#!/usr/bin/env python3
"""Initialize GraphRAG project.

Steps performed:
1. Copy .env.example → .env (if .env doesn't exist)
2. Validate GRAPHRAG_API_KEY is set (warn if placeholder)
3. Copy configs/settings.yaml → settings.yaml (project root)
4. Verify data/input/ has .txt files
5. Ensure output/logs/cache directories exist

Usage:
    PYTHONPATH=. python scripts/03_init_graphrag.py
    or: make init-graphrag
"""

import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent


def main():
    os.chdir(PROJECT_DIR)
    print(f"[init] Project root: {PROJECT_DIR}")
    print()

    # --- Step 1: .env ---
    env_example = PROJECT_DIR / ".env.example"
    env_file = PROJECT_DIR / ".env"

    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("[init] ✓ Created .env from .env.example")
            print("[init] !!! ACTION REQUIRED: edit .env and set GRAPHRAG_API_KEY !!!")
            print("[init]    Get key at: https://platform.deepseek.com/api_keys")
            print("[init]    Then re-run: make init-graphrag")
        else:
            print("[init] ✗ ERROR: .env.example not found — cannot create .env")
            sys.exit(1)
    else:
        print("[init] ✓ .env already exists")

    # --- Step 2: Validate API key ---
    load_dotenv(env_file)
    api_key = os.environ.get("GRAPHRAG_API_KEY", "")
    if not api_key:
        print("[init] ✗ WARNING: GRAPHRAG_API_KEY is EMPTY — indexing will fail!")
        print("[init]    Edit .env and add your DeepSeek API key.")
    elif "your-deepseek" in api_key.lower() or len(api_key) < 10:
        print("[init] ✗ WARNING: GRAPHRAG_API_KEY appears to be a placeholder!")
        print(f"[init]    Current value: {api_key[:20]}...")
        print("[init]    Replace with a real key from https://platform.deepseek.com/api_keys")
    else:
        print(f"[init] ✓ GRAPHRAG_API_KEY: {api_key[:8]}...{api_key[-4:]}")

    # --- Step 3: settings.yaml ---
    settings_src = PROJECT_DIR / "configs" / "settings.yaml"
    settings_dst = PROJECT_DIR / "settings.yaml"

    if not settings_src.exists():
        print(f"[init] ✗ ERROR: {settings_src} not found")
        sys.exit(1)

    shutil.copy(settings_src, settings_dst)
    print(f"[init] ✓ Copied configs/settings.yaml → settings.yaml")

    # --- Step 4: Verify input corpus ---
    input_dir = PROJECT_DIR / "data" / "input"
    if input_dir.exists():
        txt_files = list(input_dir.glob("*.txt"))
    else:
        txt_files = []

    if not txt_files:
        print("[init] ✗ WARNING: data/input/ is EMPTY — no documents to index!")
        print("[init]    Run this first:")
        print("[init]      bash scripts/01_download_corpus.sh")
        print("[init]      python scripts/02_preprocess_docs.py --input data/raw --output data/input")
    else:
        total_size = sum(f.stat().st_size for f in txt_files)
        total_kb = total_size / 1024
        print(f"[init] ✓ Input corpus: {len(txt_files)} files, {total_kb:,.0f} KB total")
        # Show first 5
        for f in sorted(txt_files)[:5]:
            print(f"[init]     - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
        if len(txt_files) > 5:
            print(f"[init]     ... and {len(txt_files) - 5} more")

    # --- Step 5: Ensure output dirs ---
    for d in ["data/output", "logs", "cache"]:
        p = PROJECT_DIR / d
        p.mkdir(parents=True, exist_ok=True)
    print("[init] ✓ Output directories ready")

    # --- Step 6: Verify embedding config ---
    print()
    print("[init] === GraphRAG project initialized ===")
    print()
    print("[init] Next steps (3 terminals):")
    print("[init]   Terminal 1: make run-embed")
    print("[init]   Terminal 2 (wait for embed): make run-index")
    print("[init]   Terminal 3: make run-query-global")
    print()
    print("[init] Or all-in-one:  make run-all")


if __name__ == "__main__":
    main()
