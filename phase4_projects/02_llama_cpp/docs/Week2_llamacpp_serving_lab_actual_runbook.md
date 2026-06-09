# 本地 AI Gateway Serving 底座实战：llama.cpp → GGUF → FastAPI Gateway → Vue3 SSE 全链路

下面这套 Week 2 不是"能跑 llama-server 就行"，而是按 **本地 AI Gateway serving 底座**来做：可编译、可部署、可压测、可观测、可前端联调、可写进简历。你的路线文件也把 Week 2 明确定位为 `llama.cpp → GGUF / OpenAI-compatible 本地 serving`，并要求沉淀 Demo、Eval 报告、Interview Notes。

> **实验机器**：MacBook Air M5，32GB unified memory，macOS 26
> **虚拟环境**：Conda 环境 `cxllm`（Python 3.11），不使用 venv
> **端口**：llama-server 用 8081（8080 被占用），Gateway 用 8000

---

# 0. Week 2 总目标

最终项目名：

```
llamacpp-serving-lab
```

最终你要能讲清楚这条链路：

```
Vue3 前端
  ↓ SSE / fetch stream
FastAPI AI Gateway
  ↓ OpenAI-compatible API proxy
llama-server
  ↓
GGUF 模型权重 + tokenizer + chat template
  ↓
Metal 后端 / 统一内存 / KV Cache / Prompt Cache
```

llama.cpp 官方 server 当前支持 OpenAI-compatible chat completions、responses、embeddings 路由，并支持 parallel decoding、continuous batching、monitoring endpoints 等能力。

---

# 1. 工程化目录架构

```
llamacpp-serving-lab/
├── README.md                         # 项目总说明：环境、启动、压测、结果复现入口
├── Makefile                          # 一键构建、启动、压测、清理命令入口
├── .env.example                      # 网关和 llama-server 的环境变量模板
├── .env                              # 实际环境变量（不进 Git）
├── .gitignore                        # 忽略 models、reports 临时文件、Python 缓存等
│
├── third_party/
│   └── llama.cpp/                    # llama.cpp 源码子目录，建议 git clone 到这里
│
├── models/
│   ├── README.md                     # 模型来源、量化等级、license、checksum 记录
│   ├── qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf   # HF 分片下载的第 1 部分
│   ├── qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf   # HF 分片下载的第 2 部分
│   └── qwen2.5-7b-instruct-q4_k_m.gguf                  # 合并后的完整模型（压测默认）
│
├── configs/
│   ├── gateway.yaml                  # FastAPI Gateway 配置：上游地址、超时、限流、默认模型
│   ├── serving.q4.yaml               # Q4_K_M 启动参数记录
│   ├── serving.q5.yaml               # Q5_K_M 启动参数记录
│   └── benchmark.yaml                # 压测场景配置：并发、prompt、max_tokens、轮次
│
├── scripts/
│   ├── build_llamacpp.sh             # Apple Silicon + Metal 编译脚本
│   ├── serve_q4.sh                   # 启动 Q4_K_M llama-server（端口 8081）
│   ├── smoke_openai.sh               # curl 测试 /v1/chat/completions
│   ├── scrape_metrics.py             # 抓取 /metrics 并保存快照
│   ├── bench_concurrency.py          # httpx + asyncio 并发压测：TTFT / TPS / P95
│   └── test_prompt_cache.sh          # slot save / restore prompt cache 实验脚本
│
├── gateway/
│   ├── __init__.py                   # Python package 标记
│   ├── app.py                        # FastAPI 应用入口，挂载路由和生命周期检查
│   ├── config.py                     # pydantic-settings 配置读取
│   ├── schemas.py                    # OpenAI-compatible 请求/响应 schema 的最小子集
│   ├── llamacpp_client.py            # 上游 llama-server async client，封装非流式和流式调用
│   ├── routes_chat.py                # /v1/chat/completions 代理路由
│   ├── routes_health.py              # /healthz /readyz 健康检查
│   ├── routes_metrics.py             # /gateway/metrics 暴露网关侧指标
│   ├── middleware.py                 # request_id、耗时日志、异常处理
│   └── errors.py                     # 统一错误码与上游异常映射
│
├── frontend/
│   └── vue3-sse-demo/
│       ├── package.json              # Vue3 + TS 最小前端工程依赖
│       ├── src/
│       │   ├── App.vue               # 页面入口
│       │   ├── api/llm.ts            # fetch SSE 流式读取核心逻辑
│       │   └── components/ChatBox.vue # 聊天输入与 token 增量渲染组件
│       └── README.md                 # 前端联调说明
│
├── observability/
│   ├── prometheus.yml                # Prometheus 抓取 llama-server /metrics 的配置
│   ├── grafana_dashboard.json        # 可选：Grafana 面板模板
│   └── metrics_snapshots/            # 每次压测保存的 metrics 文本快照
│
├── reports/
│   ├── latency_matrix.csv            # q4/q5/fp16 × ctx × parallel 的延迟矩阵
│   ├── throughput_matrix.csv         # tokens/s 吞吐矩阵
│   ├── memory_notes.md               # 统一内存、KV cache、parallel slots 估算记录
│   ├── quantization_report.md        # Q4/Q5/FP16 主观质量与性能对比
│   ├── week2_final_report.md         # Week 2 最终实验报告
│   └── slot_cache/                   # prompt cache save/restore 的 .bin 文件
│
├── docs/
│   ├── architecture.md               # 架构图、数据流、边界、异常流
│   ├── gguf_notes.md                 # GGUF、量化、chat template、tokenizer 笔记
│   ├── serving_params.md             # -c/-b/-ub/-ngl/--parallel/--metrics 参数说明
│   ├── kv_cache_math.md              # KV Cache 内存精算公式与实测对照
│   ├── prompt_cache_lab.md           # prompt cache / slot save restore 实验记录
│   └── interview_notes.md            # 面试题、答题思路、复盘
│
└── tests/
    ├── test_gateway_schema.py         # 请求参数校验单测
    ├── test_gateway_health.py         # 健康检查单测
    └── test_sse_parser.py             # SSE token 增量解析单测
```

