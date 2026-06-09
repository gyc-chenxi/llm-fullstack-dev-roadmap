# 大模型应用工程师 9 周专家级实战路线：本地推理、多模态、RAG-Agent 与 AI Infra 工程化手册

本文档面向希望系统进入“大模型应用工程师 / AI Infra 工程师”方向的学习者，围绕 9 周实战项目，完整覆盖 Apple Silicon 本地大模型部署、MLX 微调、llama.cpp GGUF 量化推理、Diffusers 生成式视觉、SAM 2 图像与视频分割、Qwen-VL/LLaVA 多模态理解、LangChain/LangGraph 企业级 RAG-Agent、GraphRAG 图谱增强检索以及 SWE-agent 代码修复智能体。通过这份路线，学习者不仅能掌握模型调用与部署，更能理解模型服务化、数据流设计、评测体系、Trace 可观测性、工具调用、状态机编排和企业级 AI 应用落地方法，最终形成一套可展示、可复现、可面试讲解的 AI 工程作品集。

> 默认设备假设：Apple Silicon，32GB 统一内存，macOS，Python 3.10/3.11，conda 或 uv 管理环境。
>  统一原则：每周都必须沉淀 README、架构图、可运行 Demo、Eval 报告、Interview Notes。

------

# Week 1：MLX LM —— Apple Silicon 本地 LLM 微调与部署

## 1. 技术背景与核心原理

MLX 是 Apple 机器学习研究团队面向 Apple Silicon 设计的数组与机器学习框架，核心优势是贴合统一内存架构，减少 CPU/GPU 间显存拷贝成本；MLX-LM 则是其上层 LLM 工具包，支持 Hugging Face Hub 模型加载、文本生成、量化、LoRA/全量微调和模型上传等能力。

这一周的核心不是“本地聊天”，而是建立你自己的 Apple Silicon LLM 实验底座：模型下载、格式转换、量化、LoRA、推理、服务化、延迟测试。它解决的是 Mac 用户做本地 LLM 实验时常见的三类问题：CUDA 不可用、Ollama 封装过厚、Transformers + MPS 对推理和微调闭环不够直接。

在当前大模型工程栈中，MLX LM 适合作为：

- Mac 本地实验底座；
- 小模型 LoRA 微调验证环境；
- 面向个人知识库、轻量 Agent、Prompt 工程的低成本推理服务；
- 和 llama.cpp、Ollama、vLLM 对比的 Apple 原生路线。

## 2. 详细技术栈与架构设计

核心栈：

```
Python 3.11
mlx
mlx-lm
transformers
datasets
huggingface_hub
fastapi
uvicorn
pydantic
httpx
rich / typer
psutil
```

推荐周边库：

```
评测与日志：
  pandas
  numpy
  jsonlines
  tqdm
  matplotlib

服务化：
  fastapi
  sse-starlette
  uvicorn
  pydantic-settings

前端联调：
  Vue 3
  TypeScript
  EventSource / fetch stream
```

推荐目录：

```
mlx-local-lab/
  README.md
  configs/
    model.yaml
    lora.yaml
    serving.yaml
  scripts/
    download_model.py
    infer.py
    finetune_lora.py
    quantize.py
    bench_latency.py
  server/
    app.py
    schemas.py
    engine.py
  datasets/
    identity_train.jsonl
    identity_valid.jsonl
  eval/
    latency_report.md
    quality_report.md
  docs/
    architecture.md
    interview_notes.md
```

后端到前端的接入建议：

```
Vue3 输入 prompt
  ↓
POST /v1/chat/completions 或 /chat/stream
  ↓
FastAPI 调用 MLX generation engine
  ↓
SSE 推送 token_delta / done / error
  ↓
前端 EventSource 或 fetch reader 增量渲染
```

接口建议尽量兼容 OpenAI Chat Completions：

```
{
  "model": "qwen-local-mlx",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "解释一下 LoRA。"}
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "stream": true
}
```

## 3. 项目实战详细描述

最终项目是一个 `mlx-local-lab`：可以在 Apple Silicon 上加载 Qwen/Llama 系列小模型，完成一次 LoRA 微调，量化后启动本地 FastAPI/SSE 推理服务，并输出延迟与内存报告。

企业价值在于：你能证明自己不是只会调用云 API，而是理解本地模型从实验到服务化的完整闭环。对内部私有数据问答、离线助手、边缘部署、低成本 PoC 很有价值。

## 4. 数据集与评测基准

推荐数据：

```
微调：
  tatsu-lab/alpaca
  yahma/alpaca-cleaned
  OpenAssistant/oasst1
  自建 identity/style/task JSONL

中文任务：
  BelleGroup/train_0.5M_CN
  firefly-train-1.1M
  自建 100-300 条个人任务指令
```

自建 Gold Set：

```
{"instruction": "你是谁？", "input": "", "output": "我是本地部署的晨熙项目助手。"}
{"instruction": "用三句话解释 Apple Silicon 统一内存。", "input": "", "output": "..."}
{"instruction": "把下面文字改写成更学术的表达。", "input": "xxx", "output": "xxx"}
```

评测指标：

```
性能：
  TTFT
  tokens/s
  peak memory
  model load time
  P50/P95 latency

质量：
  exact match
  人工偏好评分
  格式遵循率
  拒答正确率
  identity consistency
```

## 5. 核心开源项目与参考链接

必须看：

- `ml-explore/mlx`：理解 Apple Silicon 原生 ML 框架定位。
- `ml-explore/mlx-lm`：重点看 generation、quantization、fine-tuning、LoRA 示例。
- `mlx-community`：寻找已转换好的 MLX 模型权重。
- Hugging Face Transformers Tokenizer 文档：理解 chat template、special tokens、tokenizer mismatch。

## 6. 极简复现与避坑指南

### Step 1：创建环境

```
conda create -n mlxlab python=3.11 -y
conda activate mlxlab

pip install -U mlx mlx-lm transformers datasets huggingface_hub fastapi uvicorn sse-starlette pydantic rich typer psutil
```

### Step 2：测试模型生成

优先使用 4B/7B/8B 级别模型。32GB 统一内存可以比较舒服地跑 4bit 7B/8B，14B 需要谨慎，长上下文会明显吃内存。

```
python -m mlx_lm.generate \
  --model mlx-community/Qwen2.5-7B-Instruct-4bit \
  --prompt "用三句话解释 LoRA 微调的本质。"
```

也可以尝试 Qwen3 8B 或 Llama 3.x 8B 的 MLX 社区权重，但注意 chat template 是否被模型仓库正确配置。

### Step 3：准备 LoRA 数据

```
{"messages":[{"role":"user","content":"你是谁？"},{"role":"assistant","content":"我是晨熙本地大模型实验助手。"}]}
{"messages":[{"role":"user","content":"你的回答风格是什么？"},{"role":"assistant","content":"我会用工程化、可复现、可评测的方式回答问题。"}]}
```

保存为：

```
datasets/identity_train.jsonl
datasets/identity_valid.jsonl
```

### Step 4：LoRA 微调

```
python -m mlx_lm.lora \
  --model mlx-community/Qwen2.5-7B-Instruct-4bit \
  --train \
  --data datasets \
  --batch-size 1 \
  --iters 200 \
  --learning-rate 1e-5 \
  --adapter-path adapters/identity_lora
```

32GB Apple Silicon 避坑：

```
1. batch-size 先从 1 开始。
2. max_seq_length 不要一上来开到 8k/16k。
3. 训练时关闭其他吃内存应用，尤其是浏览器多标签页。
4. LoRA rank 不要盲目调大，先用 r=8 或 r=16。
5. identity/style 微调不要用太高学习率，容易产生灾难性偏移。
```

### Step 5：服务化

```
# server/app.py
from fastapi import FastAPI
from pydantic import BaseModel
from mlx_lm import load, generate

app = FastAPI()
model, tokenizer = load("mlx-community/Qwen2.5-7B-Instruct-4bit")

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: int = 512

@app.post("/generate")
def generate_text(req: ChatRequest):
    text = generate(
        model,
        tokenizer,
        prompt=req.prompt,
        max_tokens=req.max_tokens,
        verbose=False,
    )
    return {"text": text}
uvicorn server.app:app --host 0.0.0.0 --port 8001
```

## 7. 进阶工程优化方向

1. **KV Cache 与上下文管理**
    建立 prompt 长度、输出长度、内存占用的曲线。重点理解长上下文不是“免费能力”，prefill 阶段会显著增加 TTFT。
2. **服务层与模型层解耦**
    FastAPI 层不要直接写死模型调用。建议封装：

```
BaseLLMEngine
  MLXEngine
  LlamaCppEngine
  OllamaEngine
```

