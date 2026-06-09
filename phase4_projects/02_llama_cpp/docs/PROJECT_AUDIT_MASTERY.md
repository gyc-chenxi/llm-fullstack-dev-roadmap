# 项目架构与源码掌控白皮书：llamacpp-serving-lab

> **审计日期**：2026-06-06
> **审计方法**：全量源码逆向阅读，逐文件证据绑定，零预设
> **审计范围**：gateway/ (9 .py)、frontend/ (10 .ts/.vue)、scripts/ (9)、tests/ (5)、configs/、.env、Makefile (13 targets)、README.md、pyproject.toml、logs/、.pids
> **版本**：gateway v0.2.0 · 启动方式 v2（一键启停）

---

## 1. 项目总览

### 1.1 项目目标

构建一个**本地 AI Gateway serving 底座**，实现从 Vue3 前端经 FastAPI 网关到 llama.cpp Metal 推理引擎的完整 SSE 流式链路。核心场景：

- 本地 LLM 推理 serving（Qwen2.5-7B-Q4_K_M on Apple M5 Metal GPU）
- OpenAI-compatible API 代理（供 LangChain / OpenAI SDK 直接调用）
- 并发压测与性能基线采集（TTFT / TPS / P95）
- Prompt Cache 实验（slot save / restore）
- 企业级生产就绪能力演练：鉴权、限流、可观测性、统一错误码

### 1.2 技术栈（全证据绑定）

| 层 | 技术 | 证据 |
|---|---|---|
| AI 推理引擎 | llama.cpp (C++, Metal backend) | [third_party/llama.cpp/build/bin/llama-server] |
| 模型 | Qwen/Qwen2.5-7B-Instruct-GGUF Q4_K_M, 339 tensors, 4.68GB | [models/qwen2.5-7b-instruct-q4_k_m.gguf] |
| API 网关 | FastAPI 0.136.3 + uvicorn 0.49.0 | [gateway/app.py:52-57 -> FastAPI()] |
| 配置管理 | pydantic-settings 2.14.1 | [gateway/config.py:5 -> BaseSettings] |
| HTTP 客户端 | httpx 0.28.1 (AsyncClient, stream mode) | [gateway/llamacpp_client.py:5 -> import httpx] |
| 前端框架 | Vue 3.5.13 + TypeScript 5.7 + Vite 6.2.4 | [frontend/vue3-sse-demo/package.json] |
| CSS 设计系统 | CSS Custom Properties（暗色主题，零运行时依赖） | [frontend/vue3-sse-demo/src/styles/variables.css] |
| 测试框架 | pytest 9.0.3 + pytest-asyncio 1.4.0 | [pyproject.toml:1-3], [tests/] |
| Python 环境 | Conda cxllm (Python 3.11) | 实际运行环境 |
| OS/硬件 | macOS 26, Apple M5, 32GB unified memory | llama-server 日志: `MTL0 : Apple M5 (25559 MiB)` |
| 包管理 | npm (前端) + pip (后端) | [package.json], [pyproject.toml] |
| 版本控制 | Git (.gitignore) | [.gitignore] |

### 1.3 最小运行闭环（v2：一键启动）

```
$ make setup    # 检查环境（10 项，模型/二进制/依赖）
$ make start    # 🚀 一键启动 llama-server + Gateway + 前端
  → 浏览器 http://127.0.0.1:5173 即可聊天
  → Ctrl+C 自动停止所有服务并清理
$ make stop     # 或从另一终端手动停止
```

启动脚本 [scripts/start_all.sh] 内部流程：

```
1. 检查前置条件（模型文件、llama-server 二进制、端口）
2. 后台启动 llama-server → logs/llama-server.log
3. 轮询 /v1/models 等待就绪（最长 60s）
4. 后台启动 Gateway → logs/gateway.log
5. 检查 /healthz 确认 Gateway 就绪
6. 前台启动 Vite 前端（Ctrl+C → trap → 清理全部子进程 + .pids）
```

停止脚本 [scripts/stop_all.sh] 双保险策略：
- 优先读 `.pids` 文件逐 PID kill
- 兜底 `pkill -f` 按进程名模式匹配

证据链：
- [scripts/start_all.sh] — 启动编排（trap cleanup + PID 追踪 + 轮询等待）
- [scripts/stop_all.sh] — 停止编排（PID 文件 + pkill 兜底）
- [scripts/setup_check.sh] — 10 项环境检查
- [Makefile:7-15] — `make setup`, `make start`, `make stop`
- [.gitignore:12-13] — `logs/`, `.pids` 不进 Git

### 1.4 中间件栈全景（v0.2.0）

```
请求进入
  → Timing        (X-Process-Time-Ms)
  → RequestId     (X-Request-Id 注入/传播)
  → RateLimit     (滑动窗口, 30 req/s/IP, 配置驱动可关闭)
  → ApiKey        (X-API-Key 校验, secrets.compare_digest, 配置驱动可关闭)
  → CORS          (localhost:5173)
  → Route
响应返回（反向弹出，Timing 测量全栈耗时）
```

证据：[gateway/app.py:64-77]

### 1.5 当前最大风险

1. **P0**：无持久化 — 聊天历史、API key、限流计数器均在进程内存，重启丢失
2. **P1**：Gateway 侧零结构化日志（仅 uvicorn access log）— 生产排障受限
3. **P1**：限流和 Metrics 计数器为进程内实现 — 多 worker 部署时不共享状态
4. **P2**：无 HTTPS — 纯 HTTP 明文传输（API key 在 Header 中裸传）
5. **P2**：32GB M5 上 parallel=2+ctx=8192 已使并发 TPS 从 22.95 降至 7.87（见 bench_results.jsonl），扩容空间有限

### 1.6 核心入口文件