**Best Practice：** `models/` 不进 Git；模型文件必须记录来源、量化等级、license、下载命令和 checksum。否则你未来复现实验时，根本无法证明"这次 q4 和上次 q4 是同一个文件"。

---

# 2. Day 1：环境、源码编译、Metal 验证

## 2.1 环境说明

本实验使用 **Conda 虚拟环境 `cxllm`**（Python 3.11），不是 venv。所有 Python 命令都在此环境中执行。

```bash
# 确认当前在 cxllm 环境
conda activate cxllm
which python
# 预期：/Users/chenxi/miniconda3/envs/cxllm/bin/python
```

项目路径（此后所有操作的基础目录）：

```bash
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/llamacpp-serving-lab
```

## 2.2 创建项目目录结构

```bash
mkdir -p third_party models configs scripts gateway frontend observability reports docs tests
touch README.md Makefile .env.example .gitignore
```

`.gitignore`：

```
# Python
__pycache__/
*.pyc
.venv/
.env

# Models
models/*.gguf
models/*.bin
models/*.safetensors

# Reports runtime
reports/*.tmp
observability/metrics_snapshots/*.txt

# macOS
.DS_Store

# llama.cpp build
third_party/llama.cpp/build/
```

## 2.3 Python 依赖安装

```bash
conda activate cxllm
pip install -U pip
pip install fastapi uvicorn[standard] httpx pydantic pydantic-settings prometheus-client orjson rich pandas numpy
```

已安装的关键包版本（实际）：

| 包               | 版本    |
| ---------------- | ------- |
| fastapi          | 0.136.3 |
| uvicorn          | 0.49.0  |
| httpx            | 0.28.1  |
| pydantic         | 2.13.4  |
| pydantic-settings| 2.14.1  |
| prometheus_client| 0.24.1  |
| orjson           | 3.11.9  |
| rich             | 15.0.0  |
| pandas           | 3.0.2   |
| numpy            | 2.4.4   |

## 2.4 编译 llama.cpp

`llama.cpp` 官方文档说明：macOS 下 Metal 默认启用，使用 Metal 会让计算跑在 GPU 上；需要禁用时才传 `-DGGML_METAL=OFF`。官方构建流程是 `cmake -B build` 然后 `cmake --build build --config Release`。

`scripts/build_llamacpp.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TP_DIR="${ROOT_DIR}/third_party"

mkdir -p "${TP_DIR}"
cd "${TP_DIR}"

if [ ! -d "llama.cpp" ]; then
  git clone https://github.com/ggml-org/llama.cpp
fi

cd llama.cpp
git pull

# Apple Silicon 生产建议：
# -DGGML_METAL=ON       显式打开 Metal，虽然 macOS 默认打开，但这里写清楚，避免审计歧义
# -DCMAKE_BUILD_TYPE=Release  使用 Release 优化
# --target llama-server llama-cli llama-gguf-split 只构建本周需要的二进制
cmake -B build \
  -DGGML_METAL=ON \
  -DCMAKE_BUILD_TYPE=Release

cmake --build build \
  --config Release \
  --target llama-server llama-cli llama-gguf-split \
  -j "$(sysctl -n hw.ncpu)"

echo "Build done:"
ls -lh build/bin/llama-server build/bin/llama-cli build/bin/llama-gguf-split
```

运行：

```bash
chmod +x scripts/build_llamacpp.sh
./scripts/build_llamacpp.sh
```

编译完成后二进制文件：

```
-rwxr-xr-x@ 1 chenxi  staff    33K  6月  6 13:49 build/bin/llama-cli
-rwxr-xr-x@ 1 chenxi  staff    58K  6月  6 13:49 build/bin/llama-gguf-split
-rwxr-xr-x@ 1 chenxi  staff    49K  6月  6 13:49 build/bin/llama-server
```

验证：

```bash
./third_party/llama.cpp/build/bin/llama-server --help | head -n 80
```

启动日志确认 M5 Metal 后端：

```
I device_info:
  - MTL0    : Apple M5 (25559 MiB, 25558 MiB free)
  - BLAS    : Accelerate (0 MiB, 0 MiB free)
  - CPU     : Apple M5 (32768 MiB, 32768 MiB free)
I system_info: n_threads = 4 / 10 | MTL : EMBED_LIBRARY = 1 | CPU : NEON = 1 | ARM_FMA = 1 | FP16_VA = 1 | MATMUL_INT8 = 1 | DOTPROD = 1 | SME = 1 | ACCELERATE = 1 | REPACK = 1 |
```

### Infra 视角深度解析

Metal 不是"显存加速"，而是 Apple Silicon 上的 GPU compute backend。M 系列机器是统一内存，CPU/GPU 共享内存池，不需要像 CUDA 那样显式在 Host RAM 和 VRAM 间搬运，但这不等于无限显存。模型权重、KV Cache、batch buffer、系统后台、浏览器都会竞争同一块 32GB unified memory。你的 serving 参数不是越大越好，尤其是 `-c` 和 `--parallel`。

---

# 3. Day 2：模型下载与量化选择

## 3.1 模型推荐

优先顺序：

| 模型                                  | 用途               | 推荐量化                     | 原因                                                     |
| ------------------------------------- | ------------------ | ---------------------------- | -------------------------------------------------------- |
| `Qwen/Qwen2.5-7B-Instruct-GGUF`       | 中文通用、工程问答 | `Q4_K_M` 起步，`Q5_K_M` 对照 | 中文能力强，官方 GGUF 仓库直接支持 llama.cpp             |
| `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` | 代码、工程解释     | `Q4_K_M` / `Q5_K_M`          | 更适合后续 SWE-agent / 代码问答                          |
| `Meta-Llama-3.1-8B-Instruct-GGUF`     | 英文通用对照       | `Q4_K_M`                     | 适合作为英语 benchmark 对照，不作为你的中文主线 baseline |

