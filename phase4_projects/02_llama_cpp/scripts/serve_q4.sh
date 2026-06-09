#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LLAMA_SERVER="${ROOT_DIR}/third_party/llama.cpp/build/bin/llama-server"
MODEL="${ROOT_DIR}/models/qwen2.5-7b-instruct-q4_k_m.gguf"
SLOT_CACHE_DIR="${ROOT_DIR}/reports/slot_cache"

mkdir -p "${SLOT_CACHE_DIR}"

"${LLAMA_SERVER}" \
  -m "${MODEL}" \
  --alias local-qwen2.5-7b-q4 \
  --host 127.0.0.1 \
  --port 8081 \
  -c 8192 \
  -b 512 \
  -ub 128 \
  -ngl 99 \
  --parallel 2 \
  --cache-prompt \
  --slot-save-path "${SLOT_CACHE_DIR}" \
  --metrics \
  --slots \
  --log-timestamps