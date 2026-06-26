"""
A retrieval hit from the vector store or BM25 index.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetrievalHit:
    doc_id: str
    chunk_index: int
    content: str
    score: float
    retrieval_method: str = "vector"
    rerank_score: float = 0.0
    metadata: dict = field(default_factory=dict)