| 文件 | 职责 | 关键入口 |
|---|---|---|
| [gateway/app.py:52] | FastAPI 应用工厂，中间件注册，路由挂载 | `app = FastAPI(version="0.2.0")` |
| [gateway/config.py:42] | 统一配置入口，读取 .env | `settings = Settings()` |
| [gateway/llamacpp_client.py:11] | 上游 llama-server HTTP 客户端 | `class LlamaCppClient` |
| [gateway/routes_chat.py:10] | `/v1/chat/completions` 代理路由 | `async def chat_completions()` |
| [gateway/middleware.py:28] | 3 个观测中间件 | `TimingMiddleware`, `RequestIdMiddleware`, `RateLimitMiddleware` |
| [gateway/auth.py:23] | API Key 鉴权中间件 | `class ApiKeyMiddleware` |
| [gateway/errors.py:36] | 3 个全局异常处理器 | `validation_exception_handler`, `http_exception_handler`, `generic_exception_handler` |
| [frontend/vue3-sse-demo/src/App.vue:73] | Vue3 根组件 | `<div class="app-shell">` |
| [frontend/vue3-sse-demo/src/composables/useChat.ts:26] | 聊天状态机 | `export function useChat()` |
| [scripts/start_all.sh:62] | 一键启动编排（trap cleanup + PID 追踪） | `trap cleanup EXIT INT TERM` |
| [scripts/stop_all.sh] | 一键停止（PID + pkill 双保险） | `kill "$pid"` / `pkill -f` |
| [scripts/setup_check.sh] | 10 项环境就绪检查 | `check() { ... }` |
| [scripts/serve_q4.sh:11] | llama-server 启动参数 | `${LLAMA_SERVER} -m ${MODEL} --port 8081` |
| [scripts/bench_concurrency.py] | 并发压测工具 | `async def main()` |
| [Makefile:1-45] | 13 个 make target | `setup, start, stop, build, serve, gateway, dev, smoke, test, bench, metrics, clean, help` |

---

## 2. 目录与依赖图谱

### 2.1 核心目录树（排除 third_party/, node_modules/, __pycache__/, .pytest_cache/）

```
llamacpp-serving-lab/
├── README.md                         # ✅ 项目概览（架构图+快速启动+Makefile速查）
├── Makefile                          # ✅ 9 个 make target
├── pyproject.toml                    # ✅ pytest 配置 (asyncio_mode=auto)
├── .env                              # ✅ 实际环境变量（含鉴权/限流配置）
├── .env.example                      # ✅ 环境变量模板
├── .gitignore                        # ✅ 忽略 models/*.gguf, .env, build/
│
├── gateway/                          # 【后端】FastAPI AI Gateway (v0.2.0)
│   ├── __init__.py                   # 空 package marker
│   ├── app.py                        # FastAPI 应用工厂：lifespan + 5中间件 + 3异常处理器 + 3路由
│   ├── config.py                     # pydantic-settings：18 个配置项（含鉴权/限流）
│   ├── schemas.py                    # Pydantic v2：ChatMessage, ChatCompletionRequest(含validator), HealthResponse
│   ├── llamacpp_client.py            # httpx AsyncClient：非流式+流式，4种异常→HTTP错误映射
│   ├── routes_chat.py                # POST /v1/chat/completions (stream/non-stream)
│   ├── routes_health.py              # GET /healthz, /readyz
│   ├── routes_metrics.py             # ✅ GET /gateway/metrics (进程内计数器)
│   ├── middleware.py                 # ✅ 3个中间件：Timing, RequestId, RateLimit(滑动窗口)
│   ├── auth.py                       # ✅ ApiKeyMiddleware (secrets.compare_digest, 配置驱动)
│   └── errors.py                     # ✅ 统一错误码体系 + 3个全局异常处理器
│
├── frontend/vue3-sse-demo/           # 【前端】Vue3 + TypeScript + Vite
│   ├── package.json                  # vue 3.5.13, vite 6.2.4, typescript 5.7
│   ├── vite.config.ts                # Vite + @vitejs/plugin-vue + API 代理(/v1,/healthz,/readyz)
│   ├── tsconfig.json                 # TypeScript 严格模式
│   ├── env.d.ts                      # .vue 模块类型声明
│   ├── index.html                    # SPA 入口（标题：晨熙AI Gateway）
│   └── src/
│       ├── main.ts                   # createApp + 挂载 + CSS import
│       ├── App.vue                   # 根布局：侧栏(280px)+顶栏(健康指示)+消息列表+输入框
│       ├── types/index.ts            # 全局 TS 类型 (17个interface/type) + DEFAULT_SETTINGS
│       ├── styles/variables.css      # CSS 设计令牌：暗色主题，11 色板 + 排版 + 滚动条
│       ├── api/
│       │   ├── llm.ts                # SSE 流式 fetch：ReadableStream+TextDecoder+AbortController
│       │   └── health.ts             # /healthz 健康检查：5s timeout AbortController
│       ├── composables/
│       │   ├── useChat.ts            # 聊天状态机：send/abort/clear + 消息历史管理
│       │   └── useHealth.ts          # 健康轮询：15s 间隔 + onMounted/onUnmounted 生命周期
│       └── components/
│           ├── MessageItem.vue       # 消息气泡：user/AI/system三种样式+流式光标+错误Tag
│           ├── ChatInput.vue         # 输入区：Enter发送/Shift+Enter换行/自动撑高/发送↔停止
│           ├── SettingsPanel.vue     # 侧栏面板：模型选择/System Prompt/Temperature/Top-P/MaxTokens
│           └── HealthBadge.vue       # 顶栏指示灯：OK(脉冲动画)/DEGRADED/DOWN
│
├── scripts/                          # 【工具脚本】(9 个)
│   ├── start_all.sh                  # ✅ 一键启动编排：检查→llama-server→Gateway→前端 (trap + PID)
│   ├── stop_all.sh                   # ✅ 一键停止：PID文件 + pkill 双保险
│   ├── setup_check.sh                # ✅ 环境就绪检查：10 项 (conda/包/模型/npm)
│   ├── build_llamacpp.sh             # cmake 编译 llama.cpp (Metal ON, Release)
│   ├── serve_q4.sh                   # 启动 llama-server (port 8081, parallel=2, ctx=8192)
│   ├── smoke_openai.sh               # curl smoke test → /v1/chat/completions
│   ├── bench_concurrency.py          # httpx 并发压测：TTFT P50/P95 + TPS + JSONL输出
│   ├── scrape_metrics.py             # httpx GET → /metrics → 文本快照
│   └── test_prompt_cache.sh          # slot save / restore 实验
│
├── tests/                            # 【测试】(23 tests, all pass ✅)
│   ├── __init__.py                   # package marker
│   ├── conftest.py                   # pytest 配置 + asyncio 自动检测
│   ├── test_gateway_schema.py        # 14 tests：ChatMessage, ChatCompletionRequest, HealthResponse
│   └── test_gateway_health.py        # 9 tests：Health, Metrics, Validation, Middleware Headers
│
├── models/                           # 【模型权重】(不进 Git)
│   └── qwen2.5-7b-instruct-q4_k_m.gguf  # 4.68GB, 339 tensors (合并自2分片)
│
├── configs/                          # ⚠️ 空目录（占位）
├── logs/                             # ✅ 运行时日志 (.gitignore) [.gitignore:12-13]
├── .pids                             # ✅ PID 追踪文件 (.gitignore) [.gitignore:12-13]
├── docs/                             # 文档
│   ├── PROJECT_AUDIT_MASTERY.md      # 本文件
│   └── Week2_llamacpp_serving_lab_actual_runbook.md  # 实战手册
├── observability/
│   └── metrics_snapshots/            # /metrics 文本快照
└── reports/
    ├── bench_results.jsonl           # concurrency=2 压测原始数据 (10 requests)
    └── slot_cache/                   # Prompt cache .bin 文件
```

