"""
BGE-M3 本地 Embedding 服务
=============================

提供 OpenAI-compatible /v1/embeddings 端点的 FastAPI 微服务。

为什么需要这个服务：
  GraphRAG 的索引管线需要大量调用 embedding API（每个 chunk 一次）。
  - 使用远程 API (OpenAI/DeepSeek) → 海量 tokens 成本 + 网络延迟
  - 使用本地 BGE-M3 → 免费 + 低延迟 + 无 token 限制

GraphRAG 配置集成：
  在 settings.yaml 中设置 embedding 端点为 http://127.0.0.1:19530/v1，
  GraphRAG 索引时会自动调用本地 BGE-M3 服务，替代收费 API。

数据流：
  POST /v1/embeddings {"input": ["text1", "text2"], "model": "bge-m3"}
    → MODEL.encode(inputs, batch_size=16, normalize_embeddings=True)
    → [{embedding: [1024] float, index: i}] → EmbeddingResponse

性能参数：
  - BGE-M3: 1024 维 dense vector, max_seq_length=8192
  - batch_size=16: MPS 上的安全批大小（32GB 统一内存）
  - normalize_embeddings=True: 输出 L2 归一化向量（适合 cosine 相似度）

用法：
  PYTHONPATH=. python src/graphrag_lab/serve_embedding.py --host 127.0.0.1 --port 19530
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

logging.basicConfig(
    level=logging.INFO,
    format="[EmbeddingServer] %(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("embedding_server")

MODEL = None


# OpenAI-compatible Pydantic schemas
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时加载 BGE-M3 到指定设备（MPS/cpu/cuda）。"""
    global MODEL
    model_name = os.environ.get("EMBED_MODEL", "BAAI/bge-m3")
    device = os.environ.get("EMBED_DEVICE", "mps")

    logger.info("Loading %s on %s ...", model_name, device)
    from sentence_transformers import SentenceTransformer

    MODEL = SentenceTransformer(model_name, device=device)
    dim = MODEL.get_sentence_embedding_dimension()
    max_len = MODEL.max_seq_length
    logger.info("Model loaded. dim=%d, max_seq_length=%d", dim, max_len)
    logger.info("Listening on http://%s:%s", os.environ.get("EMBED_HOST", "127.0.0.1"),
                os.environ.get("EMBED_PORT", "19530"))
    yield
    logger.info("Shutting down embedding service.")


app = FastAPI(title="BGE-M3 Embedding Service", version="1.0.0", lifespan=lifespan)


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
    """OpenAI-compatible embedding 端点。

    数据流：texts → BGE-M3.encode(batch=16, normalize=True)
      → [{1024-dim vector}] → EmbeddingResponse
    """
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    inputs = [req.input] if isinstance(req.input, str) else req.input
    if not inputs:
        raise HTTPException(status_code=400, detail="Empty input")

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
