"""
LangChain RAG Runtime — implements the RagRuntimePort with full retrieval pipeline.
retrieve → rerank → generate → extract citations
"""

from __future__ import annotations

import logging
import time
from typing import AsyncIterator

from app.domain.ports.rag_runtime_port import RagRuntimePort
from app.domain.value_objects.citation import Citation
from app.domain.value_objects.retrieval_hit import RetrievalHit
from app.infrastructure.retrieval.hybrid_retriever import HybridRetriever
from app.infrastructure.retrieval.reranker import Reranker
from app.infrastructure.llm_clients.gateway_chat_model import GatewayChatModel

logger = logging.getLogger(__name__)


class LangChainRagRuntime(RagRuntimePort):
    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: Reranker,
        gateway_model: GatewayChatModel,
        default_top_k: int = 5,
        rerank_top_k: int = 3,
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.gateway_model = gateway_model
        self.default_top_k = default_top_k
        self.rerank_top_k = rerank_top_k

    async def retrieve(self, query: str, top_k: int = 0) -> list[RetrievalHit]:
        k = top_k or self.default_top_k
        t0 = time.monotonic()
        hits = await self.retriever.search(query, top_k=k)
        elapsed = (time.monotonic() - t0) * 1000
        logger.info("Retrieved %d hits in %.1fms", len(hits), elapsed)
        return hits

    async def rerank(self, query: str, hits: list[RetrievalHit], top_k: int = 0) -> list[RetrievalHit]:
        k = top_k or self.rerank_top_k
        t0 = time.monotonic()
        reranked = await self.reranker.rerank(query, hits, top_k=k)
        elapsed = (time.monotonic() - t0) * 1000
        logger.info("Reranked %d → %d hits in %.1fms", len(hits), len(reranked), elapsed)
        return reranked

    async def generate(
        self, query: str, hits: list[RetrievalHit], stream: bool = True
    ) -> AsyncIterator[dict]:
        context_parts = []
        for i, hit in enumerate(hits):
            context_parts.append(f"[Source {i+1}] (score: {hit.rerank_score:.2f})\n{hit.content}")

        context = "\n\n---\n\n".join(context_parts)
        system_prompt = (
            "You are a precise RAG assistant. Answer the user's question based ONLY on the provided context. "
            "If the context doesn't contain sufficient information, say so. "
            "Always cite the source number [Source N] when referencing specific information."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ]

        full_text = ""
        async for gen in self.gateway_model._astream(messages):
            from langchain_core.messages import AIMessage

            if isinstance(gen, AIMessage):
                token = gen.content
            elif hasattr(gen, 'message'):
                token = gen.message.content
            else:
                token = str(gen)

            full_text += token
            yield {
                "type": "token",
                "content": token,
            }

        yield {
            "type": "done",
            "full_text": full_text,
            "context_used": len(hits),
        }

    async def extract_citations(self, answer: str, hits: list[RetrievalHit]) -> list[Citation]:
        citations = []
        import re

        for i, hit in enumerate(hits):
            source_ref = f"[Source {i+1}]"
            if source_ref in answer:
                citations.append(Citation(
                    citation_id=f"cite_{i}",
                    doc_id=hit.doc_id,
                    chunk_index=hit.chunk_index,
                    excerpt=hit.content[:200],
                    relevance_score=hit.rerank_score,
                ))

        return citations

    async def query(
        self, question: str, top_k: int = 0, stream: bool = True
    ) -> AsyncIterator[dict]:
        t0 = time.monotonic()
        yield {"type": "retrieval_start", "question": question}

        hits = await self.retrieve(question, top_k=top_k)
        yield {
            "type": "retrieval_result",
            "count": len(hits),
            "hits": [{"doc_id": h.doc_id, "score": round(h.score, 4)} for h in hits],
        }

        reranked = await self.rerank(question, hits)
        yield {
            "type": "rerank_result",
            "count": len(reranked),
            "hits": [{"doc_id": h.doc_id, "rerank_score": round(h.rerank_score, 4)} for h in reranked],
        }

        async for event in self.generate(question, reranked, stream=stream):
            yield event

        total_elapsed = (time.monotonic() - t0) * 1000
        yield {"type": "rag_done", "total_latency_ms": round(total_elapsed, 2)}