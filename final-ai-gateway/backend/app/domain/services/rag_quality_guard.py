"""
RAG quality guard — validates retrieval quality and citation accuracy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..value_objects.citation import Citation
from ..value_objects.retrieval_hit import RetrievalHit


@dataclass
class RagQualityGuard:
    min_retrieval_score: float = 0.3
    min_rerank_score: float = 0.5
    require_citations: bool = True

    def check_retrieval_quality(self, hits: list[RetrievalHit]) -> tuple[bool, str]:
        if not hits:
            return False, "no retrieval results"
        avg_score = sum(h.score for h in hits) / len(hits)
        if avg_score < self.min_retrieval_score:
            return False, f"low retrieval score: {avg_score:.3f} < {self.min_retrieval_score}"
        return True, "ok"

    def check_rerank_quality(self, hits: list[RetrievalHit]) -> tuple[bool, str]:
        reranked = [h for h in hits if h.rerank_score > 0]
        if not reranked:
            return True, "no rerank scores available"
        avg_rerank = sum(h.rerank_score for h in reranked) / len(reranked)
        if avg_rerank < self.min_rerank_score:
            return False, f"low rerank score: {avg_rerank:.3f} < {self.min_rerank_score}"
        return True, "ok"

    def check_citations(self, citations: list[Citation], hits: list[RetrievalHit]) -> tuple[bool, str]:
        if self.require_citations and not citations:
            return False, "no citations provided"
        hit_doc_ids = {h.doc_id for h in hits}
        for c in citations:
            if c.doc_id not in hit_doc_ids:
                return False, f"citation {c.citation_id} references doc {c.doc_id} not in retrieved docs"
        return True, "ok"