"""
Pydantic API Schemas
======================

API 层数据模型 — RAG 请求/响应的类型约束。

RAGRequest:
  - query: 用户问题（min_length=1）
  - thread_id: 对话线程 ID（用于 checkpoint 隔离）
  - max_retries: 检索和生成的各自最大重试次数（0-5，默认 3）

RAGResponse:
  - status: ok / fallback / failed
  - citations: [{label, doc_id, source, title, quote}]
  - debug: 全流程中间状态（query_type, scores, retries, errors, events）
"""

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