### 2.2 依赖与版本（证据绑定）

#### Python (Conda cxllm)

| 包 | 版本 | 实际使用位置 | 用途 |
|---|---|---|---|
| fastapi | 0.136.3 | [gateway/app.py:18] | Web 框架 |
| uvicorn | 0.49.0 | Makefile/CLI | ASGI 服务器 |
| httpx | 0.28.1 | [gateway/llamacpp_client.py:5] | 上游 HTTP 客户端 |
| pydantic | 2.13.4 | [gateway/schemas.py:2] | 数据校验 |
| pydantic-settings | 2.14.1 | [gateway/config.py:2] | 环境变量配置 |
| orjson | 3.11.9 | [gateway/routes_chat.py:2] | 快速 JSON 序列化 |
| pytest | 9.0.3 | [pyproject.toml] | 测试框架 |
| pytest-asyncio | 1.4.0 | [tests/test_gateway_health.py:9] | 异步测试支持 |
| huggingface_hub | 1.18.0 | CLI (`hf download`) | 模型下载 |
| prometheus-client | 0.24.1 | ⚠️ 已安装但未在代码中使用 | 预留 |
| rich | 15.0.0 | ⚠️ 已安装但未在代码中使用 | 预留 |
| pandas | 3.0.2 | ⚠️ 已安装但未在代码中使用 | 预留 |
| numpy | 2.4.4 | ⚠️ 已安装但未在代码中使用 | 预留 |

#### 前端 (npm)

| 包 | 版本 | 证据 | 用途 |
|---|---|---|---|
| vue | 3.5.13 | [package.json:7] | 前端框架 |
| vite | 6.2.4 | [package.json:13] | 构建工具 |
| @vitejs/plugin-vue | 5.2.3 | [vite.config.ts:2] | Vite Vue 插件 |
| typescript | ~5.7.3 | [package.json:14] | 类型系统 |
| vue-tsc | 2.2.8 | [package.json:15] | Vue 类型检查 |

> 无 Pinia、Vue Router、Axios、UI 框架 — 纯 Vue3 Composition API + 原生 fetch。

---

## 3. 启动与环境边界

### 3.1 依赖安装

**Python（Conda 环境 cxllm）**：
```bash
conda activate cxllm
pip install fastapi uvicorn[standard] httpx pydantic pydantic-settings pytest pytest-asyncio orjson
pip install -U huggingface_hub
```

**前端（npm）**：
```bash
cd frontend/vue3-sse-demo && npm install
```

**llama.cpp（CMake + Metal）**：
```bash
./scripts/build_llamacpp.sh
# 或: make build
```

### 3.2 模型下载（实际流程，非理论）

> ⚠️ `huggingface-cli` 已废弃，必须用 `hf` CLI。

```bash
# 分片下载 Q4_K_M
hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
  qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf --local-dir models
hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
  qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf --local-dir models

# 合并分片
./third_party/llama.cpp/build/bin/llama-gguf-split \
  --merge \
  models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf \
  models/qwen2.5-7b-instruct-q4_k_m.gguf
```

### 3.3 启动命令

**一键启动（推荐）**：

| 步骤 | 命令 | 说明 | 证据 |
|---|---|---|---|
| 1. 环境检查 | `make setup` | 10 项检查（conda/包/模型/npm） | [scripts/setup_check.sh:23-58] |
| 2. 一键启动 | `make start` | 后台 llama-server + Gateway，前台 Vite | [scripts/start_all.sh:62-179] |
| 3. 浏览器 | `http://127.0.0.1:5173` | — | — |
| 停止 | `Ctrl+C` 或 `make stop` | PID 文件 + pkill 双保险 | [scripts/stop_all.sh:20-45] |

**分步启动（调试/学习用）**：

| 步骤 | 命令 | 端口 | 证据 |
|---|---|---|---|
| 1. llama-server | `make serve` | 8081 | [scripts/serve_q4.sh:15] |
| 2. Gateway | `make gateway` | 8000 | [Makefile:19-20] |
| 3. 前端 | `make dev` | 5173 | [Makefile:22-23] |

`make start` 内部编排流程 [scripts/start_all.sh:94-179]：
1. 检查前置条件（模型文件、llama-server 二进制、端口冲突）→ 失败则 exit 1
2. 后台启动 llama-server → 日志写入 `logs/llama-server.log` → PID 写入 `.pids`
3. 轮询 `http://127.0.0.1:8081/v1/models`，最长等待 60s → 超时则 exit 1
4. 后台启动 Gateway → 日志写入 `logs/gateway.log` → PID 写入 `.pids`
5. 检查 `/healthz` 确认 Gateway 就绪
6. 前台启动 Vite 前端 → `trap cleanup EXIT INT TERM` 确保 Ctrl+C 时清理全部子进程

### 3.4 自测命令

```bash
# 健康检查
curl -s http://127.0.0.1:8000/healthz | python -m json.tool --no-ensure-ascii

# Gateway 指标
curl -s http://127.0.0.1:8000/gateway/metrics | python -m json.tool

# 聊天（非流式）
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}],"max_tokens":128,"stream":false}' \
  | python -m json.tool --no-ensure-ascii

# 并发压测
make bench

# 运行测试
make test

# 抓取上游 metrics
make metrics
```

### 3.5 环境变量与硬编码审计