后续 Week 2/7 可以复用。

1. **多模型路由**
    轻任务走 4B，复杂任务走 7B/8B；格式化任务低 temperature，创作任务高 temperature。把路由策略写成配置，而不是硬编码。

## 8. 面试深度解析

**Q1：Apple Silicon 本地推理和 CUDA 推理最大的系统差异是什么？**
 答题思路：Apple Silicon 是统一内存架构，CPU/GPU 共享内存，减少数据搬运；NVIDIA CUDA 的生态、kernel 优化、并发 serving、vLLM/PagedAttention 等生产能力更成熟。Mac 适合本地实验和轻量部署，不等价于企业高并发 GPU serving。

**Q2：MLX LoRA 微调和生产环境全量微调有什么差别？**
 答题思路：MLX LoRA 更适合小数据、低成本、快速验证；生产微调要考虑数据治理、评测集、灾难性遗忘、安全对齐、持续评测、模型版本管理。

**Q3：为什么本地模型服务要记录 TTFT 而不只记录 tokens/s？**
 答题思路：TTFT 影响用户感知延迟，主要受 prompt prefill、上下文长度、模型加载、调度排队影响；tokens/s 只反映 decode 阶段吞吐，两者瓶颈不同。

------

# Week 2：llama.cpp —— GGUF 量化与高性能本地推理底座

## 1. 技术背景与核心原理

llama.cpp 是本地 LLM 推理底座的事实标准之一。它的价值在于暴露底层推理工程能力：GGUF 模型格式、K-quant 量化、Metal/CUDA/CPU 后端、OpenAI-compatible server、slot、prompt cache、tokenize、embeddings、metrics 等。llama.cpp server 文档明确支持 OpenAI 兼容的 chat completions、responses、embeddings 路由，并提供 slot prompt cache 保存/恢复接口。

GGUF 是 llama.cpp 生态下常用模型文件格式，通常把权重、tokenizer 元数据、chat template、量化信息放在同一个文件中，便于单文件分发。对 AI Infra 训练来说，Week 2 的价值超过 Ollama，因为你能直接理解服务参数和性能瓶颈之间的映射。

## 2. 详细技术栈与架构设计

核心栈：

```
llama.cpp
llama-server
GGUF models
Metal backend
Python httpx
FastAPI wrapper
Prometheus / metrics endpoint
pytest
```

推荐周边：

```
压测：
  httpx
  asyncio
  locust
  pytest-benchmark

监控：
  prometheus-client
  grafana，可选
  psutil

模型来源：
  Hugging Face GGUF repo
  ModelScope GGUF 镜像，可选
```

推荐架构：

```
llamacpp-serving-lab/
  models/
    qwen2.5-7b-instruct-q4_k_m.gguf
  scripts/
    bench_chat.py
    bench_context.py
    bench_concurrency.py
    test_prompt_cache.py
    tokenize_check.py
  gateway/
    app.py
    router.py
    schemas.py
  docs/
    quantization_report.md
    serving_params.md
    interview_notes.md
  reports/
    latency_matrix.csv
```

服务分层：

```
Vue3 / CLI
  ↓
AI Gateway FastAPI
  ↓
llama-server OpenAI-compatible API
  ↓
GGUF model + Metal backend
```

## 3. 项目实战详细描述

最终项目是 `llamacpp-serving-lab`：能够加载不同量化等级 GGUF，启动 llama-server，跑并发压测，记录 q4/q5/fp16 在速度、内存、质量上的差异，并验证 prompt cache 和 slot 行为。

企业价值：这是 AI-Gateway 的本地模型底座。你可以把本地模型像 OpenAI API 一样纳入统一网关、限流、日志、审计、成本统计和模型路由。

## 4. 数据集与评测基准

推荐测试集：

```
通用问答：
  自建 50 条中文工程问答
  AlpacaEval 风格小样本

长上下文：
  自己的 Markdown 项目文档
  README + issue + changelog 拼接

工具/格式：
  JSON 输出测试集 30 条
  function calling 伪 schema 测试集
```

Gold Set 构造：

```
{"id":"latency_001","prompt":"用三点解释 GGUF 的作用。","expected_keywords":["量化","tokenizer","llama.cpp"]}
{"id":"json_001","prompt":"返回 JSON：姓名张三，年龄20。","must_be_valid_json":true}
{"id":"ctx_001","prompt_file":"docs/lport.md","question":"L-Port 的核心边界是什么？","answer_contains":["标准 IO","candidate-only","provenance"]}
```

评测：

```
TTFT
tokens/s
P50/P95 latency
并发成功率
OOM 次数
JSON 有效率
长上下文正确率
量化前后主观质量差异
```

## 5. 核心开源项目与参考链接

必须看：

- `ggml-org/llama.cpp`。
- `tools/server/README.md`：OpenAI-compatible API、slots、metrics、prompt cache。
- llama-cpp-python server：如果你要用 Python 包封装 OpenAI-compatible server，可读它的 server 文档。
- TheBloke / bartowski / Qwen GGUF 模型仓库：学习量化命名与模型分发习惯。

## 6. 极简复现与避坑指南

### Step 1：安装或编译 llama.cpp

优先用 release binary；需要自己编译时：

```
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DGGML_METAL=ON
cmake --build build --config Release -j
```

### Step 2：下载 GGUF

建议 32GB Mac 从 7B/8B 的 `Q4_K_M` 或 `Q5_K_M` 开始：

```
Qwen2.5-7B-Instruct-Q4_K_M.gguf
Qwen2.5-7B-Instruct-Q5_K_M.gguf
Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

量化选择经验：

```
Q4_K_M：速度快、内存低，适合服务压测。
Q5_K_M：质量更稳，内存略高。
Q8_0：质量更好但内存压力明显。
F16：32GB 下只建议短上下文测试，不建议作为常驻服务。
```

### Step 3：启动 llama-server

```
./build/bin/llama-server \
  -m models/qwen2.5-7b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \
  -b 512 \
  -ub 128 \
  -ngl 99 \
  --metrics \
  --parallel 2
```

Apple Silicon 避坑：

```
1. -ngl 99 表示尽量 offload 到 GPU/Metal，具体效果取决于模型与构建。
2. -c 不要盲目开 32k，KV Cache 会吃内存。
3. --parallel 越大不一定越快；32GB 机器建议从 1/2/4 对比。
4. q4_k_m 是首选 baseline，不要一开始用 fp16 常驻。
```

### Step 4：OpenAI-compatible 测试

```
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-qwen",
    "messages": [
      {"role": "user", "content": "解释 GGUF、KV Cache、prompt cache 的区别。"}
    ],
    "temperature": 0.2,
    "max_tokens": 512
  }'
```

### Step 5：压测脚本

```
# scripts/bench_chat.py
import asyncio, time, httpx, statistics

URL = "http://localhost:8080/v1/chat/completions"

async def one(i: int):
    payload = {
        "model": "local",
        "messages": [{"role": "user", "content": f"第{i}次：用三点解释 RAG。"}],
        "max_tokens": 256,
        "temperature": 0.2,
    }
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(URL, json=payload)
    dt = time.perf_counter() - t0
    return dt, r.status_code

async def main():
    tasks = [one(i) for i in range(20)]
    results = await asyncio.gather(*tasks)
    lat = [x[0] for x in results if x[1] == 200]
    print("success:", len(lat))
    print("p50:", statistics.median(lat))
    print("p95:", sorted(lat)[int(len(lat)*0.95)-1])