## 3.2 量化对比：32GB M5 的建议基线

Qwen2.5-7B-Instruct 的配置显示 hidden size 为 3584、28 层、28 个 attention heads、4 个 KV heads、最大位置 32768。这意味着它的 KV Cache 因 GQA 比全量 MHA 更省，但长上下文和并发 slot 仍然会线性吃内存。

| 量化        | 模型文件体积参考                             | 8k ctx / parallel=2 预期常驻内存 | 建议                                     |
| ----------- | -------------------------------------------- | -------------------------------- | ---------------------------------------- |
| `Q4_K_M`    | 约 4.7GB 级别，具体以仓库文件为准            | 约 8–12GB                        | 默认 baseline，适合压测和前端联调        |
| `Q5_K_M`    | Qwen2.5-7B-Instruct `Q5_K_M` 文件约 5.44GB   | 约 10–14GB                       | 质量更稳，适合作为主观质量对照           |
| `FP16/BF16` | 7B 约 14–16GB 权重量级，另加 KV/cache/buffer | 可能 20GB+                       | 只做短上下文质量参考，不建议常驻 serving |

## 3.3 下载模型（实际操作）

> **重要**：`huggingface-cli` 已被废弃，必须使用 `hf` CLI。`hf` 在安装 `huggingface_hub` 后自带。

```bash
# 安装/升级 huggingface_hub
conda activate cxllm
pip install -U huggingface_hub
```

Qwen 官方 GGUF 仓库的大文件被拆成多个 segment（例如 `q4_k_m` 被拆为 `00001-of-00002` 和 `00002-of-00002`），不能像普通文件一样一个命令下完。实际下载流程如下：

### 第 1 步：分片下载 Q4_K_M（两个文件）

```bash
# 下载第 1 个分片（约 3.99GB）
hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf \
  --local-dir models

# 下载第 2 个分片（约 690MB）
hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf \
  --local-dir models
```

> **提示**：如果未设置 `HF_TOKEN`，会看到警告 `You are sending unauthenticated requests to the HF Hub.`，下载仍可继续但限速。建议先 `hf auth login`。

### 第 2 步：用 llama-gguf-split 合并分片

```bash
./third_party/llama.cpp/build/bin/llama-gguf-split \
  --merge \
  models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf \
  models/qwen2.5-7b-instruct-q4_k_m.gguf
```

合并输出：

```
gguf_merge: models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf -> models/qwen2.5-7b-instruct-q4_k_m.gguf
gguf_merge: reading metadata models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf done
gguf_merge: reading metadata models/qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf done
gguf_merge: writing tensors ... done
gguf_merge: models/qwen2.5-7b-instruct-q4_k_m.gguf merged from 2 split with 339 tensors.
```

### 常见错误：下载单文件不成功

```bash
# ❌ 这样会报错，因为仓库里没有单文件，只有分片
hf download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_k_m.gguf --local-dir models
# Error: File not found in repository.
```

合并后的文件确认：

```bash
find models -name "*.gguf" -maxdepth 3 -type f -print -exec ls -lh {} \;
```

### Infra 视角深度解析

量化等级影响的是**权重内存**和部分算子吞吐，但不是唯一内存来源。真正做 serving 时，总内存大致是：

```
总内存 ≈ 模型权重
      + KV Cache(context × parallel × layers × kv_dim × dtype)
      + prompt/decode batch buffer
      + llama.cpp runtime buffer
      + FastAPI / Python / 前端 / 系统后台
```

所以 32GB 机器上最常见的坑是：你看到 Q4 模型只有 5GB，于是把 `-c 32768 --parallel 4` 开满，结果不是权重 OOM，而是 KV Cache 和 batch buffer 把统一内存打爆。

---

# 4. Day 3：生产级 llama-server 启动参数

## 4.1 端口冲突与解决

**实际踩坑**：8080 端口已被占用。llama-server 启动时报错：

```
E srv         start: couldn't bind HTTP server socket, hostname: 0.0.0.0, port: 8080
```

**解决**：改用 8081 端口。后续所有配置（.env、Gateway、scripts）统一使用 8081。

## 4.2 Q4 baseline 启动脚本

`scripts/serve_q4.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LLAMA_SERVER="${ROOT_DIR}/third_party/llama.cpp/build/bin/llama-server"
MODEL="${ROOT_DIR}/models/qwen2.5-7b-instruct-q4_k_m.gguf"
SLOT_CACHE_DIR="${ROOT_DIR}/reports/slot_cache"

mkdir -p "${SLOT_CACHE_DIR}"

"${LLAMA_SERVER}" \
  -m "${MODEL}" \
  --alias local-qwen2.5-7b-q4 \
  --host 127.0.0.1 \
  --port 8081 \
  -c 8192 \
  -b 512 \
  -ub 128 \
  -ngl 99 \
  --parallel 2 \
  --cache-prompt \
  --slot-save-path "${SLOT_CACHE_DIR}" \
  --metrics \
  --slots \
  --log-timestamps
```

运行：

```bash
chmod +x scripts/serve_q4.sh
./scripts/serve_q4.sh
```

启动成功的关键日志：

```
I srv  llama_server: server is listening on http://127.0.0.1:8081
I slot   load_model: id  0 | task -1 | new slot, n_ctx = 4096
I slot   load_model: id  1 | task -1 | new slot, n_ctx = 4096
I srv    load_model: prompt cache is enabled, size limit: 8192 MiB
I init: chat template, example_format: '<|im_start|>system ...
I srv  llama_server: model loaded
```

## 4.3 参数解释

