"""FastAPI 入口 — LLM Chat Service"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routes import chat, health, models
from .errors import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动/关闭时的初始化与清理"""
    import httpx
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.request_timeout),
        limits=httpx.Limits(max_keepalive_connections=20),
    )
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    title="🤖 LLM Chat Service",
    version="2.0.0",
    description="兼容 OpenAI 格式的多模型聊天 API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id", "X-Process-Time-Ms"],
)


# 请求追踪中间件
@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", uuid.uuid4().hex[:12])
    request.state.request_id = request_id
    start = time.time()

    response = await call_next(request)

    elapsed_ms = (time.time() - start) * 1000
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.0f}"
    return response


# 注册路由
app.include_router(chat.router)
app.include_router(health.router)
app.include_router(models.router)

# 注册全局异常处理器
register_exception_handlers(app)


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "LLM Chat Service", "version": "2.0.0", "docs": "/docs"}
