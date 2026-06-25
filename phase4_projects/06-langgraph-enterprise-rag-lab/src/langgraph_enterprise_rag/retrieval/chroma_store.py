"""
ChromaDB 向量存储
===================

基于 ChromaDB PersistentClient 的向量数据库封装。

数据流：
  Ingestion: text → SentenceTransformer(BGE-M3) → [dim=1024] embedding
             → ChromaDB.upsert(documents, embeddings, metadatas)
  Query:     query → BGE-M3.encode → [dim=1024] query_embedding
             → ChromaDB.query(embedding, top_k) → distances
             → dense_score = 1/(1+distance) (Cosine 距离转相似度)

ChromaDB 距离度量：
  - 默认使用 L2 distance
  - dense_score = 1/(1+distance) 转换为 0-1 相似度
  - distance=0 → dense_score=1.0（完全匹配）
  - distance=∞ → dense_score≈0（无关联）
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import chromadb

from langgraph_enterprise_rag.retrieval.embeddings import build_embedding_model


@dataclass
class ChromaStore:
    """ChromaDB 持久化向量存储。

    特性：
      - PersistentClient 确保数据在进程重启后保留
      - get_or_create_collection 确保多次启动不会创建重复集合
      - dense_score = 1/(1+distance) 将 L2 距离转换为相似度
    """

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
        """获取集合中所有文档（用于 BM25 延迟初始化）。"""
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
        """Dense 向量检索（BGE-M3 编码 + ChromaDB 最近邻搜索）。"""
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
    """从环境变量构建 ChromaStore 实例。"""
    return ChromaStore(
        chroma_dir=os.getenv("CHROMA_DIR", "data/chroma"),
        collection_name=os.getenv("CHROMA_COLLECTION", "enterprise_rag_docs"),
    )
