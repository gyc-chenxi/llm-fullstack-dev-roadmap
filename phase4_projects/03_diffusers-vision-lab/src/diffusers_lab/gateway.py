import argparse
import os

import httpx
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Diffusers Lab Gateway", version="0.1.0")

class Txt2ImgRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    negative_prompt: str = ""
    seed: int = 42
    steps: int = 25
    guidance_scale: float = 7.5
    width: int = 512
    height: int = 512

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "diffusers-gateway",
        "engine_url": os.environ.get("ENGINE_URL", "http://127.0.0.1:8010"),
    }

@app.post("/v1/generate/txt2img")
def txt2img(req: Txt2ImgRequest):
    engine_url = os.environ.get("ENGINE_URL", "http://127.0.0.1:8010")

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
