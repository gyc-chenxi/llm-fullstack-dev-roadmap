from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI

from vlm_p5.qwen_engine import QwenVLEngine
from vlm_p5.schemas import VisionRequest, VisionResponse

MODEL_PATH = os.getenv("MODEL_PATH", "models/Qwen2.5-VL-3B-Instruct")
MODEL_BACKEND = os.getenv("MODEL_BACKEND", "qwen2_5_vl")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
MAX_PIXELS = int(os.getenv("MAX_PIXELS", "786432"))

app = FastAPI(title="P5 Qwen-VL Engine", version="0.1.0")

engine: QwenVLEngine | None = None


@app.on_event("startup")
def startup() -> None:
    global engine
    engine = QwenVLEngine(
        model_path=MODEL_PATH,
        backend=MODEL_BACKEND,
        max_new_tokens=MAX_NEW_TOKENS,
        max_pixels=MAX_PIXELS,
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_path": MODEL_PATH,
        "backend": MODEL_BACKEND,
    }


@app.post("/generate", response_model=VisionResponse)
def generate(req: VisionRequest) -> VisionResponse:
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