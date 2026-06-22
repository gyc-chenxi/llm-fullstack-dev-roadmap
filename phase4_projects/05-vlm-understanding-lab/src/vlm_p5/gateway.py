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
    return {"status": "ok", "service": "gateway"}


@app.post("/v1/vision/chat")
async def vision_chat(
    image: UploadFile = File(...),
    question: str = Form(...),
) -> dict:
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