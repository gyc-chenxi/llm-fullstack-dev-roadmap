#!/usr/bin/env bash
set -euo pipefail

echo "[models] downloading Qwen2.5 7B Instruct GGUF Q4_K_M"

mkdir -p models/llm/qwen2.5-7b-instruct-gguf

hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
  --local-dir models/llm/qwen2.5-7b-instruct-gguf \
  --include "qwen2.5-7b-instruct-q4_k_m-*.gguf"

echo "[models] warming up embedding model"
python - <<'PY'
from sentence_transformers import SentenceTransformer
SentenceTransformer("BAAI/bge-m3")
print("embedding model ready")
PY

echo "[models] warming up reranker model"
python - <<'PY'
from FlagEmbedding import FlagReranker
FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False)
print("reranker model ready")
PY

echo "[models] done"
