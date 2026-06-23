#!/usr/bin/env python3
"""Local BGE-M3 Embedding Service (OpenAI-compatible API).

Provides a lightweight FastAPI server that exposes a /v1/embeddings endpoint
compatible with GraphRAG's embedding configuration. Uses BGE-M3 on MPS for
zero-cost, low-latency text vectorization during the index pipeline.

Usage:
    PYTHONPATH=. python src/graphrag_lab/serve_embedding.py \
        --host 127.0.0.1 --port 19530 --model BAAI/bge-m3 --device mps

Verification:
    curl -s http://127.0.0.1:19530/health | python -m json.tool
    curl -s http://127.0.0.1:19530/v1/embeddings \
        -H "Content-Type: application/json" \
        -d '{"input": ["Hello world"], "model": "bge-m3"}'
"""

import os
import sys
import argparse
import time
import logging
from contextlib import asynccontextmanager
from typing import List, Union

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[EmbeddingServer] %(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("embedding_server")

MODEL = None

# ---------------------------------------------------------------------------
# Pydantic models (OpenAI-compatible shapes)
# ---------------------------------------------------------------------------
class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "bge-m3"


class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: dict


# ---------------------------------------------------------------------------
# FastAPI lifespan — load model once at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL
    model_name = os.environ.get("EMBED_MODEL", "BAAI/bge-m3")
    device = os.environ.get("EMBED_DEVICE", "mps")

    logger.info("Loading %s on %s ...", model_name, device)
    from sentence_transformers import SentenceTransformer

    # BGE-M3 on MPS: limit batch to avoid Metal memory fragmentation
    MODEL = SentenceTransformer(model_name, device=device)
    dim = MODEL.get_sentence_embedding_dimension()
    max_len = MODEL.max_seq_length
    logger.info("Model loaded. dim=%d, max_seq_length=%d", dim, max_len)
    logger.info("Listening on http://%s:%s", os.environ.get("EMBED_HOST", "127.0.0.1"),
                os.environ.get("EMBED_PORT", "19530"))
    yield
    logger.info("Shutting down embedding service.")


app = FastAPI(title="BGE-M3 Embedding Service", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    if MODEL is None:
        return {"status": "loading", "model": "bge-m3"}
    return {
        "status": "ok",
        "model": "bge-m3",
        "dim": MODEL.get_sentence_embedding_dimension(),
        "max_seq_length": MODEL.max_seq_length,
    }


@app.get("/")
def root():
    return {"service": "BGE-M3 Embedding", "docs": "/docs", "health": "/health"}


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
def embeddings(req: EmbeddingRequest):
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    inputs = [req.input] if isinstance(req.input, str) else req.input
    if not inputs:
        raise HTTPException(status_code=400, detail="Empty input")

    # Conservative batch size for M5 32GB — prevent MPS OOM on long texts
    safe_batch = min(len(inputs), 16)

    t0 = time.time()
    embeddings_array = MODEL.encode(
        inputs,
        batch_size=safe_batch,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    elapsed = time.time() - t0

    data = [
        EmbeddingData(embedding=emb.tolist(), index=i)
        for i, emb in enumerate(embeddings_array)
    ]

    throughput = len(inputs) / elapsed if elapsed > 0 else 0
    logger.info(
        "encoded %d texts in %.2fs (%.1f texts/s, batch=%d)",
        len(inputs), elapsed, throughput, safe_batch,
    )

    return EmbeddingResponse(
        data=data,
        model=req.model,
        usage={
            "prompt_tokens": sum(len(t.split()) for t in inputs),
            "total_tokens": sum(len(t.split()) for t in inputs),
        },
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="BGE-M3 Local Embedding Service (OpenAI-compatible)"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=19530, help="Bind port")
    parser.add_argument("--model", default="BAAI/bge-m3", help="HF model name")
    parser.add_argument("--device", default="mps",
                        choices=["mps", "cpu", "cuda"], help="Torch device")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev)")
    args = parser.parse_args()

    os.environ["EMBED_MODEL"] = args.model
    os.environ["EMBED_DEVICE"] = args.device
    os.environ["EMBED_HOST"] = args.host
    os.environ["EMBED_PORT"] = str(args.port)

    uvicorn.run(
        "src.graphrag_lab.serve_embedding:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
