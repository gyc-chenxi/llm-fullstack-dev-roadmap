#!/usr/bin/env bash
set -euo pipefail

curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-qwen2.5-7b-q4",
    "messages": [
      {"role": "system", "content": "你是一个严谨的 AI Infra 工程师。"},
      {"role": "user", "content": "用三点解释 GGUF、KV Cache、Prompt Cache 的区别。"}
    ],
    "temperature": 0.2,
    "max_tokens": 512,
    "stream": false
  }' | python -m json.tool