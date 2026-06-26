"""
Retriever port — abstract interface for document retrieval backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..value_objects.retrieval_hit import RetrievalHit


class RetrieverPort(ABC):
    @abstractmethod
    async def search(self, query: str, top_k: int) -> list[RetrievalHit]:
        ...

    @abstractmethod
    async def add_documents(self, documents: list[dict]) -> None:
        ...

    @abstractmethod
    async def delete_documents(self, doc_ids: list[str]) -> None:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...
