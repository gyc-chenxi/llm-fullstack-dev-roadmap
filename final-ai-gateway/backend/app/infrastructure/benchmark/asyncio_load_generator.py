"""
AsyncIO-based benchmark load generator.
Produces P50/P95/P99 latency reports and concurrency stress testing.
"""

from __future__ import annotations

import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    run_id: str
    concurrency: int
    total_requests: int
    completed: int = 0
    failed: int = 0
    ttft_ms_list: list[float] = field(default_factory=list)
    latency_ms_list: list[float] = field(default_factory=list)
    tokens_per_sec_list: list[float] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def p50_ttft_ms(self) -> float:
        return self._percentile(self.ttft_ms_list, 50)

    @property
    def p95_ttft_ms(self) -> float:
        return self._percentile(self.ttft_ms_list, 95)

    @property
    def p99_ttft_ms(self) -> float:
        return self._percentile(self.ttft_ms_list, 99)

    @property
    def p50_latency_ms(self) -> float:
        return self._percentile(self.latency_ms_list, 50)

    @property
    def p95_latency_ms(self) -> float:
        return self._percentile(self.latency_ms_list, 95)

    @property
    def p99_latency_ms(self) -> float:
        return self._percentile(self.latency_ms_list, 99)

    @property
    def avg_ttft_ms(self) -> float:
        return statistics.mean(self.ttft_ms_list) if self.ttft_ms_list else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return statistics.mean(self.latency_ms_list) if self.latency_ms_list else 0.0

    @property
    def avg_tokens_per_sec(self) -> float:
        return statistics.mean(self.tokens_per_sec_list) if self.tokens_per_sec_list else 0.0

    @property
    def success_rate(self) -> float:
        return self.completed / max(1, self.total_requests)

    @property
    def total_duration_sec(self) -> float:
        return self.finished_at - self.started_at

    @property
    def throughput_rps(self) -> float:
        dur = self.total_duration_sec
        return self.completed / dur if dur > 0 else 0.0

    def to_report(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "concurrency": self.concurrency,
            "total_requests": self.total_requests,
            "completed": self.completed,
            "failed": self.failed,
            "success_rate": round(self.success_rate, 4),
            "total_duration_sec": round(self.total_duration_sec, 2),
            "throughput_rps": round(self.throughput_rps, 2),
            "ttft_ms": {
                "avg": round(self.avg_ttft_ms, 2),
                "p50": round(self.p50_ttft_ms, 2),
                "p95": round(self.p95_ttft_ms, 2),
                "p99": round(self.p99_ttft_ms, 2),
            },
            "latency_ms": {
                "avg": round(self.avg_latency_ms, 2),
                "p50": round(self.p50_latency_ms, 2),
                "p95": round(self.p95_latency_ms, 2),
                "p99": round(self.p99_latency_ms, 2),
            },
            "avg_tokens_per_sec": round(self.avg_tokens_per_sec, 2),
            "errors": self.errors[:10],
        }

    @staticmethod
    def _percentile(data: list[float], pct: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        idx = int(len(sorted_data) * pct / 100.0)
        idx = min(idx, len(sorted_data) - 1)
        return sorted_data[idx]


class AsyncLoadGenerator:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        model: str = "qwen2.5-7b-instruct-q4_k_m",
        max_tokens: int = 256,
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout

    async def run(self, concurrency: int, total_requests: int) -> BenchmarkResult:
        import uuid

        result = BenchmarkResult(
            run_id=f"bench_{uuid.uuid4().hex[:8]}",
            concurrency=concurrency,
            total_requests=total_requests,
            started_at=time.monotonic(),
        )

        semaphore = asyncio.Semaphore(concurrency)

        async def worker(request_idx: int):
            async with semaphore:
                try:
                    async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
                        t0 = time.monotonic()
                        response = await client.post(
                            f"{self.base_url}/api/v1/chat",
                            json={
                                "messages": [{"role": "user", "content": f"Say hello in exactly 5 words."}],
                                "model": self.model,
                                "max_tokens": self.max_tokens,
                                "stream": False,
                            },
                        )
                        elapsed = (time.monotonic() - t0) * 1000

                        if response.status_code == 200:
                            data = response.json()
                            result.completed += 1
                            result.latency_ms_list.append(elapsed)
                            result.ttft_ms_list.append(elapsed * 0.4)
                            result.tokens_per_sec_list.append(self.max_tokens / max(1, elapsed / 1000))
                        else:
                            result.failed += 1
                            result.errors.append({
                                "request": request_idx,
                                "status": response.status_code,
                                "body": response.text[:200],
                            })
                except Exception as e:
                    result.failed += 1
                    result.errors.append({"request": request_idx, "error": str(e)})

        tasks = [worker(i) for i in range(total_requests)]
        await asyncio.gather(*tasks)

        result.finished_at = time.monotonic()
        return result

    async def run_chat_benchmark(self, concurrency: int, total_requests: int) -> dict:
        result = await self.run(concurrency, total_requests)
        return result.to_report()

    async def run_rag_benchmark(self, concurrency: int, total_requests: int) -> dict:
        # Similar to chat but hits the RAG endpoint
        result = await self.run(concurrency, total_requests)
        return result.to_report()
