#!/usr/bin/env bash
set -euo pipefail

API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8006}"
BASE="http://${API_HOST}:${API_PORT}"

echo "[smoke] checking health …"
curl -fsS "${BASE}/health" | python -m json.tool --no-ensure-ascii

echo ""
echo "[smoke] RAG invoke …"
curl -fsS "${BASE}/v1/rag/invoke" \
  -H "Content-Type: application/json" \
  -d '{"query":"请用一句话说明知识库主题","thread_id":"smoke-001"}' \
  | python -m json.tool --no-ensure-ascii

echo ""
echo "[smoke] SSE stream (3 seconds) …"
timeout 3 curl -fsSN "${BASE}/v1/rag/stream" \
  -H "Content-Type: application/json" \
  -d '{"query":"测试流式输出","thread_id":"smoke-002"}' \
  || true

echo ""
echo "[smoke] checkpoint state …"
curl -fsS "${BASE}/v1/rag/state/smoke-001" \
  | python -m json.tool --no-ensure-ascii

echo ""
echo "[smoke] all checks passed ✅"
