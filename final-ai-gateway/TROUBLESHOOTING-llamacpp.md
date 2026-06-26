# Troubleshooting: llama.cpp 模型服务问题

## 症状

```
httpx.ConnectError: Connection refused
```
或
```
GatewayChatModel stream error: Connection refused
```
或
```
LlamacppClient health check failed
```

## 原因

1. llama.cpp server 未启动
2. 端口冲突（默认 8080）
3. GGUF 模型文件路径错误
4. 模型参数配置不当（context length / slots）

## 解决步骤

### 1. 检查模型文件

```bash
# 确认模型文件存在
ls -lh /path/to/qwen2.5-7b-instruct-q4_k_m.gguf

# 预期输出: 约 4.4GB 的 .gguf 文件
```

### 2. 启动 llama.cpp server

```bash
llama-server \
  -m /path/to/qwen2.5-7b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  -c 8192 \
  -np 4 \
  --metrics \
  --slots \
  --cache-prompt \
  --slot-save-path ./runtime/slot_cache
```

### 3. 验证服务

```bash
# 健康检查
curl http://127.0.0.1:8080/health

# 查看 slots
curl http://127.0.0.1:8080/slots | python3 -m json.tool

# 测试 tokenize
curl -X POST http://127.0.0.1:8080/tokenize \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello world"}'

# 测试 chat completion
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50,
    "stream": false
  }'
```

### 4. 常见参数问题

| 参数 | 说明 | 建议值 |
|------|------|--------|
| `-c` | 上下文长度 | 8192 (Qwen 2.5 7B 最大) |
| `-np` | 并行 slots | 4 (M5 32GB 建议) |
| `--metrics` | 暴露指标 | 必须开启 |
| `--cache-prompt` | prompt cache | 开，减少 prefill |

### 5. 内存不足

MacBook Air M5 32GB 可以运行 Q4_K_M (约 4.4GB 模型 + KV Cache)。

```bash
# 监控内存
memory_pressure
# 或
top -l 1 | grep "PhysMem"
```

如果内存紧张，减少 `-np` 参数或换更小量化：
```bash
# 减少到 2 个 slots
llama-server -m model.gguf -np 2 ...

# 或使用 IQ3_M 量化（更小但质量稍降）
```

### 6. 端口冲突

```bash
# 检查 8080 端口
lsof -i :8080

# 如果被占用，换端口
llama-server --port 8081 ...
# 同时更新 configs/model.yaml 中的 url
```

## 使用 Ollama 替代

如果 llama.cpp server 有问题，可以临时切到 Ollama：

```bash
# 启动 Ollama
ollama serve

# 拉取模型
ollama pull qwen2.5:7b

# 测试
curl http://127.0.0.1:11434/api/tags
```

然后修改 `configs/model.yaml` 中对应模型的 `backend: ollama`。