asyncio.run(main())
```

## 7. 进阶工程优化方向

1. **上下文窗口与 KV Cache 成本建模**
    建立：

```
context_length × parallel_slots × kv_precision → memory
```

不要只看模型权重大小。

1. **Prompt Cache 复用**
    对系统提示词、长文档前缀、Agent 固定工具说明做 cache。llama-server 的 slot restore/save 能用于实验 prompt cache 效果。
2. **AI Gateway 抽象**
    在网关层统一：

```
/v1/chat/completions
/v1/embeddings
/v1/models
/health
/metrics
```

把 llama.cpp、MLX、Ollama、云 API 全部做成 provider。

## 8. 面试深度解析

**Q1：GGUF 和 safetensors 的差异是什么？**
 答题思路：safetensors 更偏通用权重存储，常用于 Transformers/Diffusers；GGUF 更贴近 llama.cpp 推理生态，通常包含量化权重和 tokenizer/chat template 元信息，适合本地推理分发。

**Q2：为什么长上下文会让本地 serving 变慢？**
 答题思路：prefill 计算随输入长度增加，KV Cache 内存也随 context length、层数、hidden size、并发 slot 增长；长上下文影响 TTFT 和并发能力。

**Q3：prompt cache 和 KV Cache 是一回事吗？**
 答题思路：KV Cache 是一次推理中 attention key/value 的缓存；prompt cache 是将某段已计算过的 prompt 前缀状态保存并复用，主要优化重复长前缀场景。

------

# Week 3：Diffusers —— 生成式视觉工程底座

## 1. 技术背景与核心原理

Diffusers 是 Hugging Face 面向扩散模型的工程化库，覆盖 Stable Diffusion、SDXL、ControlNet、LoRA、IP-Adapter、inpainting、scheduler、pipeline 组合等。IP-Adapter 是将图像条件接入文本到图像扩散模型的轻量适配器，其设计是在 UNet 中增加图像特征相关的 cross-attention，并冻结原模型主干。

这一周的重点是从 ComfyUI 节点使用者升级为 pipeline 工程师。你需要理解：

```
text encoder：把 prompt 编成文本条件
UNet / DiT：扩散去噪主干
VAE：latent 与 image 之间编码/解码
scheduler：控制去噪轨迹
LoRA：低秩注入风格/角色/概念
ControlNet：结构条件控制
IP-Adapter：图像参考控制
mask：局部重绘约束
```

## 2. 详细技术栈与架构设计

核心栈：

```
Python
PyTorch
Diffusers
Transformers
Accelerate
PEFT
safetensors
Pillow
OpenCV
numpy
pydantic
jsonlines
```

推荐周边：

```
图像质量：
  lpips
  imagehash
  clip-score
  aesthetic-predictor，可选

API：
  FastAPI
  Celery/RQ
  Redis
  SSE/WebSocket

前端：
  Vue3 + TypeScript
  Canvas mask editor
  任务队列轮询或 SSE 进度
```

任务 schema：

```
from pydantic import BaseModel
from typing import Literal

class GenerationTask(BaseModel):
    task_type: Literal["txt2img", "img2img", "inpaint", "controlnet"]
    prompt: str
    negative_prompt: str = ""
    seed: int
    width: int = 1024
    height: int = 1024
    steps: int = 30
    cfg_scale: float = 7.0
    scheduler: str = "euler"
    base_model: str
    loras: list[dict] = []
    control_images: list[str] = []
    mask_path: str | None = None
```

## 3. 项目实战详细描述

最终项目是 `diffusers-pipeline-lab`：支持 txt2img、img2img、inpaint、ControlNet/IP-Adapter 四类任务，所有生成任务写入 manifest，记录 seed、prompt、scheduler、LoRA、mask 和输出图。

企业价值：生成式视觉系统不能只靠 UI 拖节点，必须能在后端批量、可复现、可审计地生成内容。这一周直接对应 AIGC 产品的任务编排层。

## 4. 数据集与评测基准

推荐数据：

```
图像生成测试：
  自建 30 条 prompt set
  DrawBench 风格 prompt
  PartiPrompts 风格 prompt

inpaint：
  COCO validation images
  自建 mask 样本
  产品图局部替换样本

ControlNet：
  COCO pose/edge/depth 样本
  自建 lineart/canny/depth 对
```

Gold Set 构造：

```
{"id":"txt_001","prompt":"a red apple on a wooden table","must_have":["apple","table"],"seed":42}
{"id":"inpaint_001","image":"case1.png","mask":"mask1.png","prompt":"replace the cup with a blue mug"}
{"id":"control_001","control_type":"canny","prompt":"anime girl, same pose, clean lineart"}
```

评测：

```
可复现性：同 seed 参数一致时 hash/视觉是否稳定
结构保持：ControlNet 输入边缘与输出边缘相似度
局部重绘：mask 外区域变化率
审计完整性：manifest 字段完整率
人工评分：构图、语义、细节、瑕疵
```

## 5. 核心开源项目与参考链接

必须看：

- Hugging Face Diffusers 官方文档。
- Diffusers LoRA / adapter loading 文档。
- Diffusers IP-Adapter 文档。
- ControlNet 论文与 Diffusers 示例。
- SDXL 技术报告：重点理解双 text encoder、base/refiner、分辨率微条件等。

## 6. 极简复现与避坑指南

### Step 1：环境

```
conda create -n difflab python=3.11 -y
conda activate difflab

pip install -U torch torchvision torchaudio
pip install -U diffusers transformers accelerate peft safetensors pillow opencv-python pydantic jsonlines
```

Apple Silicon 可以用 MPS，但 SDXL 在 MPS 上速度和兼容性仍不如 CUDA。你的 32GB Mac 可以跑小规模推理，但训练、DreamBooth、批量高分辨率生成建议上云 GPU。

### Step 2：txt2img

```
import torch
from diffusers import StableDiffusionXLPipeline

model_id = "stabilityai/stable-diffusion-xl-base-1.0"

pipe = StableDiffusionXLPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
)

device = "mps" if torch.backends.mps.is_available() else "cpu"
pipe = pipe.to(device)

image = pipe(
    prompt="a cinematic photo of a glass teapot on a wooden table, soft light",
    negative_prompt="low quality, blurry",
    num_inference_steps=25,
    guidance_scale=6.5,
).images[0]

image.save("outputs/txt2img.png")
```

### Step 3：inpaint

```
from diffusers import StableDiffusionXLInpaintPipeline
from PIL import Image
import torch

pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
    "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
).to("mps")

image = Image.open("inputs/base.png").convert("RGB")
mask = Image.open("inputs/mask.png").convert("L")

out = pipe(
    prompt="replace the object with a blue ceramic mug, realistic lighting",
    image=image,
    mask_image=mask,
    num_inference_steps=25,
    guidance_scale=7.0,
).images[0]

out.save("outputs/inpaint.png")
```

### Step 4：LoRA 加载

```
pipe.load_lora_weights("path/to/lora", weight_name="adapter.safetensors")
pipe.fuse_lora(lora_scale=0.7)
```

避坑：

```
1. LoRA 必须匹配底模族：SD1.5、SDXL、Pony、Illustrious、Flux 不可乱用。
2. safetensors 不是自动安全等于内容可信，仍要记录来源和 license。
3. MPS 上 fp16、attention slicing、VAE decode 可能出现兼容问题，遇到异常先降分辨率。
4. 每张图必须记录 manifest，否则无法复现。
```

## 7. 进阶工程优化方向

1. **任务队列化**
    生成图像是长任务，不要用同步 HTTP 阻塞前端。推荐：

```
FastAPI submit task
  ↓
Redis/RQ queue
  ↓
worker generate
  ↓
SSE progress
  ↓
frontend gallery
```

1. **显存/统一内存优化**
    使用 attention slicing、VAE tiling、降低 batch、分离 base/refiner、限制最大分辨率。
2. **统一生成审计 manifest**
    对 L-Port 很关键：

```
{
  "task_id": "...",
  "model": "...",
  "prompt": "...",
  "negative_prompt": "...",
  "seed": 42,
  "steps": 30,
  "scheduler": "Euler",
  "loras": [],
  "control": [],
  "mask": "...",
  "output": "...",
  "created_at": "..."
}
```

## 8. 面试深度解析

**Q1：LoRA 在扩散模型里通常注入哪里？**
 答题思路：常见注入 UNet attention 层，也可能涉及 text encoder；作用是以低秩矩阵调整模型特定概念/风格/角色表达，优点是参数少、可组合，风险是冲突和过拟合。

**Q2：ControlNet 和 IP-Adapter 的条件控制差别是什么？**
 答题思路：ControlNet 更偏结构控制，如 pose、edge、depth；IP-Adapter 更偏图像参考语义/风格/身份控制。二者都可与文本 prompt 组合，但控制维度不同。

**Q3：inpaint 的关键数据流是什么？**
 答题思路：原图、mask、prompt、latent 噪声共同决定输出。mask 白区通常表示重绘区域，黑区保留区域；工程上要检查 mask 尺寸、边缘羽化、mask 外变化率。

------

# Week 4：SAM 2 —— 图像与视频统一分割基础模型

## 1. 技术背景与核心原理

SAM 2 是 Meta 提出的面向图像和视频的 promptable segmentation foundation model。官方介绍强调它把 SAM 的提示式分割能力扩展到视频，并通过 per-session memory 追踪目标；论文也描述了 streaming memory 用于实时视频处理。

这一周的核心是把你从 YOLO 框级检测升级到像素级 mask 工程。对 AIGC 来说，mask 是和 image、prompt、control image 平级的一等数据类型。没有高质量 mask，就无法可靠做局部重绘、背景替换、角色分离、视频抠像和多帧一致性编辑。

## 2. 详细技术栈与架构设计

核心栈：

```
Python
PyTorch
SAM 2 official repo
OpenCV
Pillow
numpy
scikit-image
FastAPI
pydantic
```

前端栈：

```
Vue3
TypeScript
Canvas
Konva.js 或 Fabric.js
File upload
Mask overlay preview
SSE task progress
```

推荐架构：

```
sam2-mask-service/
  api/
    routes_segment.py
  services/
    image_predictor.py
    video_predictor.py
    mask_refiner.py
  schemas/
    segment_request.py
    segment_result.py
  eval/
    mask_quality.py
    video_iou.py
  frontend/
    mask_canvas.vue
  reports/
    mask_quality_report.md
