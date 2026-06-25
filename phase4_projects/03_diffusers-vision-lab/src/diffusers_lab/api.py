"""
Diffusers 推理引擎 FastAPI 服务
===============================

提供 RESTful API 包装图像生成能力，作为内层服务暴露给 Gateway 层，
或可直接被前端/测试工具调用。

架构位置：
  客户端 → [Gateway 层: gateway.py (port 8020)]
    → [引擎层: api.py (port 8010)]  ← 当前文件
      → generate_from_config() → build_pipeline() → pipe()

数据流（POST /v1/generate/txt2img）：
  客户端 JSON → Txt2ImgRequest (Pydantic 校验)
    ↓
  load_yaml(default_config) ← 加载 YAML 作为基础配置
  cfg 各字段被请求体覆盖
    ↓
  generate_from_config(cfg) ← 执行完整生成流程
    ↓
  GenerateResponse ← 返回生成元数据（输出路径、延迟等）

启动：
  python -m src.diffusers_lab.api --port 8010
"""

import argparse
import os
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from .config import load_yaml
from .generate import generate_from_config

app = FastAPI(title="Diffusers Lab Engine", version="0.1.0")


class Txt2ImgRequest(BaseModel):
    """文生图 API 请求体（最小 OpenAI 兼容子集）。"""
    prompt: str = Field(..., min_length=1)       # 正向提示词（必填）
    negative_prompt: str = ""                    # 负向提示词（可选）
    seed: int = 42                               # 随机种子（可复现）
    steps: int = 25                              # 推理步数
    guidance_scale: float = 7.5                  # CFG 引导强度
    width: int = 512                             # 输出宽度
    height: int = 512                            # 输出高度


class GenerateResponse(BaseModel):
    """生成结果响应体。"""
    ok: bool
    task: str
    seed: int
    output_path: str
    manifest_path: str
    latency_sec: Optional[float] = None
    device: Optional[str] = None
    dtype: Optional[str] = None
    image_stats: Optional[dict] = None


@app.get("/health")
def health():
    """健康检查端点（供 Gateway / k8s 探针使用）。"""
    return {"ok": True, "service": "diffusers-engine"}


@app.post("/v1/generate/txt2img", response_model=GenerateResponse)
def txt2img(req: Txt2ImgRequest):
    """
    txt2img 生成端点。

    以 YAML 配置为蓝本，用请求体字段覆盖其中的 prompt/seed 等，
    实现"默认配置 + 运行时覆盖"的灵活模式。

    参数：
      req: Txt2ImgRequest — Pydantic 校验后的请求体

    返回：
      GenerateResponse — 包含输出路径、延迟、图像统计的元数据
    """
    default_config = os.environ.get("DEFAULT_CONFIG", "configs/sd15_txt2img.yaml")
    cfg = load_yaml(default_config)

    # 请求体字段覆盖 YAML 默认值
    cfg["task"] = "txt2img"
    cfg["prompt"] = req.prompt
    cfg["negative_prompt"] = req.negative_prompt
    cfg["seed"] = req.seed
    cfg["num_inference_steps"] = req.steps
    cfg["guidance_scale"] = req.guidance_scale
    cfg["width"] = req.width
    cfg["height"] = req.height
    cfg["dtype"] = "float32"  # API 模式固定 float32 保证兼容性

    record = generate_from_config(cfg)

    return GenerateResponse(
        ok=True,
        task=record["task"],
        seed=record["seed"],
        output_path=record["output_path"],
        manifest_path=cfg.get("manifest_path", "outputs/manifests/generation_manifest.jsonl"),
        latency_sec=record.get("latency_sec"),
        device=record.get("device"),
        dtype=record.get("dtype"),
        image_stats=record.get("image_stats"),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--default-config", default="configs/sd15_txt2img.yaml")
    args = parser.parse_args()

    os.environ["DEFAULT_CONFIG"] = args.default_config

    print(f"[server] Diffusers engine listening on http://{args.host}:{args.port}")
    print(f"[server] default_config={args.default_config}")

    uvicorn.run(
        "src.diffusers_lab.api:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()