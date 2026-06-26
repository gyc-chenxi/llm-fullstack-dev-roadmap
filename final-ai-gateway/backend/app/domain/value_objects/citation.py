"""
A citation anchoring an answer claim to a retrieved document.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Citation:
    citation_id: str
    doc_id: str
    chunk_index: int
    excerpt: str
    relevance_score: float = 0.0
    span_start: int = 0
    span_end: int = 0
    metadata: dict = field(default_factory=dict)