```

API 设计：

```
POST /segment/image
POST /segment/video
POST /segment/refine
GET  /tasks/{task_id}/events
GET  /masks/{mask_id}
```

## 3. 项目实战详细描述

最终项目是一个 SAM 2 mask 服务：用户上传图片或短视频，前端点选目标或画 box，后端输出 mask、透明 PNG、bbox、面积、边缘质量和视频跨帧 mask。

企业价值：它可以作为 AIGC 局部编辑、商品图抠图、视频素材处理、数据标注、自动 inpaint 的基础服务。

## 4. 数据集与评测基准

推荐数据：

```
图像：
  COCO val2017 segmentation
  LVIS 小样本
  自建商品图/人物图/二次元图 50 张

视频：
  DAVIS
  YouTube-VOS 小样本
  自己剪 5-10 秒短视频
```

COCO 是大型检测、分割、captioning 数据集，可用于构造基础 mask 评测样本。

Gold Set：

```
{"id":"img_001","image":"person.png","prompt_type":"point","points":[[320,420]],"expected_object":"person"}
{"id":"img_002","image":"product.png","prompt_type":"box","box":[100,80,500,600],"expected_object":"bag"}
{"id":"vid_001","video":"cat_5s.mp4","frame0_point":[200,180],"target":"cat"}
```

评测指标：

```
单图：
  mask area ratio
  boundary smoothness
  holes count
  bbox-mask consistency
  human accept rate

视频：
  frame-to-frame IoU
  area jitter
  mask disappearance count
  correction count
```

## 5. 核心开源项目与参考链接

必须看：

- `facebookresearch/sam2` 官方仓库。
- Meta SAM 2 官方介绍。
- SAM 2 paper / OpenReview。
- DAVIS / YouTube-VOS：视频分割评测集。

## 6. 极简复现与避坑指南

### Step 1：安装

```
conda create -n sam2lab python=3.11 -y
conda activate sam2lab

git clone https://github.com/facebookresearch/sam2.git
cd sam2
pip install -e .
pip install fastapi uvicorn opencv-python pillow scikit-image
```

### Step 2：下载 checkpoint

按官方 README 下载 tiny/small/base/large。32GB Mac 建议先用 tiny 或 small，验证服务链路后再换大模型。

```
sam2_hiera_tiny
sam2_hiera_small
sam2_hiera_base_plus
sam2_hiera_large
```

### Step 3：单图分割

伪代码结构：

```
import cv2
import numpy as np
from PIL import Image

# 具体 predictor 初始化以官方 repo 当前 API 为准
image = np.array(Image.open("inputs/person.jpg").convert("RGB"))

points = np.array([[320, 420]])
labels = np.array([1])

# masks, scores, logits = predictor.predict(
#     point_coords=points,
#     point_labels=labels,
#     multimask_output=True,
# )
```

### Step 4：mask 质量检测

```
import cv2
import numpy as np

def mask_stats(mask: np.ndarray) -> dict:
    mask = (mask > 0).astype("uint8")
    area = int(mask.sum())
    h, w = mask.shape
    ratio = area / (h * w)

    num_labels, labels = cv2.connectedComponents(mask)
    holes = num_labels - 1

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    perimeter = sum(cv2.arcLength(c, True) for c in contours)

    return {
        "area": area,
        "area_ratio": ratio,
        "components": holes,
        "perimeter": perimeter,
    }
```

### Step 5：前端 mask 叠加

前端不要只显示二值图，要显示：

```
原图
半透明 mask overlay
点/框 prompt
mask 边界线
面积与质量指标
```

Apple Silicon 避坑：

```
1. SAM2 视频模式比单图更吃内存，先限制视频长度、FPS、分辨率。
2. 先把输入 resize 到 720p 或 1024 边长验证链路。
3. 视频 mask 输出不要全存在内存，逐帧写入磁盘或压缩为 RLE。
4. 前端上传大视频必须走异步任务，不要阻塞 HTTP。
```

## 7. 进阶工程优化方向

1. **mask 数据结构标准化**
    同时保存：

```
binary png
rgba overlay png
bbox
polygon
RLE
quality metrics
```

1. **mask refine 流程**
    支持用户追加 positive point / negative point / box 修正，记录每次交互历史。
2. **AIGC inpaint 联动**
    Week 4 输出 mask，Week 3 Diffusers inpaint 直接消费 mask。mask 外区域变化率作为评测指标。

## 8. 面试深度解析

**Q1：为什么说 mask 是 AIGC 系统的一等数据类型？**
 答题思路：因为局部重绘、背景替换、主体保持、视频编辑都依赖 mask；mask 不是临时 UI 结果，而是可存储、可审计、可评测、可复用的控制条件。

**Q2：视频分割相比单图分割难在哪里？**
 答题思路：跨帧一致性、目标遮挡、运动模糊、mask 漂移、目标消失与重现。SAM2 通过 memory 机制改善视频目标追踪。

**Q3：如何评估 mask 质量？**
 答题思路：有 GT 时用 IoU/Dice；无 GT 时看面积突变、连通域、孔洞、边缘抖动、mask 外 inpaint 变化率和人工 accept rate。

------

# Week 5：Qwen-VL / Qwen3-VL —— 中文多模态与文档视觉理解

## 1. 技术背景与核心原理

Qwen-VL 系列适合中文 OCR、文档理解、图表问答、截图理解、公式与论文页面理解。Qwen2.5-VL 在 Transformers 文档中被定义为多模态视觉语言模型，包含 3B、7B、72B 等规模，并引入窗口注意力、动态 FPS 采样和 MRoPE 等机制来增强视觉与视频理解。

截至当前路线规划，Qwen3-VL 已有官方仓库与模型卡，官方示例强调可通过 Transformers 和 ModelScope 使用，且 Qwen3-VL 仓库说明需要较新的 Transformers 版本；如果本地版本报模型类缺失，优先从 Transformers main 分支安装。

## 2. 详细技术栈与架构设计

核心栈：

```
Python
PyTorch
Transformers
qwen-vl-utils
accelerate
Pillow
OpenCV
pydantic
jsonlines
pandas
```

可选：

```
PEFT / LoRA
bitsandbytes，仅 CUDA 更常用
ModelScope
vLLM，视模型支持情况
FastAPI
SSE
```

推荐目录：

```
qwen-vl-doc-agent/
  infer/
    infer_caption.py
    infer_ocr.py
    infer_chartqa.py
    parse_paper_page.py
  schemas/
    document_parse_result.py
    chart_answer.py
  datasets/
    gold_docvqa.jsonl
    samples/
  eval/
    evaluate_doc_vqa.py
    doc_vqa_eval.md
  api/
    routes_vlm.py
  frontend/
    doc_viewer.vue
```

结构化输出 schema：

```
from pydantic import BaseModel

class DocumentParseResult(BaseModel):
    title: str | None
    page_type: str
    language: str
    ocr_text: list[str]
    tables: list[dict]
    figures: list[dict]
    formulas: list[str]
    answer: str | None
    evidence_regions: list[dict]
    confidence: float
```

## 3. 项目实战详细描述

最终项目是 `qwen-vl-doc-agent`：上传论文截图、表格截图、图表图片或中文文档页，模型输出 OCR、版面元素、图表问答答案和结构化 JSON。

企业价值：中文业务场景里，大量知识不在纯文本里，而在 PDF 扫描件、截图、表格、图表、票据、合同页面中。VLM 文档理解是 RAG 进入企业文档场景的前置能力。

## 4. 数据集与评测基准

推荐数据：

```
DocVQA:
  HuggingFaceM4/DocumentVQA
  lmms-lab/DocVQA

ChartQA:
  HuggingFaceM4/ChartQA
  lmms-lab/ChartQA

OCR/Text:
  facebook/textvqa
  howard-hou/OCR-VQA
