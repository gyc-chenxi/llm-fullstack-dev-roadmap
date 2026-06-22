"""Unit tests for retrieval pipeline (offline — no LLM required)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from langgraph_enterprise_rag.retrieval.bm25 import BM25Index, tokenize
from langgraph_enterprise_rag.retrieval.chunking import chunk_text
from langgraph_enterprise_rag.retrieval.hybrid_search import (
    HybridSearcher,
    estimate_relevance,
    reciprocal_rank_fusion,
)


# ── tokenize ──────────────────────────────────────────────────────────


def test_tokenize_chinese() -> None:
    tokens = tokenize("这是一段中文测试文本")
    assert len(tokens) >= 2
    assert "一段" not in tokenize("我")
    # single-char tokens are filtered
    for t in tokens:
        assert len(t) >= 2


def test_tokenize_english() -> None:
    tokens = tokenize("hello world retrieval test")
    assert "hello" in tokens
    assert "world" in tokens


def test_tokenize_stopwords_filtered() -> None:
    tokens = tokenize("这是的了一个测试")
    assert "的" not in tokens
    assert "了" not in tokens


def test_tokenize_empty() -> None:
    assert tokenize("") == []


# ── BM25 ──────────────────────────────────────────────────────────────


def test_bm25_search_returns_results() -> None:
    docs = [
        {"doc_id": "1", "content": "LangGraph 企业级 RAG 状态机"},
        {"doc_id": "2", "content": "Chroma 持久化向量数据库"},
        {"doc_id": "3", "content": "BM25 关键词稀疏检索算法"},
    ]
    index = BM25Index(docs)
    results = index.search("RAG 状态机", top_k=2)
    assert len(results) >= 1
    # doc_id 1 should rank high.
    assert results[0]["doc_id"] == "1"


def test_bm25_empty_docs() -> None:
    index = BM25Index([])
    assert index.search("query") == []


# ── RRF ───────────────────────────────────────────────────────────────


def test_rrf_fusion_basic() -> None:
    dense = [
        {"doc_id": "a", "content": "x", "dense_score": 0.9},
        {"doc_id": "b", "content": "y", "dense_score": 0.7},
    ]
    bm25 = [
        {"doc_id": "b", "content": "y", "bm25_score": 5.0},
        {"doc_id": "a", "content": "x", "bm25_score": 2.0},
    ]
    fused = reciprocal_rank_fusion([dense, bm25], final_top_k=2)
    assert len(fused) == 2
    # Both docs appear.
    ids = {d["doc_id"] for d in fused}
    assert ids == {"a", "b"}


def test_rrf_empty_input() -> None:
    assert reciprocal_rank_fusion([], final_top_k=10) == []


# ── Relevance estimation ──────────────────────────────────────────────


def test_estimate_relevance_no_docs() -> None:
    assert estimate_relevance("test", []) == 0.0


def test_estimate_relevance_with_docs() -> None:
    docs = [{"doc_id": "1", "content": "企业级 RAG 系统设计", "dense_score": 0.8}]
    score = estimate_relevance("RAG 系统", docs)
    assert 0.0 < score <= 1.0


# ── Chunking integration ──────────────────────────────────────────────


def test_chunk_preserves_doc_identity() -> None:
    text = "A" * 2000
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    # Every chunk should be > 0 and ≤ chunk_size in length (approx).
    for c in chunks:
        assert 0 < len(c) <= 500
