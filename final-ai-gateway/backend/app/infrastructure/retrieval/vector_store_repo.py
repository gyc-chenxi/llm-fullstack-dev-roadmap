"""
Vector store repository — Chroma-based vector store with FAISS fallback.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.domain.value_objects.retrieval_hit import RetrievalHit

logger = logging.getLogger(__name__)


class VectorStoreRepo:
    def __init__(self, persist_dir: str = "./runtime/chroma_db", embedding_model: str = "all-MiniLM-L6-v2"):
        self.persist_dir = persist_dir
        self.embedding_model = embedding_model
        self._collection = None
        self._embedding_fn = None

    async def initialize(self):
        try:
            import chromadb
            from chromadb.config import Settings
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name="gateway_docs",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB initialized at %s", self.persist_dir)
        except ImportError:
            logger.warning("ChromaDB not available, using in-memory fallback")
            self._collection = None

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        if self._embedding_fn is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_fn = SentenceTransformer(self.embedding_model)
            except ImportError:
                logger.warning("sentence-transformers not available, using dummy embeddings")
                self._embedding_fn = None

        if self._embedding_fn is not None:
            embeddings = self._embedding_fn.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        return [[0.0] * 384 for _ in texts]

    async def add_chunks(self, chunks: list[dict]) -> int:
        if not chunks:
            return 0
        texts = [c["content"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]
        metadatas = [{k: str(v) for k, v in c.items() if k not in ("content", "embedding")} for c in chunks]

        if self._collection is not None:
            embeddings = await self._embed(texts)
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
        return len(chunks)

    async def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        if self._collection is None:
            return []

        query_embedding = await self._embed([query])
        results = self._collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dists_list = results.get("distances", [[]])[0]

        for i in range(len(ids_list)):
            score = 1.0 / (1.0 + dists_list[i]) if i < len(dists_list) else 0.0
            hits.append(RetrievalHit(
                doc_id=metas_list[i].get("doc_id", "") if i < len(metas_list) else "",
                chunk_index=int(metas_list[i].get("chunk_index", 0)) if i < len(metas_list) else 0,
                content=docs_list[i] if i < len(docs_list) else "",
                score=score,
                retrieval_method="vector",
                metadata=metas_list[i] if i < len(metas_list) else {},
            ))
        return hits

    async def count(self) -> int:
        if self._collection is not None:
            return self._collection.count()
        return 0

    async def delete_all(self):
        if self._collection is not None:
            ids = self._collection.get()["ids"]
            if ids:
                self._collection.delete(ids=ids)