```

DocVQA 论文数据集包含约 50,000 个问题、12,000+ 文档图像；ChartQA 面向图表视觉与逻辑推理问答；TextVQA 要求模型读取并推理图像中的文字。

自建 Gold Set：

```
{"id":"doc_001","image":"paper_page_1.png","question":"这页论文的主要贡献是什么？","answer_keywords":["防泄漏","RFECV","CNN-BiLSTM"]}
{"id":"chart_001","image":"chart_1.png","question":"最高柱对应哪个模型？","answer":"ISSA-CNN-BiLSTM"}
{"id":"ocr_001","image":"wps_formula_error.png","question":"图中公式报错的原因是什么？","answer_keywords":["LaTeX","格式"]}
```

评测：

```
OCR exact / fuzzy match
Answer keyword recall
Chart numerical accuracy
JSON schema valid rate
Evidence region correctness
Hallucination count
```

## 5. 核心开源项目与参考链接

必须看：

- `QwenLM/Qwen3-VL` 官方仓库。
- Qwen3-VL Hugging Face Transformers 文档。
- Qwen2.5-VL Hugging Face 模型卡与 Transformers 文档。
- Qwen-VL 原始仓库，用于理解早期输入格式与视觉编码路线。

## 6. 极简复现与避坑指南

### Step 1：环境

```
conda create -n qwen-vl python=3.11 -y
conda activate qwen-vl

pip install -U torch torchvision torchaudio
pip install -U accelerate pillow opencv-python qwen-vl-utils pydantic jsonlines
pip install -U git+https://github.com/huggingface/transformers
```

如果你在中国大陆网络环境，优先 ModelScope 下载；如果在 Hugging Face 下载，建议提前登录并配置缓存目录。

### Step 2：选择模型

32GB Apple Silicon 建议：

```
本地 Mac：
  Qwen2.5-VL-3B-Instruct
  Qwen3-VL-4B/8B，如果有可用低精度方案

云 GPU：
  Qwen2.5-VL-7B-Instruct
  Qwen3-VL-8B-Instruct
  更大模型只做 API 或云端评测
```

### Step 3：推理输入格式

典型 messages：

```
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "inputs/chart.png"},
            {"type": "text", "text": "请读取图表，并回答最高柱对应哪个模型。"},
        ],
    }
]
```

### Step 4：结构化文档解析 Prompt

```
你是文档视觉解析器。请只基于图像内容输出 JSON。
字段：
- page_type: paper/table/chart/formula/screenshot/other
- ocr_text: 按阅读顺序提取文字
- tables: 表格结构
- figures: 图像或图表说明
- formulas: 公式原文
- answer: 对用户问题的回答
- evidence_regions: 支持答案的区域描述
不确定时写 null，不要编造。
```

### Step 5：评测脚本

```
def keyword_recall(pred: str, keywords: list[str]) -> float:
    pred = pred.lower()
    hit = sum(1 for k in keywords if k.lower() in pred)
    return hit / max(len(keywords), 1)
```

Apple Silicon 避坑：

```
1. VLM 的图像 token 很吃上下文，图片分辨率不要无限增大。
2. 多图输入比单图输入内存压力大很多。
3. 文档 OCR 任务温度设低：temperature=0 或 0.1。
4. 输出 JSON 时必须加 schema 校验和失败重试。
5. LoRA 训练优先上 CUDA；Mac 本地做 dry-run 验证数据格式即可。
```

## 7. 进阶工程优化方向

1. **文档切页与区域裁剪**
    不要整篇 PDF 直接丢给 VLM。先做 page image，再做 layout crop：

```
page → title/table/figure/formula regions → region-level VLM → merge JSON
```

1. **OCR 与 VLM 双轨**
    OCR 负责高召回文字提取，VLM 负责版面理解和推理；不要指望 VLM 替代全部 OCR。
2. **Evidence Region**
    答案必须附带证据区域。没有 evidence 的文档问答在企业场景不可审计。

## 8. 面试深度解析

**Q1：OCR 和 VLM 文档理解有什么区别？**
 答题思路：OCR 主要识别文字；VLM 还能理解布局、图表、区域关系、视觉符号和问题意图。工程上两者应互补。

**Q2：为什么文档 VQA 容易幻觉？**
 答题思路：图像分辨率、文字太小、表格结构复杂、模型先验强、prompt 未要求证据。解决方案是裁剪、OCR 辅助、schema 输出、evidence region、拒答策略。

**Q3：如何把 VLM 接入 RAG？**
 答题思路：VLM 先把页面转成结构化 JSON/text chunks，并保留 page_id、bbox、image_path；后续向量检索召回文本，必要时再调用 VLM 看原图验证。

------

# Week 6：LLaVA-NeXT —— 经典开源视觉语言模型路线

## 1. 技术背景与核心原理

LLaVA 是开源 VLM 的经典架构路线：vision encoder 提取视觉特征，projector 将视觉特征映射到 LLM token 空间，LLM 负责语言推理，再通过 visual instruction tuning 学会图文问答。LLaVA-NeXT 官方博客强调其相较 LLaVA-1.5 在 reasoning、OCR 和 world knowledge 上有提升。

这周不只是调用图像问答，而是理解 VLM 的基本范式：

```
image
  ↓
vision tower / CLIP ViT
  ↓
projector
  ↓
LLM token space
  ↓
instruction-tuned answer
```

这对你后续做“图像反推 prompt”“SDXL tag 候选生成”“视觉资产解析”很关键。

## 2. 详细技术栈与架构设计

核心栈：

```
Python
PyTorch
Transformers
LLaVA-NeXT
CLIP / ViT
Llama / Vicuna / Qwen backbone
PEFT
Pillow
OpenCV
jsonlines
```

推荐项目结构：

```
llava-next-prompt-assistant/
  infer/
    infer_image_qa.py
    infer_visual_tagging.py
    infer_prompt_reverse.py
  data/
    raw_images/
    instruction_100.jsonl
  convert/
    convert_dataset.py
  schemas/
    prompt_reverse_schema.py
    visual_tag_result.py
  eval/
    visual_tagging_report.md
  docs/
    architecture.md
    interview_notes.md
```

输出 schema：

```
class VisualTagResult(BaseModel):
    objects: list[str]
    characters: list[str]
    scene: list[str]
    style: list[str]
    composition: list[str]
    lighting: list[str]
    uncertainty: list[str]
    candidate_prompt: str
```

## 3. 项目实战详细描述

最终项目是 `llava-next-prompt-assistant`：输入图片，输出图像问答、物体计数、空间关系分析、OCR 粗读、视觉标签候选和结构化 prompt 反推结果。

企业价值：它可以作为视觉内容理解层，为 AIGC prompt 生成、图像审核、素材检索、数据标注和 L-Port 视觉蓝图生成提供输入。

## 4. 数据集与评测基准

推荐数据：

```
VQA:
  VQAv2
  GQA
  TextVQA
  DocVQA 小样本

多模态指令：
  LLaVA instruction data
  M3IT
  自建 100 条图像问答 instruction

图像反推：
  自己的 ComfyUI 输出图 + 原 prompt
  COCO captions 小样本
```

自建 Gold Set：

```
{"image":"anime_001.png","question":"画面中主体数量是多少？","answer":"1"}
{"image":"chart_001.png","question":"图中是否包含柱状图？","answer":"是"}
{"image":"aigc_001.png","task":"reverse_prompt","must_tags":["1girl","close-up","soft lighting"]}
```

评测：

```
VQA exact match
tag recall
object hallucination rate
counting accuracy
spatial relation accuracy
prompt candidate human score
```

## 5. 核心开源项目与参考链接

必须看：

- `LLaVA-VL/LLaVA-NeXT` 官方仓库。
- LLaVA-NeXT 官方博客。
- LLaVA OneVision tutorials。
- LLaVA paper：Visual Instruction Tuning。
- CLIP paper：理解 vision-language 对齐基础。

## 6. 极简复现与避坑指南

### Step 1：环境

```
conda create -n llava-next python=3.11 -y
conda activate llava-next

pip install -U torch torchvision torchaudio
pip install -U git+https://github.com/LLaVA-VL/LLaVA-NeXT.git
pip install -U transformers accelerate pillow opencv-python jsonlines pydantic
```

### Step 2：选择模型

32GB Mac 本地跑 LLaVA-NeXT 可能吃力。建议：

```
Mac：
  用较小 HF 版本做推理格式验证
  或使用云端/远程 GPU 暴露 OpenAI-compatible API

云 GPU：
  LLaVA-NeXT-7B
  LLaVA-OneVision-7B