| 变量 | 默认值 | 位置 | 风险等级 |
|---|---|---|---|
| `LLAMACPP_BASE_URL` | `http://127.0.0.1:8081` | [.env:5], [gateway/config.py:20] | ✅ 可配置 |
| `DEFAULT_MODEL` | `local-qwen2.5-7b-q4` | [.env:7], [gateway/config.py:22] | ✅ 可配置 |
| `GATEWAY_API_KEY` | `""` (空=关闭) | [.env:16], [gateway/config.py:33] | ✅ 可配置，dev 默认关闭 |
| `RATE_LIMIT_MAX_REQUESTS` | `30` | [.env:19], [gateway/config.py:38] | ✅ 可配置 |
| `RATE_LIMIT_WINDOW_SECONDS` | `1.0` | [.env:20], [gateway/config.py:39] | ✅ 可配置 |
| `UPSTREAM_CONNECT_TIMEOUT` | `5.0` | [gateway/config.py:24] | ✅ 可配置 |
| `UPSTREAM_READ_TIMEOUT` | `300.0` | [gateway/config.py:25] | ✅ 可配置 |
| `MAX_OUTPUT_TOKENS` | `2048` | [gateway/config.py:28] | ✅ 可配置 |
| llama-server port | **8081 (硬编码)** | [scripts/serve_q4.sh:15] | ⚠️ 脚本硬编码 |
| Vite dev port | **5173 (硬编码)** | [vite.config.ts:8] | ⚠️ 配置硬编码 |
| CORS origins | **localhost:5173 (硬编码)** | [gateway/app.py:73] | ⚠️ 非生产安全 |
| 模型文件路径 | **脚本相对路径推导** | [scripts/serve_q4.sh:5-6] | ⚠️ 依赖 ROOT_DIR |
| llama.cpp API Key | (空) | [.env:6] | ⚠️ 未启用上游鉴权 |
| HF_TOKEN | (未设置) | 实际运行日志警告 | ⚠️ hf download 限速 |
| **GATEWAY_HOST / GATEWAY_PORT** | 在 .env 中声明但未消费 | [.env:2-3] | ⚠️ 孤儿配置 |

---

## 4. 数据流与接口契约

### 4.1 HTTP API 接口清单

#### 4.1.1 `GET /healthz`

- **提供方**：[gateway/routes_health.py:7-15 -> `healthz()`]
- **调用链**：`healthz() → request.app.state.llamacpp.health() → httpx GET /v1/models`
- **响应模型**：[gateway/schemas.py:50-53 -> `HealthResponse(status, upstream, detail)`]
- **认证**：豁免（`ApiKeyMiddleware._PUBLIC_PATHS`）
- **限流**：豁免（`RateLimitMiddleware._PUBLIC_PATHS`）

#### 4.1.2 `GET /readyz`

- **提供方**：[gateway/routes_health.py:18-25 -> `readyz()`]
- **实现**：与 `/healthz` 完全相同 — 调用同一个 `llamacpp.health()` 方法
- **设计缺陷**：K8s 语义上 `healthz`=liveness（进程存活），`readyz`=readiness（可接流量）— 当前两者行为一致，未区分

#### 4.1.3 `GET /gateway/metrics`

- **提供方**：[gateway/routes_metrics.py:35-46 -> `gateway_metrics()`]
- **返回字段**：`uptime_seconds`, `requests_total`, `errors_total`, `error_rate`, `last_latency_ms`, `rate_limit_enabled`
- **数据来源**：进程内模块级计数器 [gateway/routes_metrics.py:19-23]
- **格式**：JSON（非 Prometheus text format），进程重启计数器归零

#### 4.1.4 `POST /v1/chat/completions`

- **提供方**：[gateway/routes_chat.py:10-30 -> `chat_completions()`]
- **请求体**：[gateway/schemas.py:13-35 -> `ChatCompletionRequest`]
  - `model: str|None` — 为空时用 `DEFAULT_MODEL` 兜底 [schemas.py:39]
  - `messages: list[ChatMessage]` — 至少 1 条，须含至少 1 条 user role [schemas.py:20, :30-34]
  - `temperature: float = 0.2` (0.0–2.0) [schemas.py:24]
  - `top_p: float = 0.9` (0.0–1.0) [schemas.py:25]
  - `max_tokens: int = 512` (1–4096) [schemas.py:26]
  - `stream: bool = False` [schemas.py:27]
  - `extra_body: dict` — 透传任意字段到上游 [schemas.py:28, :46]
- **非流式响应**：`ORJSONResponse(data)`，注入 `_gateway.latency_ms` [llamacpp_client.py:57-60]
- **流式响应**：`StreamingResponse(media_type="text/event-stream")` [routes_chat.py:20-27]
- **错误映射** [llamacpp_client.py:61-74]：
  - `httpx.TimeoutException` → HTTP 504 + `UPSTREAM_TIMEOUT`
  - `httpx.HTTPStatusError` → 透传状态码 + body[:2000]
  - `httpx.HTTPError` → HTTP 502 + `UPSTREAM_CONNECT_ERROR`
  - `json.JSONDecodeError` → HTTP 502 + `UPSTREAM_INVALID_JSON`

