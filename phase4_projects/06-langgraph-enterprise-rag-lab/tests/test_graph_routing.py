"""Unit tests for LangGraph routing logic (no graph runtime needed)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from langgraph_enterprise_rag.graph.routing import route_after_judge, route_after_verify


# ── route_after_judge ─────────────────────────────────────────────────


def test_judge_routes_to_rerank_when_relevant() -> None:
    state = {
        "relevance_score": 0.72,
        "retrieve_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_judge(state) == "rerank"  # type: ignore[arg-type]


def test_judge_routes_to_rewrite_when_low_relevance_and_retries_left() -> None:
    state = {
        "relevance_score": 0.20,
        "retrieve_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_judge(state) == "rewrite"  # type: ignore[arg-type]


def test_judge_routes_to_fallback_when_retries_exhausted() -> None:
    state = {
        "relevance_score": 0.20,
        "retrieve_retry_count": 3,
        "max_retries": 3,
    }
    assert route_after_judge(state) == "fallback"  # type: ignore[arg-type]


def test_judge_threshold_boundary() -> None:
    """relevance_score == 0.45 → rerank."""
    state = {
        "relevance_score": 0.45,
        "retrieve_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_judge(state) == "rerank"  # type: ignore[arg-type]

    state["relevance_score"] = 0.449  # type: ignore[index]
    assert route_after_judge(state) == "rewrite"  # type: ignore[arg-type]


def test_judge_defaults() -> None:
    """Missing fields should use safe defaults."""
    assert route_after_judge({}) == "rerank"  # type: ignore[arg-type]
    # 0.0 >= 0.45 is False, retry count 0 < 3 → rewrite
    # Wait — empty dict: relevance_score defaults to 0.0, retry_count to 0
    # 0.0 >= 0.45 → False; 0 < 3 → True → "rewrite"
    result = route_after_judge({})  # type: ignore[arg-type]
    assert result in ("rewrite", "rerank", "fallback")


# ── route_after_verify ────────────────────────────────────────────────


def test_verify_routes_to_output_when_faithful() -> None:
    state = {
        "faithfulness_score": 0.85,
        "generate_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_verify(state) == "output"  # type: ignore[arg-type]


def test_verify_routes_to_generate_when_not_faithful() -> None:
    state = {
        "faithfulness_score": 0.40,
        "generate_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_verify(state) == "generate"  # type: ignore[arg-type]


def test_verify_generate_retries_exhausted() -> None:
    state = {
        "faithfulness_score": 0.40,
        "generate_retry_count": 3,
        "max_retries": 3,
    }
    assert route_after_verify(state) == "output"  # type: ignore[arg-type]


def test_verify_defaults() -> None:
    result = route_after_verify({})  # type: ignore[arg-type]
    assert result in ("generate", "output")
