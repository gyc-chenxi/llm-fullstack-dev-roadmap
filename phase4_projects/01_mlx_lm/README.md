# 🏠 晨熙的本地大模型实验台

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vue.js-3.5-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white" alt="Vue 3" />
  <img src="https://img.shields.io/badge/TypeScript-6.0-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/MLX-0.14-000000?style=flat-square&logo=apple&logoColor=white" alt="MLX" />
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/TailwindCSS-4.0-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="TailwindCSS v4" />
  <img src="https://img.shields.io/badge/LoRA-rank_8-8B5CF6?style=flat-square" alt="LoRA" />
  <img src="https://img.shields.io/badge/platform-macOS_Apple_Silicon-lightgrey?style=flat-square" alt="macOS" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License MIT" />
</p>

<p align="center">
  <strong>基于 Apple MLX 的纯本地大模型全栈应用 — 从 LoRA 微调到流式推理，一键启动</strong><br/>
  MLX Metal 加速 · SSE 流式响应 · SQLite 持久化 · 滑动窗口记忆 · 会话管理 · Markdown 代码高亮
</p>

---

## 📖 项目简介

**晨熙的本地大模型实验台** 是一个完全运行在 Apple Silicon Mac 上的大模型全栈应用，项目围绕 **MLX 推理框架** 与 **LoRA 微调技术** 构建——后端 FastAPI + SSE 流式协议，前端 Vue 3 + TypeScript + Pinia + TailwindCSS v4，数据层 SQLite 持久化。整个系统在断网环境下可独立运行，数据不出设备，实现了真正的本地私有化部署。

支持流式对话、会话历史管理、Markdown 代码高亮、系统提示词自定义、温度参数调节等类 ChatGPT 完整体验，并包含 11 条高质量定制训练样本及已完成 LoRA 微调的适配器权重。

**在学习路线中的位置**：Week 1 — MLX 本地模型实验（前置项目，后续衔接 Week 2 llama.cpp GGUF serving / Week 3 LangGraph Agent）

---

## 🎯 学习目标

完成本项目后，你将掌握：

| 能力域 | 具体技能 |
|--------|----------|
| **MLX 推理** | `mlx_lm.load()` 模型加载、`stream_generate()` 流式生成、`make_sampler()` 温度采样 |
| **LoRA 微调** | 参数高效微调原理、`rank=8` 适配器训练、`adapters.safetensors` 权重加载 |
| **流式响应** | SSE 协议、`EventSourceResponse`、ReadableStream 行缓冲解析、AbortController |
| **上下文管理** | tokenizer 精确 token 计数、滑动窗口截断、system 消息保留策略 |
| **数据持久化** | SQLModel ORM、SQLite、`Depends(get_db)` 依赖注入、流式结束自动落盘 |
| **前端工程** | Pinia 状态管理、Vue Router、Composition API、`defineExpose` 组件通信 |
| **UI/UX** | TailwindCSS v4 原子化样式、markdown-it 渲染、highlight.js 代码高亮、IME 输入法兼容 |
| **进程编排** | Bash trap cleanup + PID 追踪、`make start` 一键启动、轮询等待就绪 |

---

## ✨ 功能亮点

### 核心链路
- ✅ **一键启动** — `make start` 后台启动 Server（含 MLX 模型加载）+ 前台 Vite 前端，Ctrl+C 全部停止
- ✅ **SSE 流式推理** — MLX `stream_generate` token 逐字产出，前端 ReadableStream 行缓冲增量渲染
- ✅ **Metal GPU 加速** — Apple Silicon 原生 MLX 框架，4-bit 量化模型仅占 ~4.2GB 统一内存
- ✅ **LoRA 微调支持** — `rank=8` 适配器权重加载，`adapters/identity_lora/adapters.safetensors` (~16MB)

### 工程化能力
- ✅ **SQLite 持久化** — 会话自动创建 + 消息流式结束自动落盘 + 级联删除 + `COUNT(*)` 消息计数
- ✅ **会话 CRUD** — 5 个 RESTful 端点（列表/创建/详情/删除/消息历史），`GET /api/sessions`
- ✅ **滑动窗口截断** — tokenizer 精确计数，始终保留 system 消息，从最新向最旧截断
- ✅ **系统提示词管理** — Settings 面板编辑 + 三档预设（代码助手/翻译专家/通用助手）

### UI/UX
- ✅ **Markdown 渲染** — `markdown-it` + `highlight.js` GitHub Dark 主题，代码块 hover 复制按钮
- ✅ **IME 输入法兼容** — `e.isComposing` 检测，拼音选词 Enter 不误发送
- ✅ **智能自动滚动** — 距底部 <100px 时自动跟随，用户上滑查看历史时暂停
- ✅ **响应式布局** — 移动端侧边栏自动折叠，桌面端可手动切换

