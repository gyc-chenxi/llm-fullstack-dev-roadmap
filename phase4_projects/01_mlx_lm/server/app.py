"""
MLX 本地大模型聊天服务 — FastAPI 应用入口
===========================================
基于 Apple MLX 框架的本地大模型推理 API 服务，前后端分离架构。

启动方式:
    cd server && python app.py          # 直接启动（推荐）
    uvicorn app:app --host 0.0.0.0 --port 8001 --reload   # 开发热重载

完整数据流（用户请求 → 返回响应）：
  前端 Vue App
    ↓ HTTP POST /v1/chat/completions (SSE)
  FastAPI → schemas.ChatRequest (Pydantic 校验)
    ↓
  LLMEngine.chat(messages)
    ├── truncate_messages()       ← 滑动窗口截断（防止 prompt 超长）
    ├── build_prompt()            ← chat_template 拼接为单字符串
    └── stream_generate()         ← MLX 逐 token 推理，yield delta
    ↓
  EventSourceResponse             ← SSE 流式推送（OpenAI 兼容格式）
    ↓
  _persist_messages()             ← 流结束后写入 SQLite（ChatSession + Message）
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import MODEL_PATH, ADAPTER_PATH, HOST, PORT
from database import create_db_and_tables, engine
from llm import LLMEngine
from routes.chat import router as chat_router
from routes.sessions import router as sessions_router


# ---------------------------------------------------------------------------
# 应用生命周期管理
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动/关闭时的资源管理。

    启动时 (yield 前)：
      1. 初始化 SQLite 数据库表（如不存在则创建）
      2. 加载 MLX 模型 + LoRA 适配器，挂载到 app.state.engine

    运行时 (yield 期间)：
      FastAPI 正常处理请求，routes 通过 request.app.state.engine 访问引擎

    关闭时 (yield 后)：
      暂无需清理；MLX 统一内存由系统管理
    """
    # === 启动阶段 ===
    print("[Lifespan] Creating database tables...")
    create_db_and_tables()

    print("[Lifespan] Loading LLM engine...")
    # LLMEngine 构造函数会调用 mlx_lm.load()，将模型权重加载到统一内存
    # 首次加载较慢（数秒到数分钟），取决于模型大小
    app.state.engine = LLMEngine(
        model_path=MODEL_PATH,
        adapter_path=ADAPTER_PATH,
    )
    # 将数据库引擎挂接到 LLMEngine，方便 chat 路由持久化时获取
    app.state.engine.db_engine = engine

    print(f"[Lifespan] Server ready at http://{HOST}:{PORT}")
    print("[Lifespan] API docs at http://localhost:{}/docs".format(PORT))

    yield

    # === 关闭阶段 ===
    print("[Lifespan] Shutting down...")


# ---------------------------------------------------------------------------
# FastAPI 应用实例
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MLX Local LLM Chat",
    description="基于 Apple MLX 的本地大模型聊天服务",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS 配置（开发阶段开放所有来源，生产环境应限制具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(chat_router)        # /v1/chat/completions（SSE 流式）
app.include_router(sessions_router)    # /api/sessions/*（会话 CRUD）


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------

@app.get("/health")
async def health(request: Request):
    """简单的健康检查端点，返回模型加载状态和路径信息。"""
    return {
        "status": "ok",
        "model_path": MODEL_PATH,
        "adapter_path": ADAPTER_PATH,
    }


# ---------------------------------------------------------------------------
# 直接运行入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)
