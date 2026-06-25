"""
P5 VLM Gateway — FastAPI 网关服务
==================================

架构角色：前端接入层，运行在端口 8000，负责：
  1. 接收客户端 multipart/form-data 上传（图片文件 + 问题文本）
  2. 将上传图片暂存到 tmp/uploads/{uuid}.ext 供 Engine 本地读取
  3. 构造 JSON payload 转发到 Engine 服务 (port 8001)
  4. 透传 Engine 的 VisionResponse 给客户端

数据流：
  Client (multipart/form-data)
    │  image: UploadFile(bytes) ──→ 保存到 tmp/uploads/{uuid}.{ext}
    │  question: Form str ──→ 构造 JSON
    │
    └── POST /v1/vision/chat
         │
         payload = { image_path: str, question: str, system_prompt?: str }
         │
         └── httpx.AsyncClient(timeout=300s) → POST 127.0.0.1:8001/generate
              │
              └── VisionResponse JSON ← 透传给客户端

为什么 300s 超时：VLM 单次推理在 MPS 上可能耗时 30-120s，留足裕量。
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI(title="P5 VLM Gateway", version="0.1.0")

TMP_DIR = Path("tmp/uploads")
TMP_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_URL = "http://127.0.0.1:8001/generate"


@app.get("/health")
def health() -> dict:
    """网关健康检查，不依赖 Engine 状态。"""
    return {"status": "ok", "service": "gateway"}


@app.post("/v1/vision/chat")
async def vision_chat(
    image: UploadFile = File(...),
    question: str = Form(...),
) -> dict:
    """VLM 视觉问答端点。

    数据流：
      image (UploadFile bytes) → 保存到 tmp/uploads/{uuid}.{ext}
      question (Form str) → 与 image_path 拼成 JSON payload
      → httpx POST 127.0.0.1:8001/generate
      → 透传 Engine 的 JSON 响应
    """
    suffix = Path(image.filename or "image.png").suffix or ".png"
    image_path = TMP_DIR / f"{uuid.uuid4().hex}{suffix}"

    with image_path.open("wb") as f:
        shutil.copyfileobj(image.file, f)

    payload = {
        "image_path": str(image_path),
        "question": question,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(ENGINE_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    uvicorn.run(
        "vlm_p5.gateway:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )