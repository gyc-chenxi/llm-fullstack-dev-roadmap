#!/usr/bin/env bash
# ============================================================
# P7: 查询入口
# ============================================================

set -euo pipefail

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate cxllm

export HF_ENDPOINT=https://hf-mirror.com

MODE="${1:-vector}"

case "$MODE" in
    vector)
        python src/query_engines/vector_query.py
        ;;
    summary)
        python src/query_engines/summary_query.py
        ;;
    router)
        python src/routers/multi_kb_router.py
        ;;
    *)
        echo "用法: bash scripts/query.sh [vector|summary|router]"
        echo "  vector  — VectorStoreIndex 语义检索（默认）"
        echo "  summary — SummaryIndex 全文总结"
        echo "  router  — RouterQueryEngine 多知识库路由"
        ;;
esac
