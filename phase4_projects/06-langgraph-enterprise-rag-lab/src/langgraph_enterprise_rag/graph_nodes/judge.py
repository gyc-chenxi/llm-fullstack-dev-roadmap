from __future__ import annotations

from src.langgraph_enterprise_rag.graph.state import RAGState
from src.langgraph_enterprise_rag.retrieval.hybrid_search import estimate_relevance


def judge_node(state: RAGState) -> dict:
    query = state["query"]
    docs = state.get("retrieved_docs", [])

    score = estimate_relevance(query, docs)

    return {
        "relevance_score": score,
        "events": [
            {
                "node": "judge",
                "status": "done",
                "relevance_score": score,
            }
        ],
    }