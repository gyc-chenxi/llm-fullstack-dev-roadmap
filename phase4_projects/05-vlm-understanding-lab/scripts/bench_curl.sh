#!/usr/bin/env bash
# ============================================================
# 快速 curl 基准测试脚本
# ============================================================
# 用法：
#   ./scripts/bench_curl.sh <图片路径> <问题>
#   ./scripts/bench_curl.sh assets/samples/ocr_demo.png "提取文字"
#
# 向 Gateway (port 8000) 的 /v1/vision/chat 端点发送
# multipart/form-data POST 请求，返回格式化的 JSON 响应。
# 要求 Gateway + Engine 服务已启动（make run-all 或手动启动）。
# ============================================================
set -euo pipefail

IMAGE="${1:-assets/samples/ocr_demo.png}"
QUESTION="${2:-请提取图片中的所有文字，保持原始格式。}"

curl -s -X POST "http://127.0.0.1:8000/v1/vision/chat" \
  -F "image=@${IMAGE}" \
  -F "question=${QUESTION}" | python -m json.tool --no-ensure-ascii