```

### Step 3：构造 instruction 数据

```
{"image":"images/001.png","conversations":[{"from":"human","value":"<image>\n请描述图像主体。"},{"from":"gpt","value":"画面中有一名少女，背景是夜晚樱花。"}]}
```

### Step 4：图像反推 Prompt

Prompt 模板：

```
你是 AIGC 图像标注助手。请把图片转成结构化视觉标签。
只输出 JSON：
{
  "subject": [],
  "pose": [],
  "expression": [],
  "clothing": [],
  "scene": [],
  "composition": [],
  "lighting": [],
  "style": [],
  "uncertain": []
}
不要编造看不见的角色名、画师名、IP 名。
```

### Step 5：评测 hallucination

```
def hallucination_rate(pred_tags: list[str], forbidden_tags: list[str]) -> float:
    if not pred_tags:
        return 0.0
    bad = sum(1 for t in pred_tags if t in forbidden_tags)
    return bad / len(pred_tags)
```

避坑：

```
1. VLM 很容易把未知角色误判成知名 IP，角色/IP 标签必须标 uncertain。
2. 图像反推 prompt 不能当最终真值，只能当 candidate。
3. OCR、计数、空间关系要分任务评测，不要用一个总分掩盖问题。
4. 微调前先验证 tokenizer、image token、conversation template。
```

## 7. 进阶工程优化方向

1. **视觉标签 candidate-only 设计**
    输出必须带置信度和不确定项：

```
{"tag":"blue eyes","confidence":0.86,"source":"vlm","status":"candidate"}
```

1. **与 SDXL/Anima tag glossary 联动**
    VLM 输出自然语言 → tag 检索 → rerank → risk filter → prompt assembler。
2. **多模型互审**
    Qwen-VL 更适合中文/OCR，LLaVA-NeXT 更适合理解 VLM 架构。可以让二者互相验证高风险标签。

## 8. 面试深度解析

**Q1：VLM 为什么需要 projector？**
 答题思路：vision encoder 输出的视觉特征空间和 LLM token embedding 空间不同，projector 负责把视觉特征映射成 LLM 可消费的视觉 token 表示。

**Q2：visual instruction tuning 解决什么问题？**
 答题思路：让模型学会根据图像和自然语言指令进行对话式回答，而不仅是图文对齐或 caption。

**Q3：为什么 VLM 输出不能直接作为生成模型 prompt 真值？**
 答题思路：VLM 可能误识别角色/IP/画师/细节；工程上应视为候选，经过检索、校验、risk flag 和人工/规则审核后才能进入最终 prompt。

------

# Week 7：LangChain / LangGraph —— 企业级 RAG-Agent 工程化

## 1. 技术背景与核心原理

LangChain 是模型、Prompt、Retriever、Tool、OutputParser 等组件的应用开发框架；LangGraph 是面向复杂 Agent 的编排运行时，官方文档将其定位为支持 durable execution、streaming、human-in-the-loop、persistence 的 orchestration runtime。LangSmith 则用于 tracing、evaluation、prompt 和 deployment 等可观测与评测能力。

这一周要避免低级 PDF QA，而是做企业级 RAG-Agent 原型：

```
可观测：每次检索、重排、生成、验证都可 trace
可评测：Recall@K、Faithfulness、Citation Accuracy 可量化
可恢复：工具失败、检索不足、模型超时有 fallback
可接入：OpenAI-compatible 本地模型或云模型都能挂载
```

## 2. 详细技术栈与架构设计

核心栈：

```
Python
LangChain
LangGraph
LangSmith 或自研 trace
FastAPI
SSE
Pydantic
Chroma / FAISS / Qdrant
BM25S 或 rank_bm25
sentence-transformers
CrossEncoder reranker
pypdf / pymupdf
markdown-it-py
unstructured，可选
```

推荐架构：

```
enterprise-rag-agent/
  app/
    ingestion/
      loaders.py
      splitters.py
      index_builder.py
    retrieval/
      exact_retriever.py
      vector_retriever.py
      hybrid_retriever.py
      reranker.py
    chains/
      rag_chain.py
      answer_with_citations.py
    graphs/
      state.py
      nodes.py
      rag_agent_graph.py
    tools/
      search_tool.py
      file_lookup_tool.py
      calculator_tool.py
    tracing/
      trace_logger.py
      run_recorder.py
    eval/
      rag_gold_set.jsonl
      evaluate_rag.py
    api/
      routes_rag.py
      routes_agent.py
  frontend/
    chat.vue
    trace_panel.vue
  docs/
    architecture.md
    interview_notes.md
```

LangGraph 状态：

```
from typing import TypedDict

class AgentState(TypedDict):
    question: str
    rewritten_query: str | None
    route: str | None
    retrieved_docs: list[dict]
    reranked_docs: list[dict]
    selected_tools: list[str]
    draft_answer: str | None
    verified_answer: str | None
    citations: list[dict]
    errors: list[dict]
    trace_id: str
```

SSE 事件：

```
query_rewrite
retrieval_start
retrieval_hit
rerank_done
token_delta
citation_ready
verify_done
fallback
error
done
```

## 3. 项目实战详细描述

最终项目是 `enterprise-rag-agent`：支持 Markdown/PDF/txt ingestion、hybrid retrieval、rerank、带引用回答、LangGraph classify → retrieve → answer → verify → fallback 状态机、SSE streaming 和 eval 报告。

企业价值：这是真实大模型应用工程师最常见工作场景。企业并不缺“能问 PDF 的 demo”，缺的是可追踪、可评估、可恢复、能上线维护的 RAG-Agent 系统。

## 4. 数据集与评测基准

推荐数据：

```
公开检索评测：
  BEIR
  MS MARCO passage
  Natural Questions 小样本

RAG 评测：
  自建企业文档 Gold Set
  RAGAS metrics
```

BEIR 是异构信息检索基准，覆盖多类 IR 任务，可用于评估 retriever；Ragas 官方提供 RAG 和 Agentic workflow 的评测指标，如 context recall 等。

Gold Set：

```
{
  "id": "rag_001",
  "question": "L-Port 的核心边界是什么？",
  "answer": "标准 IO 编排、candidate-only、provenance、risk flags、fallback honesty。",
  "must_cite": ["docs/lport_arch.md#chunk_12"],
  "type": "local_fact"
}
{
  "id": "rag_002",
  "question": "如果检索不到证据，系统应该如何回答？",
  "answer": "应拒答或请求更多材料，不能编造。",
  "must_behavior": "fallback"
}
```

评测指标：

```
Retrieval:
  Recall@K
  MRR
  Hit@K
  chunk coverage

Generation:
  answer correctness
  faithfulness
  citation accuracy
  refusal correctness

System:
  latency
  timeout rate
  trace completeness
  streaming stability
```

## 5. 核心开源项目与参考链接

必须看：

- LangGraph overview：重点理解 state、edge、durable execution、streaming。
- LangSmith observability/evaluation：理解 trace、latency、cost、debug。
- Ragas metrics 文档。
- BEIR 官方仓库。

## 6. 极简复现与避坑指南

### Step 1：环境

```
conda create -n rag-agent python=3.11 -y
conda activate rag-agent

pip install -U langchain langgraph langchain-community langchain-openai
pip install -U fastapi uvicorn sse-starlette pydantic
pip install -U chromadb sentence-transformers rank-bm25 pypdf pymupdf
pip install -U ragas datasets pandas jsonlines httpx
```

### Step 2：接入本地 llama.cpp

```
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed",
    model="local-qwen",
    temperature=0.2,
)
```

### Step 3：文档切分与索引

```
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

loader = PyPDFLoader("docs/project.pdf")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
)

chunks = splitter.split_documents(docs)

emb = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
db = Chroma.from_documents(chunks, emb, persist_directory="indexes/chroma")
```

### Step 4：LangGraph 状态机

```
from langgraph.graph import StateGraph, END

def classify(state):
    q = state["question"]
    route = "document_qa" if "文档" in q or "根据资料" in q else "general"
    return {"route": route}

def retrieve(state):
    docs = db.similarity_search(state["question"], k=6)
    return {"retrieved_docs": [d.dict() for d in docs]}

def answer(state):
    context = "\n\n".join(d["page_content"] for d in state["retrieved_docs"])
    prompt = f"只基于证据回答，并给出引用。\n证据：{context}\n问题：{state['question']}"
    res = llm.invoke(prompt)
    return {"draft_answer": res.content}

def verify(state):
    if not state["retrieved_docs"]:
        return {"verified_answer": "没有足够证据，无法回答。"}
    return {"verified_answer": state["draft_answer"]}

graph = StateGraph(dict)
graph.add_node("classify", classify)
graph.add_node("retrieve", retrieve)
graph.add_node("answer", answer)
graph.add_node("verify", verify)

graph.set_entry_point("classify")
graph.add_edge("classify", "retrieve")
graph.add_edge("retrieve", "answer")
graph.add_edge("answer", "verify")
graph.add_edge("verify", END)

app = graph.compile()
```

### Step 5：SSE Streaming

```
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import json

api = FastAPI()

