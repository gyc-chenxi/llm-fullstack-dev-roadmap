#!/usr/bin/env bash
# ============================================================
# P7: 环境一键初始化脚本
# ============================================================

set -euo pipefail

echo "============================================"
echo " P7 环境初始化"
echo " Conda 环境: cxllm"
echo " Python:     3.11"
echo "============================================"

echo ""
echo "🔧 激活 Conda 环境 cxllm..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate cxllm

echo "✅ Python $(python --version 2>&1)"

export HF_ENDPOINT=https://hf-mirror.com
echo "✅ HF_ENDPOINT=${HF_ENDPOINT}"

echo ""
echo "🔧 升级 pip 工具链..."
pip install -U pip setuptools wheel -q

echo ""
echo "🔧 安装 Python 依赖..."
pip install -r requirements.txt

echo ""
echo "🔧 验证安装..."
python -c "
import torch
import llama_index.core
import chromadb
print(f'PyTorch:        {torch.__version__}')
print(f'LlamaIndex:     {llama_index.core.__version__}')
print(f'ChromaDB:       {chromadb.__version__}')
print(f'MPS Available:  {torch.backends.mps.is_available()}')
"

echo ""
echo "============================================"
echo " ✅ 环境初始化完成"
echo "============================================"
echo ""
echo "下一步:"
echo "  1. bash scripts/download_models.sh   # 下载模型"
echo "  2. make build                         # 构建索引"
echo "  3. make query                         # 开始查询"
