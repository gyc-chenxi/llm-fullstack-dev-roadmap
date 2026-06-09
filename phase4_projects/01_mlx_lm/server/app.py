"""
MLX 本地大模型聊天服务 — FastAPI 应用入口
===========================================
启动方式:
    cd server
    python app.py

    # 或使用 uvicorn
    uvicorn app:app --host 0.0.0.0 --port 8001 --reload
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

    启动时:
      1. 加载 MLX 模型 + LoRA 适配器（挂载到 app.state.engine）
      2. 创建数据库表（如果不存在）

    关闭时:
      暂时无需额外清理。
    """
    # === 启动阶段 ===
    print("[Lifespan] Creating database tables...")
    create_db_and_tables()

    print("[Lifespan] Loading LLM engine...")
    app.state.engine = LLMEngine(
        model_path=MODEL_PATH,
        adapter_path=ADAPTER_PATH,
    )
    # 将数据库引擎也挂上去，供 chat 路由持久化时使用
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

# CORS 配置（开发阶段开放所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(chat_router)
app.include_router(sessions_router)


# ---------------------------------------------------------------------------
# 健康检查
# ---------------------------------------------------------------------------

@app.get("/health")
async def health(request: Request):
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
