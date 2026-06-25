"""
FastAPI Application Factory — llama.cpp AI Gateway
====================================================

Gateway 架构：将 llama-server 包装为企业级 API 网关，提供认证、限流、可观测性。

中间件栈（注册顺序 = 执行顺序，outer 最先执行）：
  1. TimingMiddleware       ← 最外层，包裹全链路计时
  2. RequestIdMiddleware    ← 请求追踪 ID 注入/透传
  3. RateLimitMiddleware    ← 每 IP 滑动窗口限流
  4. ApiKeyMiddleware       ← API Key 认证
  5. CORSMiddleware         ← 浏览器跨域预检（最靠近路由）

完整数据流：
  ┌─ HTTP Request ──────────────────────────────────────────────────────────┐
  │  Method: POST /v1/chat/completions                                       │
  │  Headers: {Content-Type, X-API-Key, X-Request-Id}                       │
  │  Body: {"model":..., "messages":[...], "temperature":0.2, "stream":bool}│
  └───────────┬─────────────────────────────────────────────────────────────┘
              ↓
  [TimingMiddleware]     → 记录 t0 = time.perf_counter()  ← 全链路计时起点
  [RequestIdMiddleware]  → 注入/透传 X-Request-Id
  [RateLimitMiddleware]  → IP 滑动窗口检查（429 或放行）
  [ApiKeyMiddleware]     → X-API-Key 校验（401/403 或放行）
  [CORSMiddleware]       → CORS 预检处理（OPTIONS 请求拦截）
              ↓
  ┌─ Route Handler ─────────────────────────────────────────────────────────┐
  │  routes_chat.chat_completions()                                          │
  │    1. req.to_upstream_payload(default_model)  ← Gateway→上游格式转换    │
  │    2a. [非流式] client.chat_completion(payload) → 等待完整响应 + 注入延迟│
  │    2b. [流式]   client.stream_chat_completion(payload) → SSE 透传        │
  └──────────────────────────────────────────────────────────────────────────┘
              ↓
  ┌─ LlamaCppClient ────────────────────────────────────────────────────────┐
  │  httpx.AsyncClient POST /v1/chat/completions                             │
  │    → llama-server (上游) → 模型推理 → 响应返回                           │
  └──────────────────────────────────────────────────────────────────────────┘
              ↓
  [中间件栈倒序返回] → HTTP Response
    Headers: {X-Request-Id, X-Process-Time-Ms, Cache-Control}
    Body: OpenAI-compatible JSON / SSE event stream

启动方式：
  cd gateway && python app.py
  # 或 uvicorn app:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from gateway.config import settings
from gateway.errors import (
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from gateway.llamacpp_client import LlamaCppClient
from gateway.middleware import (
    TimingMiddleware,
    RequestIdMiddleware,
    RateLimitMiddleware,
)
from gateway.auth import ApiKeyMiddleware
from gateway.routes_chat import router as chat_router
from gateway.routes_health import router as health_router
from gateway.routes_metrics import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理。
    启动时创建 httpx 连接池（跨请求复用），关闭时释放。
    """
    app.state.llamacpp = LlamaCppClient()
    yield
    await app.state.llamacpp.close()


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    lifespan=lifespan,
    description="Local AI Gateway — OpenAI-compatible proxy to llama.cpp with rate limiting, API key auth, and observability.",
)

# ── 异常处理器（优先于中间件注册） ──
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── 中间件（outermost 先注册，按 1→2→3→4→5 执行） ──
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ApiKeyMiddleware)

# CORS 最后注册（离 route 最近），确保预检 OPTIONS 请求最先被处理
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由 ──
app.include_router(health_router)    # /healthz, /readyz
app.include_router(metrics_router)   # /gateway/metrics
app.include_router(chat_router)      # /v1/chat/completions


# ── 直接运行入口 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