| 参数               | 建议值                | 作用                                       | 对 M5 统一内存的影响              |
| ------------------ | --------------------- | ------------------------------------------ | --------------------------------- |
| `-m`               | 模型路径              | 指定 GGUF 文件                             | 决定权重常驻内存                  |
| `--alias`          | `local-qwen2.5-7b-q4` | 给 `/v1/models` 和请求 model 使用的稳定 ID | 不影响内存，但影响网关路由        |
| `--host`           | `127.0.0.1`           | 本机开发只监听 localhost                   | 不影响内存；更安全                |
| `--port`           | `8081`                | llama-server 端口                          | 不影响内存                        |
| `-c`               | `8192`                | context window                             | KV Cache 近似随它线性增长         |
| `-b`               | `512`                 | prompt processing batch size               | 影响 prefill 吞吐和临时 buffer    |
| `-ub`              | `128`                 | micro batch                                | 降低峰值 buffer，可能牺牲一点吞吐 |
| `-ngl`             | `99`                  | 尽量 offload layers 到 GPU/Metal           | 提升推理速度；Metal 共享统一内存  |
| `--parallel`       | `2`                   | server slots 数                            | KV Cache 近似随 slot 数线性增长   |
| `--cache-prompt`   | 开                    | 复用相同 prompt 前缀                       | 多轮/固定系统提示词场景降低 TTFT  |
| `--slot-save-path` | cache 目录            | 允许保存/恢复 slot prompt cache            | 会写磁盘；用于实验 prompt cache   |
| `--metrics`        | 开                    | 暴露 Prometheus metrics                    | 轻微开销，可忽略                  |
| `--slots`          | 开                    | 暴露 slots 监控                            | 用于观察并发 slot 状态            |
| `--log-timestamps` | 开                    | 日志带时间戳                               | 便于压测归因                      |

`--parallel` 在 llama.cpp server 中表示 server slots 数；`--metrics` 开启 Prometheus-compatible `/metrics`；`--cache-prompt` 控制 prompt caching；`--slot-save-path` 用于保存 slot KV cache。

## 4.4 smoke test

`scripts/smoke_openai.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

curl -s http://127.0.0.1:8081/v1/chat/completions \
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
  }' | python -m json.tool --no-ensure-ascii
```

> **提示**：`python -m json.tool` 默认将中文转义为 `\uXXXX`。加上 `--no-ensure-ascii` 才能正常显示中文。推荐日常使用 `jq` 替代：`curl ... | jq .`

### Infra 视角深度解析

`-c` 和 `--parallel` 是本地 serving 的两个危险旋钮。`-c 8192 --parallel 2` 的含义不是"总共 8192 token"，而是 server 能维护多个 slot，每个 slot 都可能占用上下文相关的 KV 空间。你应当建立矩阵：

```
Q4_K_M × context={4096,8192,16384} × parallel={1,2,4}
Q5_K_M × context={4096,8192,16384} × parallel={1,2}
```

企业面试时，不要只说"我会调参数"，要说"我用延迟、TTFT、吞吐、内存峰值建立过容量模型"。

---

# 5. Day 4：FastAPI AI Gateway

## 5.1 `.env.example` 与 `.env`（端口 8081）

`.env.example`：

```
APP_NAME=llamacpp-serving-lab
GATEWAY_HOST=127.0.0.1
GATEWAY_PORT=8000

LLAMACPP_BASE_URL=http://127.0.0.1:8081
LLAMACPP_API_KEY=
DEFAULT_MODEL=local-qwen2.5-7b-q4

UPSTREAM_CONNECT_TIMEOUT=5
UPSTREAM_READ_TIMEOUT=300
MAX_REQUEST_TOKENS=8192
MAX_OUTPUT_TOKENS=2048
```

实际使用时，从模板复制：

```bash
cp .env.example .env
```

## 5.2 `gateway/config.py`

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    统一配置入口。
    企业项目不要把上游地址、超时、默认模型写死在 route 里，
    否则后续切换 MLX/Ollama/vLLM/云 API 会非常痛苦。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "llamacpp-serving-lab"

    llamacpp_base_url: str = "http://127.0.0.1:8081"
    llamacpp_api_key: str | None = None
    default_model: str = "local-qwen2.5-7b-q4"

    upstream_connect_timeout: float = 5.0
    upstream_read_timeout: float = 300.0

    max_request_tokens: int = 8192
    max_output_tokens: int = Field(default=2048, ge=1, le=8192)


settings = Settings()
```

## 5.3 `gateway/schemas.py`

```python
from typing import Literal, Any
from pydantic import BaseModel, Field, model_validator


Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatCompletionRequest(BaseModel):
    """
    OpenAI Chat Completions 的最小兼容子集。
    不追求一次性覆盖全部字段，先保证最常用 serving 链路稳定。
    """

    model: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)

    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    stream: bool = False

    # 允许透传 llama.cpp 支持但本 schema 未显式建模的字段。
    extra_body: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_messages(self):
        if not any(m.role == "user" for m in self.messages):
            raise ValueError("messages 至少需要包含一条 user 消息")
        return self

    def to_upstream_payload(self, default_model: str) -> dict[str, Any]:
        payload = {
            "model": self.model or default_model,
            "messages": [m.model_dump() for m in self.messages],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
        }
        payload.update(self.extra_body)
        return payload


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    upstream: str
    detail: str | None = None
```

## 5.4 `gateway/llamacpp_client.py`

```python
import json
import time
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException

from gateway.config import settings


