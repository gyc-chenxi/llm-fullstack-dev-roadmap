#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-assets/samples/ocr_demo.png}"
QUESTION="${2:-请提取图片中的所有文字，保持原始格式。}"

curl -s -X POST "http://127.0.0.1:8000/v1/vision/chat" \
  -F "image=@${IMAGE}" \
  -F "question=${QUESTION}" | python -m json.tool --no-ensure-ascii