@api.get("/agent/stream")
async def stream_agent(q: str):
    async def event_gen():
        yield {"event": "start", "data": json.dumps({"question": q})}
        result = app.invoke({"question": q, "errors": []})
        yield {"event": "done", "data": json.dumps(result, ensure_ascii=False)}
    return EventSourceResponse(event_gen())
```

Apple Silicon 避坑：

```
1. embedding 模型用 small/base，不要一开始上 bge-m3 大模型。
2. 本地 LLM 负责 answer，embedding/rerank 可以独立模型，不要全塞进一个模型。
3. PDF 解析优先 pymupdf，复杂扫描件交给 Week 5 VLM/OCR。
4. 本地 llama.cpp 并发不要过高，RAG pipeline 里检索和生成要分开计时。
```

## 7. 进阶工程优化方向

1. **Hybrid Retrieval**
    不要只做 vector top-k。组合：

```
BM25 lexical recall
+ vector semantic recall
+ metadata filter
+ cross-encoder rerank
```

1. **Citation Verification**
    回答句子必须能映射到 chunk_id/span。没有 citation 的关键陈述要么删除，要么标注“不确定”。
2. **Trace Schema**
    自研 trace 至少记录：

```
{
  "trace_id": "...",
  "question": "...",
  "rewritten_query": "...",
  "retrieved_chunks": [],
  "rerank_scores": [],
  "prompt": "...",
  "model": "...",
  "latency_ms": 1234,
  "errors": []
}
```

## 8. 面试深度解析

**Q1：LangChain 和 LangGraph 的区别是什么？**
 答题思路：LangChain 提供组件抽象和组合；LangGraph 提供状态机、条件边、循环、checkpoint、resume，更适合复杂 Agent。

**Q2：为什么 RAG 不能只做 top-k vector search？**
 答题思路：向量检索对关键词、编号、实体、日期、表格字段可能召回差；需要 BM25、metadata filter、rerank、query rewrite 和 eval 闭环。

**Q3：企业 RAG 如何判断答案可信？**
 答题思路：检索命中、引用准确、答案忠实、无证据拒答、trace 可回放、Gold Set 回归测试。

------

# Week 8：GraphRAG —— 图谱增强检索生成系统

## 1. 技术背景与核心原理

GraphRAG 是图谱增强 RAG，不是普通向量检索。Microsoft GraphRAG 官方文档将其描述为结构化、层次化的 RAG 方法：从原始文本抽取知识图谱，构建社区层级，生成社区摘要，再利用这些结构进行 RAG 任务。

其核心流程：

```
documents
  ↓
entity extraction
  ↓
relationship extraction
  ↓
knowledge graph
  ↓
community detection
  ↓
community summaries
  ↓
global search / local search / DRIFT search
```

普通 RAG 更擅长回答局部事实；GraphRAG 更擅长跨文档、全局总结、多跳关系、实体密集问题。

## 2. 详细技术栈与架构设计

核心栈：

```
Python
Microsoft GraphRAG
NetworkX
Neo4j，可选
Pandas
Parquet
LLM extractor
VectorStore
LangChain Retriever interface
```

推荐目录：

```
graph-rag-lab/
  input/
    documents/
  graphrag_config/
    settings.yaml
  scripts/
    ingest_documents.py
    build_graph.py
    query_global.py
    query_local.py
    export_to_neo4j.py
  adapters/
    langchain_graph_retriever.py
  reports/
    rag_vs_graphrag.md
    graph_quality_report.md
  docs/
    architecture.md
    interview_notes.md
```

GraphRAG 作为 Week 7 Tool：

```
LangGraph Agent
  ↓
route question
  ├─ local factual question → normal RAG retriever
  ├─ entity relationship question → GraphRAG local search
  └─ global summary question → GraphRAG global search
```

## 3. 项目实战详细描述

最终项目是 `graph-rag-lab`：用你的项目文档、论文材料或 L-Port 文档构建知识图谱，对比普通 RAG 和 GraphRAG 在全局问题、多跳问题、实体关系问题上的差异，并封装成 LangChain Retriever/Tool。

企业价值：企业知识库往往不是孤立段落，而是人、项目、产品、事件、合同、系统模块之间的关系网络。GraphRAG 适合做战略分析、知识聚合、长文档总结、项目脉络追踪。

## 4. 数据集与评测基准

推荐数据：

```
自有：
  L-Port 架构文档
  项目审计报告
  论文材料
  README + issues + changelog

公开：
  HotpotQA 小样本
  WikiHop
  MuSiQue
  多跳问答数据集
```

Gold Set：

```
{"id":"global_001","question":"L-Port 当前主线经历了哪些方向转移？","type":"global_summary","must_cover":["SDXL","Anima","外部工具编排"]}
{"id":"local_001","question":"CharacterAnchorResolver 位于哪个阶段之间？","type":"entity_local","answer":"AnimaIRReadinessValidator 之后、AnimaIntentAssembler 之前"}
{"id":"multi_001","question":"为什么角色解析失败不能归因到 8B 本地模型？","type":"multi_hop","must_cover":["外部资产解析","LLM 不负责 canonical tag"]}
```

评测：

```
global coverage
entity recall
relationship correctness
community summary usefulness
普通 RAG vs GraphRAG 答案差异
人工事实核查
```

## 5. 核心开源项目与参考链接

必须看：

- `microsoft/graphrag` 官方仓库。
- Microsoft GraphRAG 官方文档。
- GraphRAG paper：A Graph RAG Approach to Query-Focused Summarization。
- GraphRAG local search 文档：理解实体相关问题的检索方式。
- Microsoft Research GraphRAG 项目页：了解 global/local/DRIFT Search 方向。

## 6. 极简复现与避坑指南

### Step 1：环境

```
conda create -n graphrag-lab python=3.11 -y
conda activate graphrag-lab

pip install -U graphrag pandas networkx pyarrow
pip install -U langchain langgraph pydantic
```

### Step 2：准备文档

```
input/
  documents/
    lport_architecture.md
    anima_audit.md
    c2_report.md
    c3_blueprint.md
```

### Step 3：初始化 GraphRAG

命令以当前官方 CLI 为准，典型流程是：

```
python -m graphrag.index --init --root .
```

配置：

```
llm:
  type: openai_chat
  model: local-qwen-or-cloud
  api_base: http://localhost:8080/v1

embeddings:
  type: openai_embedding
  model: local-embedding-or-bge
```

如果本地 llama.cpp 对抽取质量不稳定，建议先用强模型构建 graph，再用本地模型做 query 实验。GraphRAG 的抽取阶段比普通 RAG 更依赖模型稳定性。

### Step 4：构建索引

```
python -m graphrag.index --root .
```

检查输出：

```
entities.parquet
relationships.parquet
communities.parquet
community_reports.parquet
text_units.parquet
```

### Step 5：查询对比

```
python -m graphrag.query \
  --root . \
  --method global \
  "这个项目的整体技术路线是什么？"

python -m graphrag.query \
  --root . \
  --method local \
  "CharacterAnchorResolver 的职责是什么？"
```

Apple Silicon 避坑：

```
1. 图谱构建阶段 LLM 调用多，本地模型会慢；先小语料验证。
2. 抽取 prompt 对模型能力要求高，弱模型容易抽错实体关系。
3. GraphRAG 不是替代普通 RAG，而是补充全局/多跳问题。
4. Parquet 中间产物要纳入版本管理或至少记录 checksum。
```

## 7. 进阶工程优化方向

1. **实体规范化**
    同一实体可能有多个别名：

```
大黑塔
The Herta
Herta
大黑塔(星穹铁道)
```

要做 canonical entity resolution。

1. **GraphRAG + Vector RAG 路由**
    问题分类：

```
局部事实 → Vector RAG
全局总结 → GraphRAG global
实体关系 → GraphRAG local
```

1. **图谱质量评测**
    抽样检查：

```
entity 是否真实
relationship 是否有证据
community summary 是否覆盖核心主题
是否引入幻觉关系
```

## 8. 面试深度解析

**Q1：GraphRAG 相比普通 RAG 的核心优势是什么？**
 答题思路：普通 RAG 召回相似 chunk；GraphRAG 显式建模实体、关系、社区摘要，更适合全局问题、多跳问题和跨文档知识聚合。

**Q2：GraphRAG 最大风险是什么？**
 答题思路：抽取阶段幻觉会污染图谱；社区摘要错误会被放大；构建成本高。必须保留 source span、实体证据和图谱质量评估。

**Q3：GraphRAG 如何接入 LangGraph？**
 答题思路：作为 retriever/tool 接入，由路由节点判断调用普通 retriever、GraphRAG local search 或 global search，并把结果统一成 citation chunks。

------

# Week 9：SWE-agent —— 真实 GitHub Issue 修复 Agent

## 1. 技术背景与核心原理

SWE-agent 的核心是让语言模型使用真实工程工具解决 GitHub issue：读 issue、搜索代码、打开文件、编辑、运行测试、根据错误重试。官方文档将其定位为可让模型自主使用工具修复真实 GitHub 仓库 issue 的系统；SWE-bench 则是衡量 AI 系统解决真实 GitHub issue 能力的基准。

代码 Agent 与普通 RAG Agent 的根本差异：

```
RAG Agent：证据检索 → 回答
SWE Agent：定位问题 → 修改代码 → 运行测试 → 根据反馈修复 → 生成 patch
```

测试结果是最重要的 reward signal。

## 2. 详细技术栈与架构设计

核心栈：

```
Python
Git
pytest
Docker，可选
SWE-agent
mini-swe-agent
ripgrep
tree-sitter，可选
LangGraph，可选复刻状态机
OpenAI-compatible LLM
```

推荐目录：

```
swe-agent-lab/
  tasks/
    issues.jsonl
  repos/
    target_repo/
  tools/
    code_search.py
    open_file.py
    edit_file.py
    run_tests.py
    git_diff.py
  runs/
    run_001/
      trace.jsonl
      patch.diff
      test.log
  reports/
    agent_failure_analysis.md
    issue_resolution_report.md
  docs/
    architecture.md
    interview_notes.md
