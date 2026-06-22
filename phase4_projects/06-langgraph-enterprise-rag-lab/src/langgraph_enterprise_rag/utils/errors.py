"""Custom exception classes for the RAG pipeline."""

from __future__ import annotations


class RAGError(Exception):
    """Base exception for all RAG pipeline errors."""


class RetrievalError(RAGError):
    """Raised when the retrieval stage fails."""


class LLMError(RAGError):
    """Raised when the LLM call fails or times out."""


class CheckpointError(RAGError):
    """Raised when checkpoint operations fail."""


class EmbeddingError(RAGError):
    """Raised when embedding generation fails."""


class ChromaError(RAGError):
    """Raised when Chroma operations fail."""
