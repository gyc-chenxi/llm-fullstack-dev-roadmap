"""
Hybrid retriever — combines vector and BM25 retrieval with fusion.
"""

from __future__ import annotations

import logging

from app.domain.ports.retriever_port import RetrieverPort
from app.domain.value_objects.retrieval_hit import RetrievalHit
from app.infrastructure.retrieval.bm25_retriever import BM25Retriever
from app.infrastructure.retrieval.vector_store_repo import VectorStoreRepo

logger = logging.getLogger(__name__)


class HybridRetriever(RetrieverPort):
    def __init__(
        self,
        vector_store: VectorStoreRepo,
        bm25: BM25Retriever,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
    ):
        self.vector_store = vector_store
        self.bm25 = bm25
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

    async def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        vector_hits = await self.vector_store.search(query, top_k=top_k * 2)
        bm25_hits = self.bm25.search(query, top_k=top_k * 2)

        scores: dict[str, float] = {}
        contents: dict[str, RetrievalHit] = {}

        for h in vector_hits:
            key = f"{h.doc_id}:{h.chunk_index}"
            scores[key] = scores.get(key, 0) + self.vector_weight * h.score
            contents[key] = h

        max_bm25 = max((h.score for h in bm25_hits), default=1)
        for h in bm25_hits:
            key = f"{h.doc_id}:{h.chunk_index}"
            normalized_score = h.score / max_bm25 if max_bm25 > 0 else 0
            scores[key] = scores.get(key, 0) + self.bm25_weight * normalized_score
            if key not in contents:
                contents[key] = h
                contents[key].score = 0
            contents[key].retrieval_method = "hybrid"

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        hits = []
        for key, score in ranked[:top_k]:
            hit = contents[key]
            hit.score = score
            hits.append(hit)

        return hits

    async def add_documents(self, documents: list[dict]) -> None:
        pass

    async def delete_documents(self, doc_ids: list[str]) -> None:
        pass

    async def count(self) -> int:
        return await self.vector_store.count()