class LlamaCppClient:
    """
    llama-server 的异步 HTTP 客户端。
    设计原则：
    1. Gateway 不直接做推理，只代理上游 OpenAI-compatible API。
    2. 所有超时、异常、状态码在这里统一收敛。
    3. stream 和 non-stream 分开处理，避免把 SSE 全量读入内存。
    """

    def __init__(self) -> None:
        timeout = httpx.Timeout(
            connect=settings.upstream_connect_timeout,
            read=settings.upstream_read_timeout,
            write=30.0,
            pool=30.0,
        )
        headers = {}
        if settings.llamacpp_api_key:
            headers["Authorization"] = f"Bearer {settings.llamacpp_api_key}"

        self._client = httpx.AsyncClient(
            base_url=settings.llamacpp_base_url,
            timeout=timeout,
            headers=headers,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def health(self) -> tuple[bool, str]:
        try:
            r = await self._client.get("/v1/models")
            if r.status_code == 200:
                return True, "llama-server ready"
            return False, f"llama-server returned {r.status_code}"
        except httpx.HTTPError as e:
            return False, repr(e)

    async def chat_completion(self, payload: dict) -> dict:
        """
        非流式调用。适合压测 correctness、JSON 输出、短请求。
        """
        t0 = time.perf_counter()
        try:
            r = await self._client.post("/v1/chat/completions", json=payload)
            r.raise_for_status()
            data = r.json()
            data.setdefault("_gateway", {})
            data["_gateway"]["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            return data
        except httpx.TimeoutException as e:
            raise HTTPException(status_code=504, detail=f"upstream timeout: {e!r}") from e
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    "message": "upstream llama-server error",
                    "body": e.response.text[:2000],
                },
            ) from e
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"upstream http error: {e!r}") from e
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"invalid upstream json: {e!r}") from e

    async def stream_chat_completion(self, payload: dict) -> AsyncIterator[bytes]:
        """
        流式调用。直接把上游 SSE chunk 透传给前端。
        关键点：不能 await r.aread()，否则会把流式响应变成阻塞响应。
        """
        try:
            async with self._client.stream(
                "POST",
                "/v1/chat/completions",
                json=payload,
            ) as r:
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    if chunk:
                        yield chunk
        except httpx.TimeoutException as e:
            yield f"event: error\ndata: {json.dumps({'error': 'upstream timeout', 'detail': repr(e)}, ensure_ascii=False)}\n\n".encode("utf-8")
        except httpx.HTTPStatusError as e:
            body = e.response.text[:2000]
            yield f"event: error\ndata: {json.dumps({'error': 'upstream status error', 'body': body}, ensure_ascii=False)}\n\n".encode("utf-8")
        except httpx.HTTPError as e:
            yield f"event: error\ndata: {json.dumps({'error': 'upstream http error', 'detail': repr(e)}, ensure_ascii=False)}\n\n".encode("utf-8")
```

## 5.5 `gateway/routes_chat.py`

```python
from fastapi import APIRouter, Request
from fastapi.responses import ORJSONResponse, StreamingResponse

from gateway.config import settings
from gateway.schemas import ChatCompletionRequest

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    """
    对外暴露 OpenAI-compatible 路由。
    前端、LangChain、OpenAI SDK 都可以把这里当成本地 base_url。
    """
    client = request.app.state.llamacpp
    payload = req.to_upstream_payload(default_model=settings.default_model)

    if req.stream:
        return StreamingResponse(
            client.stream_chat_completion(payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    data = await client.chat_completion(payload)
    return ORJSONResponse(data)
```

## 5.6 `gateway/routes_health.py`

```python
from fastapi import APIRouter, Request
from gateway.schemas import HealthResponse
from gateway.config import settings

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz(request: Request):
    ok, detail = await request.app.state.llamacpp.health()
    return HealthResponse(
        status="ok" if ok else "degraded",
        upstream=settings.llamacpp_base_url,
        detail=detail,
    )


@router.get("/readyz", response_model=HealthResponse)
async def readyz(request: Request):
    ok, detail = await request.app.state.llamacpp.health()
    return HealthResponse(
        status="ok" if ok else "degraded",
        upstream=settings.llamacpp_base_url,
        detail=detail,
    )
```

## 5.7 `gateway/app.py`

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gateway.config import settings
from gateway.llamacpp_client import LlamaCppClient
from gateway.routes_chat import router as chat_router
from gateway.routes_health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期管理：
    启动时创建上游连接池，关闭时释放连接。
    避免每个请求都新建 AsyncClient，降低连接开销。
    """
    app.state.llamacpp = LlamaCppClient()
    yield
    await app.state.llamacpp.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# 本地开发允许前端访问；生产环境应替换为明确域名。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
```

## 5.8 启动与测试 Gateway

**终端 1：启动 llama-server**

```bash
conda activate cxllm
./scripts/serve_q4.sh
```

**终端 2：启动 Gateway**

```bash
conda activate cxllm
uvicorn gateway.app:app --host 127.0.0.1 --port 8000 --reload
```

**测试健康检查：**

```bash
curl -s http://127.0.0.1:8000/healthz | python -m json.tool --no-ensure-ascii
```

正常输出：

```json
{
    "status": "ok",
    "upstream": "http://127.0.0.1:8081",
    "detail": "llama-server ready"
}
```

**测试聊天接口（中文正常显示）：**

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "用三句话解释 llama.cpp 的 serving 价值。"}
    ],
    "max_tokens": 256,
    "stream": false
  }' | python -m json.tool --no-ensure-ascii
```

实际返回（Qwen2.5-7B-Q4_K_M）：

```json
{
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "llama.cpp 是一个开源的库，用于高效地部署和运行大语言模型。它的 serving 价值在于能够快速部署模型到生产环境，支持低延迟的实时推理。此外，它还提供了高度的灵活性和可定制性，使得用户可以根据自己的需求调整模型的配置和参数。"
            }
        }
    ],
    "created": 1780727890,
    "model": "local-qwen2.5-7b-q4",
    "object": "chat.completion",
    "usage": {
        "completion_tokens": 65,
        "prompt_tokens": 40,
        "total_tokens": 105,
        "prompt_tokens_details": {
            "cached_tokens": 39
        }
    },
    "_gateway": {
        "latency_ms": 2499.12
    }
}
```

### 实际踩坑记录

**坑 1：llama-server 没启动导致 502**

如果 Gateway 返回如下，说明上游没有运行：

```json
{
    "detail": {
        "message": "upstream llama-server error",
        "body": ""
    }
}
```

此时 `/healthz` 也会显示 `"status": "degraded"`。解决：先启动 `./scripts/serve_q4.sh`。

**坑 2：`.env` 未更新导致连错端口**

如果忘记 `cp .env.example .env`，Gateway 会使用代码中的默认值（可能是 8080 而不是 8081）。启动 Gateway 前务必确认 `.env` 存在且 `LLAMACPP_BASE_URL=http://127.0.0.1:8081`。

