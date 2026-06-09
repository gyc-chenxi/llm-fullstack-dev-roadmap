# 🚀 12 — 模型部署与 vLLM 推理引擎

> 🎯 **目标**：理解生产级推理引擎的工作原理，知道什么时候用 vLLM、Ollama、llama.cpp。
> ⏱️ 预计时间：1 天

---

## 📋 直接用 Transformers 跑模型有什么问题？

```python
# Demo 级别：能跑，但生产环境远远不够
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B")
output = model.generate("你好", max_new_tokens=256)
# 😅 单次推理，没有并发，显存利用率只有 20-40%
```

| 问题 | 影响 | vLLM 怎么解决的 |
|------|------|----------------|
| KV Cache 碎片化 | 显存利用率 20-40% | PagedAttention → ~100% |
| 静态 Batching | 并发能力差 | Continuous Batching |
| 无量化 | 大模型跑不动 | AWQ/GPTQ/FP8 支持 |
| 无标准 API | 每个模型不同调用方式 | OpenAI-compatible API |

---

## 1️⃣ vLLM 核心创新：PagedAttention

### 📌 问题：KV Cache 的碎片化

```
传统推理引擎（Fixed Allocation）:
  模型为每个请求预分配 max_seq_len 的 KV Cache 空间
  
  请求A(生成长度=实际只用了50%): ████████████░░░░░░░░░░░░  浪费50%
  请求B(生成长度较长):           ████████████████████████
  请求C(刚加入):                 ██████░░░░░░░░░░░░░░░░░░  浪费75%
  
  显存碎片化 → 大量空闲但无法利用的空间 → 并发上限低
```

### 📌 解决方案：分页管理

```
PagedAttention:
  每个 Block = 固定数量的 token（如 16 个）
  请求按需分配 Block，用完归还
  
  Block 0  Block 1  Block 2  Block 3  Block 4  Block 5
  请求A:████  ████   ___
  请求B:████  ████   ████   ████   ___
  请求C:████  ___
             ↑ 有空位立即给新请求用，没有碎片
```

> 💡 灵感来自操作系统的虚拟内存管理——物理内存分页，进程按需分配。

### 📌 量化收益

```
实验：Llama 2-7B，A100-80GB GPU

           传统方案      vLLM
吞吐量:    15 req/s      45 req/s    (↑ 3x)
显存利用率:  ~30%         ~95%
最大并发:   32 请求       128 请求    (↑ 4x)
```

---

## 2️⃣ Continuous Batching

### 📌 传统 Batching vs Continuous Batching

```
传统（Static Batching）:
  Batch = [请求A, 请求B, 请求C] → 必须等三个全部生成完 → 才能处理新请求
  请求A: ████████████████ (先生成完，但只能等着)
  请求B: ████████████████████████
  请求C: ██████ (早就生成完了，干等)
  
  问题：快请求被慢请求拖累

Continuous Batching:
  每生成一个 token 后检查 → 有请求完成？→ 立即腾出位置给新请求
  请求A: ████████████████ → 完成 → 退出
  请求B: ████████████████████████
  请求C: ██████ → 完成 → 退出
  请求D:          ████████████ → 中途插入！
```

---

## 3️⃣ 快速上手

### 📌 安装与启动

```bash
# 安装（需要 NVIDIA GPU + CUDA）
pip install vllm

# 启动 OpenAI 兼容 API 服务
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 8192 \          # 最大上下文长度
  --gpu-memory-utilization 0.90 \ # GPU 显存使用率上限
  --max-num-seqs 128 \            # 最大并发请求数
  --tensor-parallel-size 1        # 单 GPU = 1，多 GPU = N
```

### 📌 关键启动参数

| 参数 | 含义 | 建议值 | 为什么 |
|------|------|--------|--------|
| `--max-model-len` | 最大上下文长度 | 模型支持的最大值 | 设太大浪费显存 |
| `--gpu-memory-utilization` | GPU 显存使用率 | 0.85-0.95 | 留一点给系统 |
| `--max-num-seqs` | 最大并发数 | 根据 GPU 显存 | 太大 OOM |
| `--tensor-parallel-size` | 跨 GPU 数量 | N | 大模型拆到多卡 |

### 📌 API 调用

