"""
Benchmark config DTO.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BenchmarkConfigDTO(BaseModel):
    concurrency: int = Field(default=10, ge=1, le=100)
    total_requests: int = Field(default=50, ge=1, le=1000)
    model: str = "qwen2.5-7b-instruct-q4_k_m"
    max_tokens: int = 256