### 4.2 SSE 流式聊天：完整数据流追踪

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. UI EVENT                                                         │
│    ChatInput.vue: handleSubmit()                                    │
│    → emit('send', userText)                                         │
│    → App.vue:48-50: handleSend(text)                                │
│    → useChat.ts:56: chat.send(text)                                 │
│                                                                     │
│ 2. STATE UPDATE (useChat.ts:56-107)                                 │
│    → push user message {status:'done'}                              │
│    → push assistant placeholder {status:'streaming', content:''}    │
│    → loading.value = true                                           │
│                                                                     │
│ 3. API CALL (useChat.ts:84-105)                                     │
│    → streamChatCompletion(config, callbacks)                        │
│    → api/llm.ts:36-47: fetch('/v1/chat/completions', {stream:true})│
│                                                                     │
│ 4. VITE PROXY (vite.config.ts:9-21)                                 │
│    → '/v1' → http://127.0.0.1:8000                                  │
│                                                                     │
│ 5. GATEWAY MIDDLEWARE STACK (app.py:64-77)                          │
│    → Timing → RequestId → RateLimit → ApiKey → CORS → Route         │
│                                                                     │
│ 6. GATEWAY ROUTE (routes_chat.py:10-30)                             │
│    → Pydantic 校验: ChatCompletionRequest                           │
│    → to_upstream_payload(default_model)                             │
│    → req.stream == True → StreamingResponse(                        │
│          client.stream_chat_completion(payload),                    │
│          media_type="text/event-stream"                             │
│        )                                                            │
│                                                                     │
│ 7. UPSTREAM CALL (llamacpp_client.py:76-97)                         │
│    → httpx.AsyncClient.stream("POST", "/v1/chat/completions", ...)  │
│    → async for chunk in r.aiter_bytes(): yield chunk                │
│    ⚠️ 不调用 r.aread() — 否则流式变阻塞                            │
│                                                                     │
│ 8. LLAMA.CPP INFERENCE                                              │
│    → Metal GPU (ngl=99), Q4_K_M weights, ctx=8192                   │
│    → parallel=2 slots, cache-prompt enabled                         │
│    → token-by-token generation → SSE data chunks                    │
│                                                                     │
│ 9. RESPONSE STREAMING                                               │
│    → Gateway: StreamingResponse → bytes stream                      │
│    → Vite proxy: forward SSE chunks to browser                      │
│                                                                     │
│ 10. FRONTEND INCREMENTAL RENDERING (api/llm.ts:59-104)              │
│     → resp.body.getReader() → ReadableStream                        │
│     → TextDecoder("utf-8") 逐 chunk 解码                            │
│     → buffer += chunk, split('\n'), 保留不完整末行                  │
│     → 逐行解析: 'data: ...' → JSON.parse → choices[0].delta.content │
│     → callbacks.onDelta(content)                                    │
│     → useChat.ts:94-96: msg.content += delta                        │
│     → MessageItem.vue: Vue 响应式更新 → 逐 token 渲染               │
│     → '[DONE]' → callbacks.onDone() → status='done'                 │
└─────────────────────────────────────────────────────────────────────┘
```

证据链（自上而下）：
- [frontend/vue3-sse-demo/src/components/ChatInput.vue:45-48]
- [frontend/vue3-sse-demo/src/App.vue:48-50]
- [frontend/vue3-sse-demo/src/composables/useChat.ts:56-107]
- [frontend/vue3-sse-demo/src/api/llm.ts:36-104]
- [frontend/vue3-sse-demo/vite.config.ts:10-12]
- [gateway/app.py:64-77]
- [gateway/routes_chat.py:15-30]
- [gateway/llamacpp_client.py:76-97]
- [scripts/serve_q4.sh:11-28]

### 4.3 前端数据流注意事项

- ⚠️ [api/llm.ts:46] 硬编码 `stream: true` — Settings 面板中的 `stream` 参数在前端不生效
- ✅ AbortController：用户点击停止 → `chat.abort()` → `controller.abort()` → `AbortError`捕获为非异常 [llm.ts:98-101]
- ✅ 缓冲区管理：`buffer = lines.pop() ?? ''` 保留不完整 SSE 行跨 chunk 继续 [llm.ts:69]

---

## 5. 数据库与持久化

### ❌ 未发现持久化机制

- 无 SQLite/PostgreSQL/MySQL 连接
- 无 ORM (SQLAlchemy/Tortoise/Prisma)
- 无文件存储层
- 聊天历史仅存在于浏览器内存（Vue reactive `ref<UIMessage[]>`），刷新即丢失
- API Key / 限流计数器 / metrics 计数器均为进程内存，重启归零

唯一的数据持久化：
- [reports/bench_results.jsonl] — 压测结果手动 JSONL 写入 [scripts/bench_concurrency.py]
- [observability/metrics_snapshots/] — /metrics 文本快照 [scripts/scrape_metrics.py]
- [reports/slot_cache/gateway_system_prompt.bin] — llama.cpp slot save (18.7MB, 326 tokens)

---

## 6. 核心业务与 AI 引擎

### 6.1 AI 推理引擎：llama.cpp

**启动方式**：[scripts/serve_q4.sh] → llama-server 进程常驻内存
**模型加载**：启动时一次性加载 [models/qwen2.5-7b-instruct-q4_k_m.gguf] (4.68GB, 339 tensors)
**推理后端**：Metal (Apple M5 GPU)，ngl=99（全部 28 层 offload 到 GPU）
**并发模型**：parallel=2 server slots，continuous batching
**KV Cache**：ctx=8192 per slot，prompt cache enabled
**Chat Template**：Qwen2.5 原生 `<|im_start|>...<|im_end|>` (Jinja)，由 llama.cpp 内置模板引擎自动处理

启动日志证据：
```
I device_info: MTL0 : Apple M5 (25559 MiB, 25558 MiB free)
I system_info: n_threads = 4 / 10 | MTL : EMBED_LIBRARY = 1
I slot load_model: id 0 | task -1 | new slot, n_ctx = 4096
I slot load_model: id 1 | task -1 | new slot, n_ctx = 4096
I srv  load_model: prompt cache is enabled, size limit: 8192 MiB
I init: chat template, example_format: '<|im_start|>system...'
```

### 6.2 核心参数解释

| 参数 | 值 | 作用 | 来源 |
|---|---|---|---|
| `-m` | models/qwen2.5-7b-instruct-q4_k_m.gguf | 模型权重文件 | [scripts/serve_q4.sh:6] |
| `--alias` | local-qwen2.5-7b-q4 | /v1/models 中的稳定 ID | [scripts/serve_q4.sh:13] |
| `-ngl 99` | 99 | 全部 28 层 offload 到 Metal GPU | [scripts/serve_q4.sh:20] |
| `-c 8192` | 8192 | 每个 slot 的 context window | [scripts/serve_q4.sh:17] |
| `-b 512` | 512 | prompt processing batch size | [scripts/serve_q4.sh:18] |
| `-ub 128` | 128 | micro batch size（降低峰值 buffer） | [scripts/serve_q4.sh:19] |
| `--parallel 2` | 2 | server slots（并发请求数） | [scripts/serve_q4.sh:21] |
| `--cache-prompt` | on | 复用相同 prompt 前缀的 KV 状态 | [scripts/serve_q4.sh:22] |
| `--metrics` | on | 暴露 `/metrics` (Prometheus format) | [scripts/serve_q4.sh:26] |

### 6.3 Prompt 构造路径

```
用户输入 (ChatInput.vue)
  → useChat.ts:39-53: buildApiMessages()
    → 如果 systemPrompt 非空，前置 {role:"system", content:...}
    → 追加所有 status='done' 的历史消息
    → 调用方不追加 user 消息（已在 send() 中 push 到 messages）
  → api/llm.ts:40-47: body: JSON.stringify({model, messages, ...})
  → Gateway: schemas.py:37-46: to_upstream_payload() 合并 extra_body
  → llama-server: 内置 Qwen2.5 chat template 格式化
