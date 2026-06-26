"""
Reranker — re-ranks retrieval results using rule-based or cross-encoder scoring.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.domain.value_objects.retrieval_hit import RetrievalHit

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, score_threshold: float = 0.5):
        self.score_threshold = score_threshold
        self._model = None

    async def rerank(self, query: str, hits: list[RetrievalHit], top_k: int = 3) -> list[RetrievalHit]:
        if not hits:
            return []

        reranked = []
        for hit in hits:
            new_score = self._rule_based_score(query, hit)
            hit.rerank_score = new_score
            reranked.append(hit)

        reranked.sort(key=lambda h: h.rerank_score, reverse=True)
        return [h for h in reranked[:top_k] if h.rerank_score >= self.score_threshold]

    def _rule_based_score(self, query: str, hit: RetrievalHit) -> float:
        query_terms = set(query.lower().split())
        content_lower = hit.content.lower()

        term_matches = sum(1 for t in query_terms if t in content_lower)
        term_score = term_matches / max(1, len(query_terms))

        exact_match = 1.0 if query.lower() in content_lower else 0.0

        length_penalty = min(1.0, 500 / max(1, len(hit.content)))

        return 0.5 * hit.score + 0.3 * term_score + 0.1 * exact_match + 0.1 * length_penalty