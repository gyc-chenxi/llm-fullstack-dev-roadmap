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
    prompt: str = Field(..., min_length=1)
    negative_prompt: str = ""
    seed: int = 42
    steps: int = 25
    guidance_scale: float = 7.5
    width: int = 512
    height: int = 512

class GenerateResponse(BaseModel):
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
    return {"ok": True, "service": "diffusers-engine"}

@app.post("/v1/generate/txt2img", response_model=GenerateResponse)
def txt2img(req: Txt2ImgRequest):
    default_config = os.environ.get("DEFAULT_CONFIG", "configs/sd15_txt2img.yaml")
    cfg = load_yaml(default_config)

    cfg["task"] = "txt2img"
    cfg["prompt"] = req.prompt
    cfg["negative_prompt"] = req.negative_prompt
    cfg["seed"] = req.seed
    cfg["num_inference_steps"] = req.steps
    cfg["guidance_scale"] = req.guidance_scale
    cfg["width"] = req.width
    cfg["height"] = req.height
    cfg["dtype"] = "float32"

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