### 待增强
- 🟡 **自动化测试** — 当前无 pytest/vitest 覆盖（llamacpp-serving-lab 对标项目已有 23 tests）
- 🚧 **API Key 鉴权** — 当前仅 CORS 开放
- 🚧 **Docker** — macOS 上 MLX 不需要容器化（原生 Metal 加速），Docker 反而损失 GPU

---

## 🛠 技术栈

| 层 | 技术 | 版本 |
|---|---|---|
| **AI 推理** | MLX + mlx-lm | 0.14+ |
| **模型** | Qwen2.5-7B-Instruct-4bit (MLX format) | ~4.2GB |
| **微调** | LoRA (rank=8, iters=200) | adapters.safetensors ~16MB |
| **API 框架** | FastAPI + uvicorn | 0.110 / 0.27 |
| **SSE** | sse-starlette | 1.6 |
| **ORM** | SQLModel + SQLAlchemy | 0.0.14 |
| **数据库** | SQLite (chat.db) | 3 |
| **前端框架** | Vue 3 + TypeScript + Vite | 3.5 / 6.0 / 8.0 |
| **状态管理** | Pinia | 3.0 |
| **路由** | Vue Router | 4.5 |
| **样式** | TailwindCSS v4 (Vite 插件) | 4.0 |
| **渲染** | markdown-it + highlight.js | 14.1 / 11.11 |
| **Python 环境** | Conda (cxllm) | Python 3.11 |
| **进程编排** | Bash (trap cleanup + PID 追踪) | — |

---

## 🏗 系统架构

```mermaid
graph TD
    subgraph "浏览器 :5173"
        V[Vue3 SPA<br/>Pinia Store · Vue Router<br/>SSE token-by-token 渲染]
    end

    subgraph "Vite Dev Proxy"
        PX["/v1, /api → :8001"]
    end

    subgraph "FastAPI Server :8001"
        LF[lifespan: 模型加载 + 建表]
        RT[POST /v1/chat/completions<br/>SSE 流式端点]
        API[GET/POST/DELETE /api/sessions<br/>会话 CRUD 5 端点]
        ENG[LLMEngine<br/>truncate → build_prompt → stream_generate]
    end

    subgraph "MLX + LoRA"
        MLX["mlx_lm.load()<br/>Qwen2.5-7B-Instruct-4bit<br/>+ identity_lora adapter"]
    end

    subgraph "Persistence"
        DB["chat.db (SQLite)<br/>ChatSession + Message"]
    end

    V -->|fetch SSE| PX
    PX -->|HTTP proxy| LF
    LF --> RT
    LF --> API
    RT --> ENG
    ENG --> MLX
    RT -->|_persist_messages()| DB
    API --> DB
```

### 模块职责

| 模块 | 路径 | 职责 |
|------|------|------|
| **应用入口** | `server/app.py` | FastAPI lifespan 管理：启动时加载 MLX 模型 + LoRA + 建表，关闭时清理 |
| **配置中心** | `server/config.py` | 8 个环境变量驱动配置（模型路径/数据库/推理参数/端口） |
| **推理引擎** | `server/llm.py` | LLMEngine：模型加载、滑动窗口截断、prompt 构建、流式生成 |
| **SSE 端点** | `server/routes/chat.py` | `/v1/chat/completions`，流式生成 + 自动持久化 |
| **会话 API** | `server/routes/sessions.py` | 5 个 CRUD 端点（列表/创建/详情/删除/消息历史） |
| **Pinia Store** | `frontend/src/stores/chat.ts` | 唯一状态源：会话/消息/SSE/AbortController |
| **SSE 客户端** | `frontend/src/composables/useSSE.ts` | 行缓冲解析 + delta 提取 |
| **启动编排** | `scripts/start_all.sh` | 前置检查→后台 Server→轮询 /health→前台 Vite→trap 清理 |

---

## 📁 项目目录结构

```
mlx-local-lab/
├── Makefile                    # 一键启动/停止 (make start / make stop / make setup)
├── scripts/                    # 工具脚本 (5 个)
│   ├── start_all.sh            #   🚀 一键启动编排（trap + PID + 轮询等待）
│   ├── stop_all.sh             #   一键停止（PID 文件 + pkill 双保险）
│   ├── setup_check.sh          #   10 项环境就绪检查
│   ├── download_model.py       #   模型下载（国内镜像加速）
│   └── infer.py                #   单次推理测试
│
├── server/                     # FastAPI 后端
│   ├── app.py                  #   应用入口（lifespan：模型加载 + 建表）
│   ├── config.py               #   环境变量驱动配置
│   ├── llm.py                  #   LLMEngine（推理/截断/流式生成）
│   ├── models.py               #   SQLModel 表定义（ChatSession + Message）
│   ├── schemas.py              #   Pydantic 模型（含 field_serializer）
│   ├── database.py             #   SQLAlchemy 引擎 + Depends(get_db)
│   ├── requirements.txt        #   Python 依赖
│   └── routes/
│       ├── chat.py             #   POST /v1/chat/completions (SSE + 持久化)
│       └── sessions.py         #   /api/sessions CRUD (5 端点)
│
├── frontend/                   # Vue3 + TypeScript + Vite 前端
│   ├── vite.config.ts          #   Vite 配置 + /v1 & /api 代理
│   └── src/
│       ├── stores/chat.ts      #   Pinia Store（核心状态 + SSE + AbortController）
│       ├── composables/         #   useSSE (行缓冲解析) · useAutoScroll (智能滚动)
│       ├── components/          #   Sidebar · ChatArea · ChatBubble · ChatInput · SettingsPanel
│       └── utils/markdown.ts   #   markdown-it + highlight.js + 复制按钮
│
├── adapters/identity_lora/     # LoRA 微调权重 (rank=8, ~16MB)
├── datasets/                   # 微调数据集 (train.jsonl 11 条 + valid.jsonl)
├── models/                     # 模型权重（⛔ 不进 Git，~8GB）
├── chat.db                     # SQLite 数据库（运行时自动生成，⛔ 不进 Git）
└── docs/                       # 项目文档
```

---

## 🚀 快速开始

### 1. 环境要求

| 组件 | 要求 | 检查方式 |
|------|------|----------|
| 硬件 | MacBook M 系列 (M1–M5)，16GB+ 统一内存 | 关于本机 |
| macOS | 14.0+ (Sonoma) | `sw_vers` |
| Conda | Miniconda/Anaconda，环境名 `cxllm` | `which conda` |
| Node.js | 18+ | `node -v` |

### 2. 克隆项目

```bash
git clone https://github.com/<your-username>/mlx-local-lab.git
cd mlx-local-lab
```

### 3. 环境检查

```bash
make setup
```

自动检测 conda 环境、`mlx-lm`、`fastapi`、`sqlmodel`、模型目录、LoRA adapter、npm 依赖。缺失项会提示修复命令。

### 4. 安装依赖

```bash
# Python 后端
conda activate cxllm
pip install -r server/requirements.txt

# 前端
cd frontend && npm install && cd ..
```

### 5. 下载模型（仅首次，约 8GB）

```bash
make download-model
# 等价于: python scripts/download_model.py
# 使用 HuggingFace 国内镜像加速下载
```

模型来源：[mlx-community/Qwen2.5-7B-Instruct-4bit](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit)，License：Apache 2.0（模型权重）+ Qwen License。

### 6. 一键启动 🚀

```bash
make start
```

等待约 10–30 秒（MLX 模型加载），看到：

```
[INFO]  All services are running!
        Frontend:  http://127.0.0.1:5173
        API:       http://127.0.0.1:8001
        Press Ctrl+C to stop all services.
```

### 7. 打开浏览器

**http://127.0.0.1:5173** → 新建会话 → 开始聊天。

### 8. 停止服务

按 **Ctrl+C**，或从另一终端 `make stop`。

### 自测命令

```bash
# Health check
curl http://127.0.0.1:8001/health

# API 文档（自动生成）
open http://127.0.0.1:8001/docs

# 创建会话
curl -X POST http://127.0.0.1:8001/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "测试会话"}'

# 获取会话列表
curl http://127.0.0.1:8001/api/sessions | python -m json.tool

# 流式聊天测试
curl -N http://127.0.0.1:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "用 Python 写一个快速排序"}],
    "max_tokens": 256,
    "temperature": 0.7
  }'

# 单次推理测试（直接调 MLX，不走 HTTP）
python scripts/infer.py
```

---

## 📡 核心使用方式

### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查（模型路径 + adapter 路径） |
| `GET` | `/docs` | 自动生成的 Swagger API 文档 |
| `POST` | `/v1/chat/completions` | SSE 流式聊天（OpenAI 兼容格式） |
| `GET` | `/api/sessions` | 获取所有会话列表（按更新时间倒序） |
| `POST` | `/api/sessions` | 创建新会话（可选 title + system_prompt） |
| `GET` | `/api/sessions/{id}` | 获取单个会话详情 |
| `DELETE` | `/api/sessions/{id}` | 删除会话及所有消息 |
| `GET` | `/api/sessions/{id}/messages` | 获取会话全部消息（按时间正序） |

### 分步启动（调试/学习用）

```bash
# 终端 1：后端
make server
# → http://127.0.0.1:8001

# 终端 2：前端
make dev
# → http://127.0.0.1:5173
```

### 环境变量（可选）

在 `server/` 目录下创建 `.env` 文件：

```bash
MODEL_PATH=models/Qwen2.5-7B-Instruct-4bit
ADAPTER_PATH=adapters/identity_lora
DATABASE_URL=sqlite:///chat.db
MAX_TOKENS_DEFAULT=512
TEMPERATURE_DEFAULT=0.7
CONTEXT_WINDOW_TOKENS=4096
HOST=0.0.0.0
PORT=8001
```

### 查看运行日志

```bash
tail -f logs/server.log
```

---

## 🔬 关键实现说明

### 1. 滑动窗口上下文截断

[server/llm.py:42-89]

大模型有最大上下文长度限制（Qwen2.5-7B 为 32768 tokens），多轮对话会不断增长直到 OOM。解决方案：

1. 始终保留所有 `system` 消息（角色定义不丢失）
2. 从最新消息向旧方向用 `tokenizer.encode()` **精确 token 计数**累加
3. 超过 `CONTEXT_WINDOW_TOKENS`（默认 4096）时丢弃更早的消息
4. 极端情况保护：如果截断后没有任何 chat 消息，至少保留最后一条

与"字符估算"不同，tokenizer 精确计数避免了中文场景下字符数≠token 数导致的 OOM 风险。

### 2. SSE 行缓冲解析

[frontend/src/stores/chat.ts] + [frontend/src/composables/useSSE.ts]

SSE 协议以 `\n` 分隔事件，但 TCP 字节流不保证每次 `reader.read()` 返回完整行。处理方式：

```typescript
buffer += decoder.decode(value, { stream: true });
const lines = buffer.split("\n");
buffer = lines.pop() || "";  // 保留不完整末行，等待下一 chunk 拼接
```

这个细节决定了 token 渲染会不会出现"卡顿"或"粘包"——面试中高频考点。

### 3. 流式结束自动落盘

[server/routes/chat.py:91]

采用「SSE 流式传输 → 全量回复完成后一次性写入」策略，而非逐 token 写数据库：

- **一致性**：User 消息 + Assistant 完整回复在同一事务中写入
- **效率**：避免每条 SSE chunk 触发一次 SQL INSERT
- **会话管理**：无 `session_id` 时自动创建新会话，标题取首条用户消息前 30 字

### 4. `make_sampler` 温度采样

[server/llm.py:109-131]

MLX 的 `stream_generate()` 不接受裸 `temp` 参数——必须通过 `make_sampler(temp=temperature)` 构造 sampler callable 传入。`temperature=0` 时等价 argmax（确定性输出），`temperature=2.0` 时输出最随机。这个 API 细节直接影响生成质量，踩坑后才理解 MLX 的 `generate_step` 参数设计。

### 5. SQLite 时区修正

[server/schemas.py:55-58]

SQLite 不存储 `DATETIME` 的时区信息——从数据库读出的 `datetime` 对象的 `tzinfo` 为 `None`。前端解析 ISO 8601 字符串时若无时区标识，浏览器会误当本地时间处理导致显示偏差。解决：`@field_serializer` 检测缺失时区时自动补 `timezone.utc`，前端兜底检查 `endsWith("Z")`。

---

## 🩺 复现与排错指南

| 问题 | 可能原因 | 解决方式 |
|------|----------|----------|
| `make setup` 报 mlx-lm 缺失 | 未在 cxllm 环境中 | `conda activate cxllm && pip install mlx-lm` |
| `make start` 报 model dir 不存在 | 模型未下载 | `make download-model` 或 `python scripts/download_model.py` |
| `make start` 报 port 8001 in use | 残留 Server 进程 | `make stop` 后重试 |
| 启动后 /health 一直超时 | MLX 模型加载慢（首次 10-30s） | 等待，`make start` 最长等 120s |
| Server 报 `generate_step() got unexpected keyword argument 'temp'` | 旧版 `stream_generate` 参数不兼容 | 使用 `make_sampler(temp=...)` 构造 sampler（当前已修复） |
| 前端 SSE 输出重复/粘包 | 行缓冲解析未生效 | 确认 `useSSE.ts` 的 `parseSSELine` 正确拆行 |
| TailwindCSS 样式不生效 | Vite 插件未加载 | 确认 `vite.config.ts` 有 `tailwindcss()` 插件 |
| 中文输入法 Enter 误发送 | IME composing 未检测 | 确认 `e.isComposing` 检查（当前已修复） |
| `/docs` 页面 404 | Server 未启动 | `curl http://127.0.0.1:8001/health` |
| 模型下载很慢 | 直连 HuggingFace | `download_model.py` 已自动使用国内镜像 `hf-mirror.com` |