### Infra 视角深度解析

为什么要加 Gateway？因为企业里很少让业务系统直接打模型进程。Gateway 负责统一：鉴权、限流、路由、日志、trace、fallback、模型别名、参数兜底、错误映射。你现在虽然只有一个 llama.cpp provider，但接口边界应该从 Day 1 就按多 provider 设计：未来 Week 7 接 LangGraph、Week 9 接 SWE-agent 时，这个网关可以直接复用。

---

# 6. Day 5：并发压测与 TTFT / Tokens/s

## 6.1 压测脚本

`scripts/bench_concurrency.py`（代码同上，此处省略完整源码，见项目中的实际文件）。

关键逻辑：
- 通过 SSE 流式响应测 TTFT（Time to First Token）
- TTFT = request 发出后，到收到第一个有效 data chunk 的时间
- tokens/s 用字符数 ÷ 2 粗估（中文场景）
- 企业报告中应优先使用 llama-server `/metrics` 的 predicted_tokens_seconds

## 6.2 实际压测结果

### Concurrency = 1（5 requests，串行）

```bash
python scripts/bench_concurrency.py --concurrency 1 --requests 5 --max-tokens 256
```

```
SUMMARY
{
  "requests": 5,
  "concurrency": 1,
  "success": 5,
  "error": 0,
  "ttft_ms_p50": 236.82,
  "ttft_ms_p95": 250.91,
  "total_ms_p50": 11024.52,
  "total_ms_p95": 13953.01,
  "approx_tps_avg": 22.95
}
```

### Concurrency = 2（10 requests）

```bash
python scripts/bench_concurrency.py --concurrency 2 --requests 10 --max-tokens 256
```

```
SUMMARY
{
  "requests": 10,
  "concurrency": 2,
  "success": 10,
  "error": 0,
  "ttft_ms_p50": 476.19,
  "ttft_ms_p95": 765.29,
  "total_ms_p50": 35614.59,
  "total_ms_p95": 36489.18,
  "approx_tps_avg": 7.87
}
```

### 关键发现

| 指标        | concurrency=1 | concurrency=2 | 变化         |
| ----------- | ------------- | ------------- | ------------ |
| TTFT P50    | 236.82 ms     | 476.19 ms     | ↑ 约 2×      |
| TTFT P95    | 250.91 ms     | 765.29 ms     | ↑ 约 3×      |
| Total P50   | 11024.52 ms   | 35614.59 ms   | ↑ 约 3.2×    |
| Avg TPS     | 22.95         | 7.87          | ↓ 约 65%     |

并发=2 时两个请求同时抢占两个 slot，prefill 排队等待导致 TTFT 翻倍，每个 slot 的 decode 吞吐也下降。与 `--parallel 2` 参数吻合：2 个 slot 刚好被 2 个并发请求占满。

## 6.3 抓取 `/metrics`

```bash
python scripts/scrape_metrics.py
```

保存到 `observability/metrics_snapshots/metrics_YYYYMMDD_HHMMSS.txt`。

```bash
grep -E "prompt_tokens|predicted_tokens|requests_processing|requests_deferred|n_tokens_max" observability/metrics_snapshots/*.txt | tail -n 30
```

### Infra 视角深度解析

TTFT 主要看 **prefill 阶段**：prompt 越长，模型越要先处理完整输入，首字越慢。Tokens/s 主要看 **decode 阶段**：每次生成新 token 都要基于已有 KV 继续算。用户感知上，TTFT 决定"有没有卡住"，Tokens/s 决定"输出是否丝滑"。压测时必须拆开看，否则你会误判瓶颈。

---

# 7. Day 6：Prompt Cache / Slot 实验

llama.cpp server 支持 slot prompt cache 的 save / restore / erase；保存时使用 `/slots/{id_slot}?action=save`，恢复时使用 `/slots/{id_slot}?action=restore`，文件路径由 `--slot-save-path` 控制。

`scripts/test_prompt_cache.sh`：

```bash
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
```

运行：

```bash
chmod +x scripts/test_prompt_cache.sh
./scripts/test_prompt_cache.sh
```

实际输出：

```
warmup done
{
    "id_slot": 0,
    "filename": "gateway_system_prompt.bin",
    "n_saved": 326,
    "n_written": 18700064,
    "timings": {
        "save_ms": 5.494
    }
}
{
    "id_slot": 0,
    "filename": "gateway_system_prompt.bin",
    "n_restored": 326,
    "n_read": 18700064,
    "timings": {
        "restore_ms": 2.295
    }
}
cache reuse request done
```

- 保存了 326 个 token 的 KV 状态，写入 18.7MB，仅耗时 5.5ms
- 恢复时读取 18.7MB，仅耗时 2.3ms
- 恢复后再请求相同系统提示词，prompt cache 命中，cached_tokens > 0，TTFT 显著降低

### Infra 视角深度解析

KV Cache 是一次推理过程中 attention 的 K/V 状态缓存；Prompt Cache 是把一段已经 prefill 过的 prompt 前缀状态复用起来。典型收益场景：长 system prompt、RAG 固定文档前缀、Agent 工具说明、代码仓库上下文。它优化的是重复长前缀的 TTFT，不会让任意新 prompt 免费变快。

---

# 8. Day 7：前端联调与最终报告

## 8.1 前端目录创建

```bash
mkdir -p frontend/vue3-sse-demo/src/api
mkdir -p frontend/vue3-sse-demo/src/components
touch frontend/vue3-sse-demo/src/api/llm.ts
```

## 8.2 Vue3 + TS SSE 核心逻辑

`frontend/vue3-sse-demo/src/api/llm.ts`：

