"""
Benchmark Routes — POST /api/v1/benchmark/run, GET status
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from app.application.dto.benchmark_config_dto import BenchmarkConfigDTO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/benchmark", tags=["benchmark"])


@router.post("/run")
async def run_benchmark(body: BenchmarkConfigDTO, request: Request):
    """Run a benchmark with specified concurrency and request count."""
    from app.infrastructure.benchmark.asyncio_load_generator import AsyncLoadGenerator

    generator = AsyncLoadGenerator(
        base_url=f"http://{request.url.hostname}:{request.url.port or 8000}",
        model=body.model,
        max_tokens=body.max_tokens,
    )
    report = await generator.run_chat_benchmark(body.concurrency, body.total_requests)
    return report


@router.get("/history")
async def benchmark_history():
    """List past benchmark runs."""
    return {"runs": [], "note": "Benchmark history stored in Redis trace repo"}
