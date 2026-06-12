"""
SAM 2 Vision API — FastAPI 服务入口
-----------------------------------
使用 lifespan 事件管理模型生命周期，路由定义拆分到 routes.py。
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

from sam2_lab.api.routes import router, set_predictor

# ── 全局状态 ──────────────────────────────────────────────

_predictor: SAM2ImagePredictor | None = None
_device: str = "mps" if torch.backends.mps.is_available() else "cpu"


# ── 生命周期 ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的模型加载与清理。"""
    global _predictor

    # 启动时加载模型
    print(f"[server] Loading SAM2 model on {_device} ...")
    checkpoint = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
    model = build_sam2(model_cfg, checkpoint, device=_device)
    _predictor = SAM2ImagePredictor(model)
    set_predictor(_predictor, _device)
    print(f"[server] SAM2 loaded: {checkpoint} on {_device}")

    yield  # 服务运行期间

    # 关闭时清理
    print("[server] Shutting down ...")
    _predictor = None


# ── App 创建 ──────────────────────────────────────────────

app = FastAPI(
    title="SAM 2 Vision API",
    description="基于 Meta SAM 2.1 的图像分割 RESTful API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 允许本地 Gradio UI 跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)