```typescript
export type ChatMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

export type StreamOptions = {
  baseUrl?: string;
  model?: string;
  messages: ChatMessage[];
  maxTokens?: number;
  temperature?: number;
  onDelta: (text: string) => void;
  onDone?: () => void;
  onError?: (err: Error) => void;
};

export async function streamChatCompletion(opts: StreamOptions) {
  const baseUrl = opts.baseUrl ?? "http://127.0.0.1:8000";
  const controller = new AbortController();

  try {
    const resp = await fetch(`${baseUrl}/v1/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      signal: controller.signal,
      body: JSON.stringify({
        model: opts.model ?? "local-qwen2.5-7b-q4",
        messages: opts.messages,
        max_tokens: opts.maxTokens ?? 512,
        temperature: opts.temperature ?? 0.2,
        stream: true,
      }),
    });

    if (!resp.ok || !resp.body) {
      throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line.startsWith("data: ")) continue;

        const data = line.slice("data: ".length).trim();
        if (data === "[DONE]") {
          opts.onDone?.();
          return { abort: () => controller.abort() };
        }

        try {
          const obj = JSON.parse(data);
          const delta = obj?.choices?.[0]?.delta?.content;
          if (delta) opts.onDelta(delta);
        } catch {
          // 忽略非 JSON SSE 行，避免 UI 因上游一行异常直接崩掉。
        }
      }
    }

    opts.onDone?.();
    return { abort: () => controller.abort() };
  } catch (e) {
    const err = e instanceof Error ? e : new Error(String(e));
    opts.onError?.(err);
    return { abort: () => controller.abort() };
  }
}
```

`ChatBox.vue` 核心片段：

```vue
<script setup lang="ts">
import { ref } from "vue";
import { streamChatCompletion } from "../api/llm";

const input = ref("");
const output = ref("");
const loading = ref(false);
const error = ref("");

async function send() {
  if (!input.value.trim() || loading.value) return;

  output.value = "";
  error.value = "";
  loading.value = true;

  await streamChatCompletion({
    messages: [
      { role: "system", content: "你是严谨的 AI Infra 工程师。" },
      { role: "user", content: input.value },
    ],
    onDelta: (text) => {
      output.value += text;
    },
    onDone: () => {
      loading.value = false;
    },
    onError: (err) => {
      error.value = err.message;
      loading.value = false;
    },
  });
}
</script>

<template>
  <main class="chat">
    <textarea v-model="input" placeholder="输入你的问题" />
    <button :disabled="loading" @click="send">
      {{ loading ? "生成中..." : "发送" }}
    </button>

    <p v-if="error" class="error">{{ error }}</p>
    <pre class="output">{{ output }}</pre>
  </main>
</template>
```

## 8.3 最终报告模板

`reports/week2_final_report.md`：

```
# Week 2 Final Report：llama.cpp GGUF Serving Lab

## 1. 环境
- 机器：MacBook Air M5，32GB unified memory
- OS：macOS 26
- Conda 环境：cxllm (Python 3.11)
- llama.cpp commit：最新 main 分支（2026-06-06 编译）
- 模型：Qwen/Qwen2.5-7B-Instruct-GGUF
- 量化：Q4_K_M

## 2. 启动参数
| model | quant | ctx | batch | ubatch | parallel | ngl | cache_prompt | port |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| qwen2.5-7b-instruct | Q4_K_M | 8192 | 512 | 128 | 2 | 99 | on | 8081 |

## 3. 性能矩阵
| quant | ctx | parallel | concurrency | TTFT P50 | TTFT P95 | total P95 | tokens/s | notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Q4_K_M | 8192 | 2 | 1 | 236.82ms | 250.91ms | 13953ms | 22.95 | prompt cache warm |
| Q4_K_M | 8192 | 2 | 2 | 476.19ms | 765.29ms | 36489ms | 7.87 | 2 slots 占满 |

## 4. 内存观察
- Activity Monitor 峰值：
- llama.cpp 日志：
- /metrics n_tokens_max：
- 是否出现 requests_deferred：

## 5. Prompt Cache 实验
- 固定 system prompt 长度：326 tokens
- 写入文件大小：18.7MB
- save 耗时：5.5ms
- restore 耗时：2.3ms
- 恢复后 TTFT：cache 命中，prompt 处理从 40 tokens 降至 1 token

## 6. 前端联调
- Gateway URL：http://127.0.0.1:8000
- 是否支持 stream：是
- 异常处理：连接拒绝/超时/JSON 解析错误均有兜底

## 7. 结论
- 推荐生产 baseline：Q4_K_M / ctx=8192 / parallel=2 / port=8081
- 不推荐参数组合：parallel=4 在 32GB M5 上需谨慎，需压测验证
- 下一步优化：Q5_K_M 质量对照、长上下文阶梯测试、MCP tool calling
```

### Infra 视角深度解析

最终报告比代码更重要。企业不缺"我跑起来了"，缺的是"我知道为什么快、为什么慢、什么时候会炸、怎么扩容、怎么观测"。你要把 Week 2 做成一个容量评估样本：当模型从 Q4 切到 Q5，当 context 从 4k 增到 16k，当 parallel 从 1 到 4，TTFT、吞吐、deferred requests、内存峰值如何变化。

---

# 9. Makefile

```makefile
.PHONY: build serve-q4 gateway smoke bench metrics

build:
	bash scripts/build_llamacpp.sh

serve-q4:
	bash scripts/serve_q4.sh

gateway:
	uvicorn gateway.app:app --host 127.0.0.1 --port 8000 --reload

smoke:
	bash scripts/smoke_openai.sh

bench:
	python scripts/bench_concurrency.py --concurrency 2 --requests 10 --max-tokens 256

metrics:
	python scripts/scrape_metrics.py
