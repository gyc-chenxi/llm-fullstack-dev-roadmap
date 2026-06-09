#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TP_DIR="${ROOT_DIR}/third_party"

mkdir -p "${TP_DIR}"
cd "${TP_DIR}"

if [ ! -d "llama.cpp" ]; then
  git clone https://github.com/ggml-org/llama.cpp
fi

cd llama.cpp
git pull

# Apple Silicon 生产建议：
# -DGGML_METAL=ON       显式打开 Metal，虽然 macOS 默认打开，但这里写清楚，避免审计歧义
# -DCMAKE_BUILD_TYPE=Release  使用 Release 优化
# --target llama-server llama-cli llama-gguf-split 只构建本周需要的二进制
cmake -B build \
  -DGGML_METAL=ON \
  -DCMAKE_BUILD_TYPE=Release

cmake --build build \
  --config Release \
  --target llama-server llama-cli llama-gguf-split \
  -j "$(sysctl -n hw.ncpu)"

echo "Build done:"
ls -lh build/bin/llama-server build/bin/llama-cli build/bin/llama-gguf-split