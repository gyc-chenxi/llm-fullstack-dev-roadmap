from __future__ import annotations

from typing import Literal

from langgraph_enterprise_rag.graph.state import RAGState


def route_after_judge(state: RAGState) -> Literal["rewrite", "rerank", "fallback"]:
    score = float(state.get("relevance_score", 0.0))
    retry_count = int(state.get("retrieve_retry_count", 0))
    max_retries = int(state.get("max_retries", 3))

    if score >= 0.45:
        return "rerank"

    if retry_count < max_retries:
        return "rewrite"

    return "fallback"


def route_after_verify(state: RAGState) -> Literal["generate", "output"]:
    score = float(state.get("faithfulness_score", 0.0))
    retry_count = int(state.get("generate_retry_count", 0))
    max_retries = int(state.get("max_retries", 3))

    if score >= 0.70:
        return "output"

    if retry_count < max_retries:
        return "generate"

    return "output"