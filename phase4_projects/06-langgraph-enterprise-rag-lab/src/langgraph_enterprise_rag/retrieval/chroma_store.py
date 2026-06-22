from __future__ import annotations

import os
from dataclasses import dataclass

import chromadb

from langgraph_enterprise_rag.retrieval.embeddings import build_embedding_model


@dataclass
class ChromaStore:
    chroma_dir: str
    collection_name: str = "enterprise_rag_docs"

    def __post_init__(self) -> None:
        self.client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )
        self.embedder = build_embedding_model()

    def count(self) -> int:
        return self.collection.count()

    def all_docs(self, limit: int = 100_000) -> list[dict]:
        result = self.collection.get(
            limit=limit,
            include=["documents", "metadatas"],
        )

        docs: list[dict] = []

        ids = result.get("ids") or []
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []

        for idx, doc_id in enumerate(ids):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            content = documents[idx] if idx < len(documents) else ""

            docs.append(
                {
                    "doc_id": doc_id,
                    "content": content,
                    "source": metadata.get("source", ""),
                    "title": metadata.get("title", ""),
                    "metadata": metadata,
                }
            )

        return docs

    def dense_search(self, query: str, top_k: int = 8) -> list[dict]:
        if self.count() == 0:
            return []

        query_embedding = self.embedder.encode([query])[0]

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        docs: list[dict] = []

        for i, doc_id in enumerate(ids):
            distance = float(distances[i]) if i < len(distances) else 999.0
            dense_score = 1.0 / (1.0 + max(distance, 0.0))
            metadata = metadatas[i] if i < len(metadatas) else {}

            docs.append(
                {
                    "doc_id": doc_id,
                    "content": documents[i] if i < len(documents) else "",
                    "source": metadata.get("source", ""),
                    "title": metadata.get("title", ""),
                    "metadata": metadata,
                    "dense_score": dense_score,
                }
            )

        return docs


def build_chroma_store() -> ChromaStore:
    return ChromaStore(
        chroma_dir=os.getenv("CHROMA_DIR", "data/chroma"),
        collection_name=os.getenv("CHROMA_COLLECTION", "enterprise_rag_docs"),
    )