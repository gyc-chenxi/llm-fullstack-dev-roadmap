#!/usr/bin/env bash
# ============================================================
# P7: 文档摄取脚本
# ============================================================

set -euo pipefail

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate cxllm

export HF_ENDPOINT=https://hf-mirror.com

echo "🚀 启动文档摄取..."
python -c "
from src.utils.config import Config
from src.loaders.document_loader import load_local_documents
from src.ingestion.pipeline import build_ingestion_pipeline, run_ingestion

config = Config.load('configs/settings.yaml')
docs = load_local_documents(input_dir='data/raw')
pipeline = build_ingestion_pipeline(config)
nodes = run_ingestion(docs, pipeline, config)
print(f'Done: {len(nodes)} nodes')
"
