#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:8081"

# 1. 先发一个长系统提示词请求，让 slot 内产生可复用 KV
curl -s "${BASE}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-qwen2.5-7b-q4",
    "messages": [
      {"role": "system", "content": "你是企业级 AI Gateway 审计助手。请始终从架构、性能、可靠性、可观测性、安全边界五个角度回答。这个系统提示词故意写长，用于测试 prompt cache 复用。"},
      {"role": "user", "content": "解释为什么本地模型 serving 需要网关层。"}
    ],
    "max_tokens": 256,
    "temperature": 0.2
  }' > /tmp/cache_warmup.json

echo "warmup done"

# 2. 保存 slot 0 的 prompt cache
curl -s -X POST "${BASE}/slots/0?action=save" \
  -H "Content-Type: application/json" \
  -d '{"filename":"gateway_system_prompt.bin"}' | python -m json.tool

# 3. 恢复 slot 0 的 prompt cache
curl -s -X POST "${BASE}/slots/0?action=restore" \
  -H "Content-Type: application/json" \
  -d '{"filename":"gateway_system_prompt.bin"}' | python -m json.tool

# 4. 再次请求同类 prompt，对比 TTFT 和 metrics 中 prompt throughput
curl -s "${BASE}/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-qwen2.5-7b-q4",
    "messages": [
      {"role": "system", "content": "你是企业级 AI Gateway 审计助手。请始终从架构、性能、可靠性、可观测性、安全边界五个角度回答。这个系统提示词故意写长，用于测试 prompt cache 复用。"},
      {"role": "user", "content": "解释 prompt cache 和 KV cache 的区别。"}
    ],
    "max_tokens": 256,
    "temperature": 0.2
  }' > /tmp/cache_reuse.json

echo "cache reuse request done"