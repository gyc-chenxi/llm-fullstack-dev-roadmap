"""
异常层级体系
==============

RAG 管线的自定义异常树，按 pipeline 阶段分类：

  RAGError (基类)
  ├── RetrievalError  — 检索阶段失败
  ├── LLMError       — LLM 调用失败或超时
  ├── CheckpointError — 状态持久化失败
  ├── EmbeddingError  — Embedding 生成失败
  └── ChromaError    — ChromaDB 操作失败

用于上层 try/except 中按异常类型区分处理策略（重试/降级/告警）。
"""

from __future__ import annotations


class RAGError(Exception):
    """All RAG pipeline errors."""


class RetrievalError(RAGError):
    """Retrieval stage failures (ChromaDB / BM25)."""


class LLMError(RAGError):
    """LLM call failures or timeouts."""


class CheckpointError(RAGError):
    """Checkpoint persistence failures."""


class EmbeddingError(RAGError):
    """Embedding generation failures."""


class ChromaError(RAGError):
    """ChromaDB operation failures."""
