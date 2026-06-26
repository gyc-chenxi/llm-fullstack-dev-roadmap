"""
A RAG query request, representing retrieval-augmented generation workloads.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RagRequest:
    request_id: str = field(default_factory=lambda: f"rag_{uuid.uuid4().hex[:12]}")
    tenant_id: str = "default"
    question: str = ""
    knowledge_base_id: str = "default"
    retrieval_top_k: int = 5
    rerank_top_k: int = 3
    required_citations: bool = True
    stream: bool = True
    max_answer_tokens: int = 1024
    priority: int = 5
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    status: str = "created"
    retrieval_result_ids: list[str] = field(default_factory=list)
    trace_id: Optional[str] = None

    def __post_init__(self):
        if not self.question.strip():
            raise ValueError("question must not be empty")
