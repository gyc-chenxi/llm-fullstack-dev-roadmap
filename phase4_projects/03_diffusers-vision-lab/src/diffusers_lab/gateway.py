"""
Diffusers Gateway 代理层
========================

对外暴露的 API 网关，将请求转发到内层 Diffusers 推理引擎。
与 02_llama_cpp 的 Gateway 模式类似，但职责更轻：
  1. 路由转发：接收外部请求，转发给引擎层 (api.py, port 8010)
  2. 不自行管理模型生命周期（完全委托给引擎层）
  3. 无认证/限流（可由外部 API Gateway 统一管理）

架构分层：
  外部客户端 → [Gateway (port 8020)] → [Engine (port 8010)]
                                         ↓
                                     (GPU) Diffusers pipeline

数据流（POST /v1/generate/txt2img）：
  客户端 JSON → Txt2ImgRequest (Pydantic)
    ↓
  httpx.POST(engine_url/v1/generate/txt2img) ← 转发到引擎层
    ↓
  引擎返回的 JSON 响应 ← 直接透传回客户端

启动：
  python -m src.diffusers_lab.gateway --port 8020 --engine-url http://127.0.0.1:8010
"""

import argparse
import os

import httpx
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Diffusers Lab Gateway", version="0.1.0")


class Txt2ImgRequest(BaseModel):
    """文生图请求体（与引擎层完全对齐）。"""
    prompt: str = Field(..., min_length=1)
    negative_prompt: str = ""
    seed: int = 42
    steps: int = 25
    guidance_scale: float = 7.5
    width: int = 512
    height: int = 512


@app.get("/health")
def health():
    """健康检查：返回自身状态及上游引擎地址。"""
    return {
        "ok": True,
        "service": "diffusers-gateway",
        "engine_url": os.environ.get("ENGINE_URL", "http://127.0.0.1:8010"),
    }


@app.post("/v1/generate/txt2img")
def txt2img(req: Txt2ImgRequest):
    """
    将 txt2img 请求转发到引擎层。

    不执行任何生成逻辑，纯代理转发。引擎不可用时抛 502。

    参数：
      req: Txt2ImgRequest — Pydantic 校验后的请求体

    返回：
      引擎返回的完整 JSON 响应（透传）
    """
    engine_url = os.environ.get("ENGINE_URL", "http://127.0.0.1:8010")

    # httpx.Client(timeout=None): 推理可能持续数十秒，不设超时
    with httpx.Client(timeout=None) as client:
        r = client.post(
            f"{engine_url}/v1/generate/txt2img",
            json=req.model_dump(),
        )
        r.raise_for_status()
        return r.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8020)
    parser.add_argument("--engine-url", default="http://127.0.0.1:8010")
    args = parser.parse_args()

    os.environ["ENGINE_URL"] = args.engine_url

    print(f"[gateway] upstream engine={args.engine_url}")
    print(f"[gateway] listening on http://{args.host}:{args.port}")

    uvicorn.run(
        "src.diffusers_lab.gateway:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()