---

## 🗺 学习路线中的位置

```
大模型应用工程师学习路线 (3 个月)

Week 1: MLX 本地模型实验          ← 📍 你在这里（本项目）
Week 2: llama.cpp GGUF serving    ← 后续：C++ 推理引擎 + API Gateway + 并发压测
Week 3: LangChain / LangGraph     ← 后续：Agent 编排框架
Week 4: RAG 检索增强生成          ← 后续：向量数据库 + 文档检索
Week 5: 智能路由网关              ← 后续：多模型路由 / fallback / 负载均衡
```

**前置知识**：Python 基础、命令行操作、HTTP 基本概念、了解 LLM 推理基本概念。

**本项目 vs Week 2 (llamacpp-serving-lab) 的区别**：

| 维度 | 本项目 (MLX) | Week 2 (llama.cpp) |
|------|-------------|---------------------|
| 推理框架 | Apple MLX (Python native) | llama.cpp (C++ server) |
| 模型格式 | MLX directory | GGUF single file |
| 架构复杂度 | 2 层（Server + Frontend） | 3 层（llama-server + Gateway + Frontend） |
| 数据库 | ✅ SQLite 持久化 | ❌ 无持久化 |
| 鉴权/限流 | ❌ 无 | ✅ API Key + 滑动窗口限流 |
| 测试 | ❌ 无 | ✅ 23 tests |

两个项目互补：本项目侧重 MLX 框架理解 + 全栈体验，llamacpp-serving-lab 侧重企业级中间件栈 + 性能工程。

---

## 🗺 Roadmap

### 短期优化
- [ ] 添加 pytest 后端测试 + vitest 前端测试
- [ ] 前端添加非流式模式切换
- [ ] `.env` 文件统一到项目根目录（当前在 `server/` 下）

### 中期增强
- [ ] 多轮对话 JSONL 数据集扩展（ShareGPT 格式，50+ 条）
- [ ] DPO 直接偏好优化实验
- [ ] KV Cache 量化（`mlx.nn.KVCache(bits=4)`）降低长文本内存
- [ ] `mx.compile()` JIT 编译加速推理

### 长期演进
- [ ] 接入 Gateway 模式（统一鉴权/限流/监控，对标 llamacpp-serving-lab）
- [ ] 投机采样（Qwen2.5-0.5B draft + 7B verify，Apple Silicon 1.5-2x 加速）
- [ ] 多模态推理（接入 MLX 视觉模型）
- [ ] 前端 E2E 测试（Playwright）

---

## ⚖️ License

本项目代码采用 [MIT License](https://opensource.org/licenses/MIT)。

使用的开源项目与模型：

| 项目 | License | 用途 |
|------|---------|------|
| [MLX](https://github.com/ml-explore/mlx) | MIT | Apple Silicon 机器学习框架 |
| [mlx-community/Qwen2.5-7B-Instruct-4bit](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit) | Apache 2.0 + Qwen License | 基座模型（MLX 4-bit 量化） |
| [FastAPI](https://github.com/fastapi/fastapi) | MIT | API 框架 |
| [SQLModel](https://github.com/fastapi/sqlmodel) | MIT | ORM |
| [Vue.js](https://github.com/vuejs/core) | MIT | 前端框架 |
| [Pinia](https://github.com/vuejs/pinia) | MIT | 状态管理 |
| [TailwindCSS](https://github.com/tailwindlabs/tailwindcss) | MIT | CSS 框架 |
| [markdown-it](https://github.com/markdown-it/markdown-it) | MIT | Markdown 渲染 |
| [highlight.js](https://github.com/highlightjs/highlight.js) | BSD-3-Clause | 代码语法高亮 |

## 👤 Author

**晨熙** — 大模型应用工程师学习实践。

---

> 💡 这个项目不仅是"跑起来一个聊天界面"——去改 `CONTEXT_WINDOW_TOKENS` 看滑动窗口何时触发截断，去注释掉 LoRA adapter 对比微调前后的回答风格差异，去 `tail -f logs/server.log` 看 MLX 模型加载过程。工程师和"跑过 demo"的区别，就在于你多问的那几个"如果改了 X，Y 会怎样"。