```

状态机：

```
read_issue
  ↓
repo_map
  ↓
search_code
  ↓
inspect_file
  ↓
plan_patch
  ↓
edit_file
  ↓
run_tests
  ↓
analyze_error
  ├─ pass → final_diff
  └─ fail → search/edit retry
```

## 3. 项目实战详细描述

最终项目是 `swe-agent-lab`：选择一个小型 Python 开源 repo，构造 3-5 个真实 bug issue，运行 SWE-agent 或 mini-swe-agent，记录 search/open/edit/test/retry 全过程，输出 patch 和失败分析。

企业价值：代码 Agent 是最接近真实生产力的 Agent 类型之一。它不靠聊天效果，而靠能否提交通过测试的 patch。

## 4. 数据集与评测基准

推荐：

```
SWE-bench
SWE-bench Verified
自建小 repo issue set
真实 GitHub issue 小样本
```

SWE-bench 收集真实 Python 仓库的 issue/PR 任务，用于测试系统是否能解决 GitHub issue。

自建任务：

```
{"id":"issue_001","repo":"repos/calculator","issue":"divide 函数遇到除数为0时应抛 ValueError，但现在返回 None","test":"pytest tests/test_divide.py"}
{"id":"issue_002","repo":"repos/parser","issue":"parse_config 不支持带空格的 key=value","test":"pytest tests/test_parser.py"}
{"id":"issue_003","repo":"repos/api","issue":"当 name 为空字符串时应返回 400","test":"pytest tests/test_api.py"}
```

评测：

```
resolve rate
test pass rate
patch minimality
number of tool calls
retry count
time to fix
wrong file edit count
regression count
```

## 5. 核心开源项目与参考链接

必须看：

- `swe-agent/swe-agent` 官方仓库。
- SWE-agent 官方文档。
- `SWE-agent/mini-swe-agent`：轻量实现，适合学习核心机制。
- SWE-bench 官方。
- SWE-agent benchmarking 文档：理解 inference 与 evaluation 两阶段。

## 6. 极简复现与避坑指南

### Step 1：环境

```
conda create -n swe-agent-lab python=3.11 -y
conda activate swe-agent-lab

pip install -U swe-agent
pip install -U pytest rich pydantic jsonlines gitpython
```

也可以先看 mini-swe-agent，代码量更小，更适合理解工具循环。

### Step 2：准备目标 repo

```
mkdir -p repos
cd repos
git clone https://github.com/yourname/tiny-python-bug-repo.git
cd tiny-python-bug-repo
pytest
```

### Step 3：构造 issue

```
{
  "issue": "Function parse_bool should accept 'yes' and 'no', but currently only accepts 'true' and 'false'. Please fix it and add tests.",
  "repo": "repos/tiny-python-bug-repo",
  "test_command": "pytest tests/test_parser.py"
}
```

### Step 4：运行 Agent

具体命令以当前 SWE-agent 文档为准。最小原则：

```
输入：
  repo path
  issue text
  model config
  test command

输出：
  patch
  logs
  test result
```

### Step 5：记录 trace

```
{"step":1,"action":"search","query":"parse_bool","result":["src/parser.py","tests/test_parser.py"]}
{"step":2,"action":"open_file","path":"src/parser.py","lines":"1-80"}
{"step":3,"action":"edit","path":"src/parser.py","summary":"add yes/no support"}
{"step":4,"action":"run_tests","cmd":"pytest tests/test_parser.py","status":"failed","error":"expected ValueError"}
{"step":5,"action":"edit","path":"src/parser.py","summary":"fix invalid input handling"}
{"step":6,"action":"run_tests","cmd":"pytest","status":"passed"}
```

Apple Silicon 避坑：

```
1. 本地 7B/8B 代码模型可做小 repo，真实 SWE-bench 建议强云模型。
2. Agent 运行前必须创建 git clean checkpoint。
3. 每次 edit 后立即 git diff，避免大面积无关修改。
4. 测试命令要短而确定，先跑目标测试，再跑全量测试。
5. 不要让 Agent 无限循环，设置 max_steps/max_time。
```

## 7. 进阶工程优化方向

1. **工具约束**
    不允许 Agent 直接重写大文件。工具层限制：

```
max_edit_lines
allowed_paths
forbidden_paths
max_test_runtime
```

1. **测试反馈分层**

```
syntax error → 快速修
unit test fail → 定位断言
integration fail → 查调用链
all pass → 检查 diff minimality
```

1. **接入 Week 7 Trace/Eval**
    把 SWE-agent 的 search/open/edit/test/run 统一写入 Week 7 trace schema，这样你的 Agent 系统就有一致的可观测层。

## 8. 面试深度解析

**Q1：代码 Agent 和普通聊天 Agent 最大区别是什么？**
 答题思路：代码 Agent 必须和真实环境交互，有工具调用、文件修改和测试反馈闭环；最终价值由 patch 是否通过测试决定，而不是回答是否像样。

**Q2：SWE-agent 为什么容易失败？**
 答题思路：定位错误、上下文不足、修改范围过大、测试理解错误、环境不一致、循环试错、把正确代码误修。需要 repo map、检索、测试分层、工具限制和回滚机制。

**Q3：如何评估代码 Agent？**
 答题思路：resolve rate、test pass rate、patch minimality、regression、tool calls、retry count、时间成本；最好用独立隐藏测试或人工 review 防止过拟合公开测试。

------

# 九周最终集成主线

完成 9 周后，你的作品集不应该是 9 个散项目，而应该整合成一个 AI Infra Portfolio：

```
Week 1 MLX LM
  → Apple Silicon 本地实验与微调

Week 2 llama.cpp
  → GGUF / OpenAI-compatible 本地 serving

Week 3 Diffusers
  → 生成式视觉 pipeline

Week 4 SAM 2
  → mask 工程与局部编辑基础

Week 5 Qwen-VL / Qwen3-VL
  → 中文文档与视觉理解

Week 6 LLaVA-NeXT
  → VLM 架构理解与图像反推

Week 7 LangChain / LangGraph
  → 企业级 RAG-Agent 编排

Week 8 GraphRAG
  → 图谱增强检索与全局问答

Week 9 SWE-agent
  → 长任务代码 Agent 与测试反馈闭环
```

最终总集成可以命名为：

```
local-ai-infra-portfolio/
  model_gateway/
    mlx_provider.py
    llamacpp_provider.py
  vision_pipeline/
    diffusers_service.py
    sam2_service.py
  vlm_service/
    qwen_vl_service.py
    llava_service.py
  rag_agent/
    langgraph_app.py
    retrievers/
    eval/
  graphrag/
    graph_retriever.py
  swe_agent/
    code_tools/
    run_traces/
  frontend/
    vue3-dashboard/
  docs/
    architecture.md
    interview_notes.md
    demo_script.md
```

你简历上的核心表述可以是：

> 构建了一套面向 Apple Silicon 与本地模型的 AI Infra 实战系统，覆盖 MLX/llama.cpp 本地推理底座、Diffusers/SAM2 生成式视觉与 mask 工程、Qwen-VL/LLaVA 多模态理解、LangGraph 企业级 RAG-Agent、GraphRAG 图谱增强检索与 SWE-agent 代码修复闭环；所有模块均具备可运行 Demo、评测报告、trace 日志和服务化接口。
