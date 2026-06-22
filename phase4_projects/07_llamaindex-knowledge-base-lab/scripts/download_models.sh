#!/usr/bin/env bash
# ============================================================
# P7: 模型下载脚本 — 通过 HF 镜像下载 BGE Embedding 模型
# 平台：macOS / Apple Silicon
# ============================================================

set -euo pipefail

export HF_ENDPOINT=https://hf-mirror.com

MODEL_NAME="BAAI/bge-small-zh-v1.5"
LOCAL_DIR="models/bge-small-zh-v1.5"

echo "============================================"
echo " P7 模型下载工具"
echo " 镜像: ${HF_ENDPOINT}"
echo " 模型: ${MODEL_NAME}"
echo " 本地: ${LOCAL_DIR}"
echo "============================================"

if ! command -v hf &> /dev/null; then
    echo "❌ hf 未安装，请先执行: pip install -U huggingface_hub[hf]"
    exit 1
fi

mkdir -p "${LOCAL_DIR}"

echo ""
echo "🚀 开始下载模型..."
hf download \
    "${MODEL_NAME}" \
    --local-dir "${LOCAL_DIR}"

echo ""
echo "✅ 下载完成！模型文件:"
ls -lh "${LOCAL_DIR}/"
du -sh "${LOCAL_DIR}/"

echo ""
echo "💡 下一步: python src/indexes/build_vector_index.py"
