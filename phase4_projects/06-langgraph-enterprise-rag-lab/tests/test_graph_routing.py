"""
单元测试：LangGraph 条件路由逻辑（无 graph 运行时依赖）
========================================================

测试 route_after_judge 和 route_after_verify 的所有分支和边界条件。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from langgraph_enterprise_rag.graph.routing import route_after_judge, route_after_verify


# ── route_after_judge ──


def test_judge_routes_to_rerank_when_relevant() -> None:
    """relevance_score >= 0.45 → 直接进入 rerank 精排。"""
    state = {
        "relevance_score": 0.72,
        "retrieve_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_judge(state) == "rerank"  # type: ignore[arg-type]


def test_judge_routes_to_rewrite_when_low_relevance_and_retries_left() -> None:
    """relevance_score < 0.45 & retries left → 改写查询重新检索。"""
    state = {
        "relevance_score": 0.20,
        "retrieve_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_judge(state) == "rewrite"  # type: ignore[arg-type]


def test_judge_routes_to_fallback_when_retries_exhausted() -> None:
    """relevance_score < 0.45 & retries exhausted → 放弃检索，走 fallback。"""
    state = {
        "relevance_score": 0.20,
        "retrieve_retry_count": 3,
        "max_retries": 3,
    }
    assert route_after_judge(state) == "fallback"  # type: ignore[arg-type]


def test_judge_threshold_boundary() -> None:
    """relevance_score == 0.45 为边界值：>=0.45 走 rerank，<0.45 走 rewrite。"""
    state = {
        "relevance_score": 0.45,
        "retrieve_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_judge(state) == "rerank"  # type: ignore[arg-type]

    state["relevance_score"] = 0.449  # type: ignore[index]
    assert route_after_judge(state) == "rewrite"  # type: ignore[arg-type]


def test_judge_defaults() -> None:
    """缺失字段使用安全默认值（缺省 state 也能正确路由）。"""
    result = route_after_judge({})  # type: ignore[arg-type]
    assert result in ("rewrite", "rerank", "fallback")


# ── route_after_verify ──


def test_verify_routes_to_output_when_faithful() -> None:
    """faithfulness_score >= 0.70 → 答案通过校验，进入 output。"""
    state = {
        "faithfulness_score": 0.85,
        "generate_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_verify(state) == "output"  # type: ignore[arg-type]


def test_verify_routes_to_generate_when_not_faithful() -> None:
    """faithfulness_score < 0.70 & retries left → 重新生成答案。"""
    state = {
        "faithfulness_score": 0.40,
        "generate_retry_count": 0,
        "max_retries": 3,
    }
    assert route_after_verify(state) == "generate"  # type: ignore[arg-type]


def test_verify_generate_retries_exhausted() -> None:
    """faithfulness_score < 0.70 & retries exhausted → 强制输出（即使不够好）。"""
    state = {
        "faithfulness_score": 0.40,
        "generate_retry_count": 3,
        "max_retries": 3,
    }
    assert route_after_verify(state) == "output"  # type: ignore[arg-type]


def test_verify_defaults() -> None:
    """缺失字段使用安全默认值。"""
    result = route_after_verify({})  # type: ignore[arg-type]
    assert result in ("generate", "output")