```

使用：

```bash
make build
make serve-q4    # 终端 1
make gateway     # 终端 2
make smoke
make bench
make metrics
```

---

# 10. 你必须避开的坑

**坑 1：8080 端口被占用。**
macOS 上 8080 常被其他服务（如 AirPlay Receiver）占用。llama-server 绑定 8080 会直接报错退出：
```
E srv         start: couldn't bind HTTP server socket, hostname: 0.0.0.0, port: 8080
```
**解决**：改用 8081，并在 `.env`、`serve_q4.sh`、Gateway 配置中统一。

**坑 2：`huggingface-cli` 已废弃。**
`huggingface-cli` 不再可用，必须使用 `hf` CLI（安装 `huggingface_hub` 后自带）。常用命令：
```bash
hf auth login                    # 登录
hf download REPO FILE --local-dir DIR   # 下载
```

**坑 3：GGUF 大文件是分片的，不能直接下载单文件。**
`hf download ... qwen2.5-7b-instruct-q4_k_m.gguf` 会报 `File not found`。实际文件是 `-00001-of-00002.gguf` 和 `-00002-of-00002.gguf` 两个分片，需要分别下载后用 `llama-gguf-split --merge` 合并。

**坑 4：把 `--parallel` 当成越大越好。**
在 32GB 统一内存上，`--parallel 4` 可能让吞吐变高，也可能因为 KV Cache、调度排队和内存压力让 P95 变差。必须实测。

**坑 5：只看 Tokens/s，不看 TTFT。**
用户体感首先被 TTFT 支配。RAG、Agent、长 system prompt 场景中，prefill 往往比 decode 更致命。

**坑 6：模型文件不记录来源。**
GGUF 社区量化很多，同名模型不同人、不同 imatrix、不同 tokenizer 元数据都可能有差异。企业报告必须记录 repo、filename、size、checksum。

**坑 7：让前端直接打 llama-server。**
开发 demo 可以，工程作品不行。前端应该打 Gateway，由 Gateway 处理模型别名、参数兜底、异常映射和未来多模型路由。

**坑 8：Gateway 启动前没检查上游。**
Gateway 返回 502 + `"body": ""`，本质是 llama-server 没跑。先用 `curl http://127.0.0.1:8081/v1/models` 确认上游 alive，再测 Gateway。

**坑 9：`python -m json.tool` 中文变乱码。**
默认 `json.tool` 会转义非 ASCII 字符，中文变成 `\uXXXX`。加 `--no-ensure-ascii` 解决，推荐日常使用 `jq`。

**坑 10：忘记 `cp .env.example .env`。**
`.env` 不存在时 Gateway 会用代码中的默认值，可能连错端口。启动 Gateway 前务必确认 `.env` 存在。

---

# 11. 高频资深工程师面试题

## Q1：GGUF 和 safetensors 的本质区别是什么？

答题思路：

```
safetensors 更偏通用深度学习权重存储格式，常用于 Transformers / Diffusers 生态。
GGUF 更贴近 llama.cpp 推理生态，不只是权重文件，通常还包含 tokenizer、chat template、量化元信息等推理所需元数据。
所以 GGUF 更适合本地单文件分发和 llama.cpp serving，safetensors 更适合训练/微调/通用框架加载。
```

加分点：
说明 tokenizer/chat template mismatch 会导致模型输出异常；GGUF 的价值不是"文件后缀不同"，而是降低本地推理部署复杂度。

## Q2：为什么长上下文会让本地 serving 变慢？

答题思路：

```
长上下文首先增加 prefill 计算量，所以 TTFT 上升。
其次 KV Cache 随 context length、layers、KV heads、head dim、parallel slots、KV dtype 近似线性增长。
当 context 和 parallel 同时增大时，统一内存压力上升，batch buffer 和调度开销也会上升，P95 latency 可能恶化。
```

可以写出公式：

```
KV Cache bytes ≈ layers × ctx_tokens × parallel_slots × 2(K,V) × kv_heads × head_dim × bytes_per_element
```

## Q3：Prompt Cache 和 KV Cache 是一回事吗？

答题思路：

```
不是。
KV Cache 是单次推理过程中保存 attention key/value，避免每生成一个 token 都重复计算全部历史。
Prompt Cache 是把某段已 prefill 的 prompt 前缀状态保存或复用，主要优化重复长前缀场景，比如固定 system prompt、RAG 文档前缀、Agent 工具说明。
KV Cache 是生成机制内部必需缓存；Prompt Cache 是 serving 层面的复用策略。
```

加分点：
说明 prompt cache 主要降低重复前缀的 TTFT，而不是提升所有请求的 decode tokens/s。

---

# 12. 本周验收标准

到 Week 2 结束，你至少要交付：

```
1. ✅ llama.cpp Metal Release 编译成功
2. ✅ Qwen2.5-7B-Instruct Q4_K_M GGUF 可启动（下载分片→合并→serve）
3. ✅ llama-server 支持 /v1/chat/completions stream=false / stream=true
4. ✅ FastAPI Gateway 可代理 OpenAI-compatible 请求（端口 8081→8000）
5. ✅ Vue3 前端 SSE 流式接收逻辑完成（llm.ts + ChatBox.vue）
6. ✅ bench_concurrency.py 输出 TTFT P50/P95、total latency、粗略 tokens/s
7. ✅ /metrics 可抓取 prompt/generation throughput
8. ✅ prompt cache save / restore 跑通（326 tokens, 18.7MB, save 5.5ms, restore 2.3ms）
9. ⬜ reports/week2_final_report.md 完成性能矩阵
10. ⬜ docs/interview_notes.md 写五个核心问题的答题思路
```

建议你的默认 baseline：

```
Qwen2.5-7B-Instruct-Q4_K_M
-c 8192
-b 512
-ub 128
-ngl 99
--parallel 2
--cache-prompt
--metrics
--port 8081
```

这个组合足够稳，能覆盖本地 AI Gateway 的核心工程问题。下一步再扩展到 `Q5_K_M`、`-c 16384`、`--parallel 4`，用实测数据决定是否值得。