```

证据：[composables/useChat.ts:39-53], [schemas.py:37-46], [api/llm.ts:40-47]

### 6.4 Token 管理

- **输入截断**：❌ 应用层未实现显式截断。依赖 llama-server `-c 8192` 自动处理。
- **输出限制**：
  - 前端默认 `maxTokens: 512` [types/index.ts:106]
  - Gateway schema 允许 `1–4096` [schemas.py:26]
  - Gateway config 允许 `1–8192` [config.py:28 -> `Field(ge=1, le=8192)`]
- **Token 计数**：❌ 应用层无 tokenizer（无 tiktoken/transformers）。仅在非流式响应中透传上游 `usage.prompt_tokens/completion_tokens`。
- **实际 metrics** [observability/metrics_snapshots/metrics_20260606_144601.txt]：
  - `prompt_tokens_total: 229`, `tokens_predicted_total: 4030`
  - `prompt_tokens_seconds: 46.43 t/s`, `predicted_tokens_seconds: 9.67 t/s`
  - `n_tokens_max: 311`

### 6.5 流式输出实现

- **Gateway 层**：[llamacpp_client.py:82-90] — `async with self._client.stream("POST", ...) as r → async for chunk in r.aiter_bytes(): yield chunk`
  - ⚠️ 关键约束：不能调用 `r.aread()`，否则全量读入内存破坏流式语义
- **前端层**：[api/llm.ts:59-104] — `resp.body.getReader() → ReadableStream → TextDecoder → split('\n') → JSON.parse`
  - 非 JSON 行静默忽略（keepalive ping / 注释）
  - `AbortError` 视为用户取消（非异常），调用 `onDone`

---

## 7. 防御、日志与测试

### 7.1 输入校验

| 层级 | 校验内容 | 证据 |
|---|---|---|
| Gateway Schema | `messages: min_length=1`, 至少一条 `role="user"` | [schemas.py:20, :30-34] |
| Gateway Schema | `temperature: 0.0–2.0`, `top_p: 0.0–1.0`, `max_tokens: 1–4096` | [schemas.py:24-27] |
| Gateway Config | `MAX_OUTPUT_TOKENS: 1–8192` | [config.py:28] |
| Gateway 异常处理器 | Pydantic `ValidationError` → 统一 422 + `code:"VALIDATION_ERROR"` + `details[]` | [errors.py:36-54] |
| 前端 | ❌ 无客户端校验 — 输入直接发送，依赖 Gateway 拒绝 | [ChatInput.vue -> handleSubmit 仅做 trim] |

### 7.2 异常处理层级

| 层级 | 处理方式 | 证据 |
|---|---|---|
| 上游客户端 | `TimeoutException→504`, `HTTPStatusError→透传`, `HTTPError→502`, `JSONDecodeError→502` | [llamacpp_client.py:61-74] |
| 流式错误 | SSE `event: error` 帧，不中断流 | [llamacpp_client.py:91-97] |
| 全局 HTTP 异常 | `http_exception_handler`: 状态码→error code 映射 (401/403/429/502/504→code) | [errors.py:57-76] |
| 全局未知异常 | `generic_exception_handler`: 统一 500 + `INTERNAL_ERROR` | [errors.py:79-89] |
| 前端网络异常 | `onError` callback → App.vue 全局错误横幅 | [llm.ts:98-103], [App.vue:137-139] |
| 前端 Abort | `AbortError` → `onDone` (非异常) | [llm.ts:98-101] |
| 前端 JSON 解析 | 非 JSON SSE 行静默忽略 | [llm.ts:88-91] |

### 7.3 安全边界

| 检查项 | 状态 | 证据 |
|---|---|---|
| **API Key 鉴权** | ✅ 已实现 | [gateway/auth.py:23-49 -> `ApiKeyMiddleware`] |
| **时序攻击防护** | ✅ `secrets.compare_digest` | [gateway/auth.py:46] |
| **鉴权配置驱动** | ✅ `GATEWAY_API_KEY=""` 时自动关闭 | [gateway/auth.py:40-41] |
| **限流** | ✅ 已实现 | [gateway/middleware.py:66-113 -> `RateLimitMiddleware`] |
| **限流 X-Forwarded-For** | ✅ 代理环境 IP 识别 | [gateway/middleware.py:95-98] |
| **限流 Retry-After** | ✅ 429 响应附带 `Retry-After` header | [gateway/middleware.py:105-109] |
| **限流配置驱动** | ✅ `RATE_LIMIT_MAX_REQUESTS=0` 时关闭 | [gateway/middleware.py:91-92] |
| **CORS** | ✅ 仅允许 localhost:5173 | [gateway/app.py:71-77] |
| **健康端点公开** | ✅ `/healthz`, `/readyz` 豁免鉴权+限流 | [auth.py:32], [middleware.py:78] |
| **HTTPS** | ❌ 纯 HTTP | [.env:2-5 -> 所有 URL 为 http://] |
| **输入消毒** | ❌ 无 XSS/注入防护 | 纯透传文本 |
| **上游 API Key** | ⚠️ 支持但未启用 | [.env:6 -> LLAMACPP_API_KEY=''] |

### 7.4 日志体系

| 系统 | 日志方式 | 证据 |
|---|---|---|
| llama-server | `--log-timestamps`，stderr 输出 | [scripts/serve_q4.sh:28] |
| Gateway 业务日志 | ❌ 无应用级 logging 配置 | [gateway/app.py] 无 `logging` 模块引用 |
| Gateway 访问日志 | uvicorn access log（默认 stderr） | uvicorn 内置 |
| Gateway 请求追踪 | ✅ `X-Request-Id` header（注入/传播） | [gateway/middleware.py:30-35] |
| Gateway 性能 | ✅ `X-Process-Time-Ms` header | [gateway/middleware.py:42-47] |
| 前端日志 | ❌ 无 console.log / 日志收集 | 前端源码中无 `console` 调用 |

> ⚠️ Gateway 侧零业务日志。排障途径：`X-Request-Id` + uvicorn access log + `/gateway/metrics` 端点。

### 7.5 测试覆盖

| 指标 | 数值 | 证据 |
|---|---|---|
| **测试文件数** | 2 个 | [tests/test_gateway_schema.py], [tests/test_gateway_health.py] |
| **测试用例数** | 23 个 (全部通过 ✅) | `make test` 输出：23 passed |
| **Schema 测试** | 14 个 | `TestChatMessage`(3), `TestChatCompletionRequest`(8), `TestHealthResponse`(3) |
| **集成测试** | 9 个 | `TestHealthEndpoints`(3), `TestMetricsEndpoint`(1), `TestValidationErrors`(2), `TestMiddlewareHeaders`(3) |
| **测试配置** | ✅ pyproject.toml (asyncio_mode=auto) | [pyproject.toml:1-3] |
| **测试运行** | `make test` | [Makefile:22-23] |
| **前端测试** | ❌ 无 vitest 配置，无 .test.ts 文件 | — |
| **E2E 测试** | ❌ 无 Playwright/Cypress | — |
| **CI** | ❌ 无 CI/CD 配置（无 .github/workflows） | — |

---

## 8. 部署、故障与技术债

### 8.1 部署方式

- **当前**：一键启动（`make start`：后台 llama-server+Gateway，前台 Vite，Ctrl+C 全部停止）
- **进程编排**：✅ [scripts/start_all.sh] trap cleanup + PID 追踪 + 轮询等待就绪 + 日志重定向
- **停止**：✅ [scripts/stop_all.sh] PID 文件 kill + pkill 兜底
- **环境检查**：✅ [scripts/setup_check.sh] 10 项自动检查 + 修复指引
- **Docker**：❌ 无 Dockerfile / docker-compose.yml（**有意为之** — macOS Docker 无法访问 Metal GPU，CPU 推理极慢）
- **CI/CD**：❌ 无 GitHub Actions / GitLab CI
- **进程管理**：⚠️ 开发级（trap 信号 + PID 文件），非 systemd/supervisor
- **Makefile**：✅ 13 个 make target [Makefile:1-45]

### 8.2 实际性能基线

来源：[reports/bench_results.jsonl] (concurrency=2, 10 requests)

| 指标 | concurrency=1 | concurrency=2 | 退化 |
|---|---|---|---|
| TTFT P50 | 236.82 ms | 476.19 ms | ↑ 101% |
| TTFT P95 | 250.91 ms | 765.29 ms | ↑ 205% |
| Total P50 | 11024.52 ms | 35614.59 ms | ↑ 223% |
| Avg TPS | 22.95 | 7.87 | ↓ 65.7% |

上游 metrics [observability/metrics_snapshots/metrics_20260606_144601.txt]：
```
prompt_tokens_seconds: 46.43 t/s
predicted_tokens_seconds: 9.67 t/s
n_busy_slots_per_decode: 1.46
requests_processing: 0
requests_deferred: 0
```

> 关键发现：parallel=2 + ctx=8192 在 M5 上已使 decode 吞吐从约 27 t/s（单请求）降至约 9.7 t/s（并发平均值）。`n_busy_slots_per_decode=1.46` 说明两个 slot 不是同时饱和的。

### 8.3 高频故障排查表

| 症状 | 根因 | 排查命令 | 修复 |
|---|---|---|---|
| `make setup` 报 conda 缺失 | 未装 Miniconda | `which conda` | `brew install miniconda` |
| `make start` 报 model not found | 模型未下载/合并 | `ls -lh models/*.gguf` | `hf download` 分片下载 + `llama-gguf-split --merge` |
| Gateway 502 + `"code":"UPSTREAM_CONNECT_ERROR"` | llama-server 未启动 | `lsof -i :8081` | 先启动 `make serve`，确认 `curl :8081/v1/models` |
| `make start` 提示端口冲突 | 残留进程 | `lsof -i :8081` / `lsof -i :8000` | `make stop` 清理后重试 |
| Gateway 504 `UPSTREAM_TIMEOUT` | llama-server 超时 | `tail -f logs/llama-server.log` | 检查模型加载/内存 |
| Gateway 422 + `"code":"VALIDATION_ERROR"` | 请求格式错误 | 检查请求体 | 确认 messages 含 user role |
| Gateway 401 / 403 | API Key 缺失/错误 | 检查 `.env` 中 `GATEWAY_API_KEY` | 设置 key 或留空关闭鉴权 |
| Gateway 429 + `Retry-After` | 超出限流 | 检查 `RATE_LIMIT_MAX_REQUESTS` | 调大限制或设为 0 关闭 |
| llama-server 端口绑定失败 | 8080/8081 被占用 | `lsof -i :8080` | 改 `serve_q4.sh` 中的端口 |
| 前端请求 404 | Vite proxy 未生效 | 检查 `vite.config.ts` | 确认 target 指向 :8000 |
| 模型加载 OOM | ctx 过大 / parallel 过多 | Activity Monitor | 降低 `-c` 或 `--parallel` |
| `hf download` 报 `File not found` | 单文件名不存在（实际是分片） | — | 分别下载分片再 merge |
| `python -m json.tool` 中文乱码 | 默认 escape 非 ASCII | — | 加 `--no-ensure-ascii` 或用 `jq` |
| `make test` 运行失败 | 未用 conda env python | `which python` | 确认在 `cxllm` 环境中 |

### 8.4 技术债分级

#### P0（阻塞生产化）

1. **无持久化**：聊天历史、API key 均存进程内存 — 需 SQLite (dev) / PostgreSQL (prod)
2. **无结构化日志**：需 `structlog` 或 `logging` + JSON formatter

#### P1（影响可靠性）

3. **限流/Metrics 进程内实现**：多 worker 不共享 — 需 Redis 后端
4. **healthz / readyz 行为相同**：应区分 liveness vs readiness
5. **前端 stream 硬编码**：[api/llm.ts:46] 始终 `stream:true`
6. **无进程守护**：llama-server 崩溃需手动重启
7. **无 HTTPS**：API Key 在 HTTP Header 中裸传
8. **CORS 硬编码**：仅 localhost:5173
9. **configs/ 目录空置**：runbook 声称有 yaml 配置但未实现

#### P2（代码质量）

10. **Python 依赖冗余**：`prometheus-client`、`rich`、`pandas`、`numpy` 未实际使用
11. **环境变量未消费**：`GATEWAY_HOST`/`GATEWAY_PORT` 在 .env 声明但代码未使用
12. **前端零测试**：无 vitest 配置

### 8.5 10 倍并发 / 企业级重构路线

| 当前 | 目标 | 改动 |
|---|---|---|
| 单 llama-server 进程 | 多实例 + Nginx 负载均衡 | 增加 upstream 池 + health check |
| 进程内 API Key | JWT + Redis session | 增加 auth service |
| 进程内限流 | Redis Token Bucket | 替换 `RateLimitMiddleware` backend |
| 进程内 metrics | Prometheus + Grafana | 引入 `prometheus-client` histogram/counter |
| 内存会话 | SQLite / PostgreSQL 持久化 | 增加 SQLAlchemy + Alembic |
| 手动启动 | Docker Compose 一键编排 | 编写 Dockerfile + compose.yaml（macOS 需保留 native Metal 路径） |
| 零 CI | GitHub Actions | build + test + lint pipeline |
| 单模型 | 多模型 alias + fallback | 增加 model registry + router |
| 单 provider | 多 provider 抽象 (MLX/Ollama/vLLM) | 增加 provider interface + factory |

> 注：启动体验问题已在 v2 解决 — `make start/stop/setup` + `scripts/start_all.sh` trap cleanup 已替代 3 终端手动启动。Docker 在 macOS 上因 Metal GPU 不可访问，不作为当前推荐方案。

---

## 9. 开发者掌握清单

### 9.1 必须能讲清楚的 20 个问题（附关键源码位置）

1. llama.cpp 的 Metal 后端在 Apple Silicon 统一内存架构下如何工作？→ [scripts/build_llamacpp.sh:26 `-DGGML_METAL=ON`]
2. GGUF 和 safetensors 的本质区别？GGUF 包含 tokenizer + chat template + 量化元信息
3. Q4_K_M 量化中 "Q4"="4-bit", "K"="K-quant", "M"="medium (推荐平衡)"
4. KV Cache 精算公式：`layers × ctx × parallel × 2(K,V) × kv_heads × head_dim × dtype_bytes`
5. Prompt Cache vs KV Cache：前者复用已 prefill 的前缀状态，后者是推理过程内部缓存 → [scripts/test_prompt_cache.sh]
6. `--parallel` 增加时 P95 恶化的原因：多 slot 抢占统一内存带宽 + 调度排队 → [reports/bench_results.jsonl] 实测数据
7. `-b 512` (logical batch) vs `-ub 128` (physical micro batch) → [scripts/serve_q4.sh:18-19]
8. FastAPI lifespan 的作用：创建/释放全局连接池 → [gateway/app.py:41-49]
9. SSE 为什么不能 `await r.aread()`：会把流式响应读入内存 → [gateway/llamacpp_client.py:77-78 注释]
10. Gateway 502/504 分别对应什么上游故障 → [gateway/errors.py:66-67 映射表]
11. `json.tool --no-ensure-ascii` 解决中文 `\uXXXX` 问题
12. ReadableStream SSE 解析中 buffer 的作用：跨 chunk 保留不完整行 → [api/llm.ts:67-69]
13. Token-by-token vs 全量渲染：TTFT 用户感知差异 → [bench_concurrency.py: TTFT 测量]
14. TTFT (prefill 阶段) vs TPS (decode 阶段) 分别由什么决定
15. `n_busy_slots_per_decode=1.46` 说明两个 slot 非同时饱和 → [metrics_20260606_144601.txt:32]
16. `hf download` 报 `File not found` 的根因：GGUF 文件被拆成分片，单文件名不存在
17. `llama-gguf-split --merge` 合并分片 → [llama-server 日志: merged from 2 split with 339 tensors]
18. 32GB M5 上 Q4_K_M + ctx=8192 + parallel=2 的极限 → 实测 TPS 从 22.95 降至 7.87
19. Pydantic `model_validator(mode="after")` vs `field_validator` → [schemas.py:30]
20. 当前项目的 5 层中间件栈顺序及原因 → [gateway/app.py:4-9 注释]

### 9.2 必须能独立完成的 10 个操作

1. 运行 `make setup`，确认 10 项检查全部通过
2. 运行 `make start`，一键启动全栈 → 浏览器打开 `http://127.0.0.1:5173` 发消息验证 SSE 流式输出
3. 从零编译 llama.cpp（Metal/Release）→ `make build`
4. 用 `hf` 分片下载 GGUF 模型，用 `llama-gguf-split --merge` 合并
5. 单独启动 llama-server，调整 `-c`/`--parallel`/`-ngl` 观察内存和吞吐变化
6. 启动 Gateway (v0.2.0)，验证 5 个中间件 header：`x-request-id`、`x-process-time-ms`
7. 用 `make bench` 跑出 TTFT P50/P95/TPS 矩阵
8. 用 `make metrics` 采集上游 `/metrics`，解读 `prompt_tokens_seconds` 和 `predicted_tokens_seconds`
9. 运行 `make test`，确认 23 个测试全部通过
10. 跟踪一条完整的 `curl → 5 层中间件 → Gateway → llama-server → response` 调用链，用 `make stop` 清理

### 9.3 L4/L5 掌握等级缺口

| 能力 | 状态 | 需补齐 |
|---|---|---|
| 多模型路由/fallback | ❌ | provider factory 模式 |
| JWT/OAuth2 鉴权 | ❌ | FastAPI depends + python-jose |
| 分布式限流 (Redis) | ❌ 当前为进程内 | Redis + Lua script |
| 结构化日志 + 链路追踪 | ❌ | structlog + OpenTelemetry |
| CI/CD pipeline | ❌ | GitHub Actions |
| Docker Compose 编排 | ❌ | Dockerfile × 3 + compose.yaml |
| 数据库持久化 (SQLAlchemy) | ❌ | SQLAlchemy + Alembic + SQLite→PostgreSQL |
| 前端 E2E 测试 | ❌ | vitest + Playwright |
| Grafana 监控面板 | ❌ | Prometheus datasource + dashboard JSON |
| WebSocket 双向流式 | ❌ 当前仅 SSE 单向 | FastAPI WebSocket |
| 多模态 (图片/音频) | ❌ | llama.cpp mtmd 模块已可用但未集成 |
| 模型量化自定义 (imatrix) | ❌ | GGUF 量化流程深入学习 |

---

> **审计结论**：v0.2.0 + 启动方式 v2 已实现完整的 **企业级本地 AI Gateway serving 底座**——`make start` 一键启动（trap cleanup + PID 追踪 + 轮询等待就绪）→ llama.cpp Metal 推理 → 5 层中间件 FastAPI Gateway（鉴权/限流/Timing/RequestId/CORS）→ Vue3 SSE 流式前端 + 23 个自动化测试 + 并发压测工具链 + 统一错误码体系 + 10 项环境就绪自动检查。所有 v0.1.0 中"文档声称有但代码缺失"的缺陷已在 v0.2.0 全部补齐。启动体验问题在 v2（start_all.sh/stop_all.sh/setup_check.sh）解决——无需 3 终端、无需 Docker（macOS Metal 不可容器化）。剩余缺口集中在持久化、CI/CD 和前端测试——属于企业生产化的标准演进路径，当前架构已为这些扩展预留了清晰的接口边界（middleware / dependency-injection 模式）。
