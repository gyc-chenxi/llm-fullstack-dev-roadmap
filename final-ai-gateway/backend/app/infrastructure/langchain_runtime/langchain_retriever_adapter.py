"""
LangChain retriever adapter — wraps our HybridRetriever as a LangChain-compatible retriever.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.infrastructure.retrieval.hybrid_retriever import HybridRetriever


class LangChainRetrieverAdapter(BaseRetriever):
    hybrid_retriever: HybridRetriever
    top_k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> list[Document]:
        import asyncio

        async def _run():
            hits = await self.hybrid_retriever.search(query, top_k=self.top_k)
            return [
                Document(page_content=h.content, metadata={
                    "doc_id": h.doc_id,
                    "chunk_index": h.chunk_index,
                    "score": h.score,
                    "retrieval_method": h.retrieval_method,
                })
                for h in hits
            ]
        return asyncio.get_event_loop().run_until_complete(_run())

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> list[Document]:
        hits = await self.hybrid_retriever.search(query, top_k=self.top_k)
        return [
            Document(page_content=h.content, metadata={
                "doc_id": h.doc_id,
                "chunk_index": h.chunk_index,
                "score": h.score,
                "retrieval_method": h.retrieval_method,
            })
            for h in hits
        ]