```bash
# 完全兼容 OpenAI 格式！
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "用三句话解释量子计算"}],
    "max_tokens": 256,
    "temperature": 0.7
  }'

# 流式
curl http://localhost:8000/v1/chat/completions \
  -d '{"model": "...", "messages": [...], "stream": true}'

# 查看模型列表
curl http://localhost:8000/v1/models
```

---

## 4️⃣ 四种推理方案完整对比

| 维度 | **Ollama** | **llama.cpp** | **vLLM** | **MLX LM** |
|------|-----------|--------------|----------|-----------|
| 平台 | 全平台 | 全平台 | NVIDIA GPU only | Apple Silicon only |
| 安装难度 | ⭐ 一键安装 | ⭐⭐ 需编译 | ⭐⭐ pip install | ⭐⭐ pip install |
| 推理速度 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 显存效率 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 并发能力 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| OpenAI API | ✅ | ✅ | ✅ | 需自己封装 |
| 量化生态 | GGUF | GGUF | AWQ/GPTQ | MLX 原生 |
| 适用场景 | 个人使用 | CPU/边缘设备 | 🚀 生产高并发 | Mac 本地 |

### 📌 选型决策树

```
你在什么设备上跑？
  ├── Apple Silicon Mac
  │   ├── 个人学习/实验 → MLX LM / Ollama
  │   └── 本地项目部署 → llama.cpp server
  │
  ├── NVIDIA GPU 服务器
  │   ├── 高并发生产环境 → vLLM 🔥
  │   └── 单个开发测试 → Ollama
  │
  └── CPU only 服务器
      └── llama.cpp（CPU 推理最强）
```

---

## 5️⃣ vLLM 高级特性

### 📌 Prefix Caching

```python
# 所有请求有相同的 system prompt 时，自动复用 KV Cache
# 实测：326 token system prompt
#   首次: TTFT = 450ms
#   后续: TTFT = 230ms  (节省 ~50%)
```

### 📌 Multi-LoRA 动态切换

```bash
# 一个 7B 基础模型 + 3 个 LoRA 适配器
# 请求时指定用哪个 LoRA，不需要重启服务
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --lora-modules identity=./lora_identity \
  --lora-modules medical=./lora_medical \
  --lora-modules code=./lora_coding

# 请求时指定
curl ... -d '{"model": "Qwen/Qwen2.5-7B-Instruct", "lora": "medical", ...}'
```

### 📌 Speculative Decoding

```
小模型（快但不够准）  →  猜 5 个 token
大模型（准但慢）      →  验证这 5 个 token
                     →  通过 4 个 → 相当于一次生成了 4 个！
                     
加速比：1.5-3x，取决于大小模型的"默契度"
```

---

## 6️⃣ 性能基准测试

```bash
# 并发压测
python -c "
import asyncio, httpx, time

async def bench():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post('http://localhost:8000/v1/chat/completions', json={
                'model': 'Qwen/Qwen2.5-7B-Instruct',
                'messages': [{'role': 'user', 'content': '你好'}],
                'max_tokens': 256,
            })
            for _ in range(100)  # 100 个并发请求
        ]
        start = time.time()
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        print(f'100 请求 {elapsed:.1f}s, 平均 {100/elapsed:.1f} req/s')

asyncio.run(bench())
"
```

---

## 7️⃣ 常见翻车现场 🚨

| 现象 | 原因 | 解决 |
|------|------|------|
| vLLM 启动 OOM | `max-model-len` 设太大 | 减小到 4096 或降低 `gpu-memory-utilization` |
| 第一个请求超时 | 模型加载（~30s） | 设置合适的 `timeout` |
| "Model not found" | 模型名不是 HuggingFace ID | 给绝对路径或确认模型名正确 |
| 吞吐量低于预期 | batch size 不够 | 增大 `max-num-seqs` + 发更多并发请求 |
| Mac 上装不了 vLLM | vLLM 依赖 CUDA | Mac 用 MLX LM 或 llama.cpp |

---

## ✅ 产出物 Checklist

- [ ] 用 `pip install vllm` 安装（NVIDIA GPU 环境）或云 GPU 上跑
- [ ] 启动 vLLM serve，用 curl 测试流式和非流式
- [ ] 用 asyncio + httpx 做并发压测，记录吞吐量
- [ ] 对比 Ollama vs llama.cpp vs vLLM 的推理速度（同一模型）
- [ ] 理解 PagedAttention 为什么能提升 2-4x 吞吐
