from __future__ import annotations

from pydantic import BaseModel, Field


class RAGRequest(BaseModel):
    query: str = Field(..., min_length=1)
    thread_id: str = Field(..., min_length=1)
    max_retries: int = Field(default=3, ge=0, le=5)


class RAGResponse(BaseModel):
    thread_id: str
    status: str
    answer: str
    citations: list[dict] = []
    debug: dict = {}