"""
RAG Runtime port — abstract interface for the LangChain RAG execution runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from ..value_objects.citation import Citation
from ..value_objects.retrieval_hit import RetrievalHit


class RagRuntimePort(ABC):
    @abstractmethod
    async def retrieve(self, query: str, top_k: int) -> list[RetrievalHit]:
        ...

    @abstractmethod
    async def rerank(self, query: str, hits: list[RetrievalHit], top_k: int) -> list[RetrievalHit]:
        ...

    @abstractmethod
    async def generate(
        self, query: str, hits: list[RetrievalHit], stream: bool = True
    ) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    async def extract_citations(self, answer: str, hits: list[RetrievalHit]) -> list[Citation]:
        ...
