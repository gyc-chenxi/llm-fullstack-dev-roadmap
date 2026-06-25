"""
P5 Qwen-VL Engine — 模型推理微服务
====================================

运行在端口 8001，负责加载 Qwen-VL 模型并提供 /generate 推理端点。

生命周期：
  startup → QwenVLEngine(full GPU load) → 常驻内存 → 等待 Gateway 请求

环境变量配置（可在 Makefile 或命令行中覆盖）：
  MODEL_PATH:    模型本地目录（默认 models/Qwen2.5-VL-3B-Instruct）
  MODEL_BACKEND: 模型类选择 "qwen2_5_vl" 或 "qwen2_vl"
  MAX_NEW_TOKENS: 最大生成 token 数，默认 512
  MAX_PIXELS:     图片最大像素数，控制 VLM 输入图片分辨率上限

与 Gateway 的契约：
  Gateway POST /generate ← VisionRequest JSON
  Gateway ← VisionResponse JSON
"""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI

from vlm_p5.qwen_engine import QwenVLEngine
from vlm_p5.schemas import VisionRequest, VisionResponse

# 环境变量覆盖默认配置（Makefile run-engine 目标中设置）
MODEL_PATH = os.getenv("MODEL_PATH", "models/Qwen2.5-VL-3B-Instruct")
MODEL_BACKEND = os.getenv("MODEL_BACKEND", "qwen2_5_vl")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
MAX_PIXELS = int(os.getenv("MAX_PIXELS", "786432"))

app = FastAPI(title="P5 Qwen-VL Engine", version="0.1.0")

engine: QwenVLEngine | None = None


@app.on_event("startup")
def startup() -> None:
    """服务启动时加载模型到 GPU/MPS，后续请求复用同一实例。"""
    global engine
    engine = QwenVLEngine(
        model_path=MODEL_PATH,
        backend=MODEL_BACKEND,
        max_new_tokens=MAX_NEW_TOKENS,
        max_pixels=MAX_PIXELS,
    )


@app.get("/health")
def health() -> dict:
    """Engine 健康检查，返回当前加载的模型路径和后端类型。"""
    return {
        "status": "ok",
        "model_path": MODEL_PATH,
        "backend": MODEL_BACKEND,
    }


@app.post("/generate", response_model=VisionResponse)
def generate(req: VisionRequest) -> VisionResponse:
    """执行 VLM 推理并将结果结构化返回。

    数据流：VisionRequest → engine.ask() → VisionResponse
    """
    assert engine is not None
    answer = engine.ask(
        image_path=req.image_path,
        question=req.question,
        system_prompt=req.system_prompt,
    )
    return VisionResponse(
        answer=answer,
        model=MODEL_PATH,
        device=engine.device,
    )


if __name__ == "__main__":
    uvicorn.run(
        "scripts.serve_qwen_vl:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )
