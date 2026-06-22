from __future__ import annotations

from src.langgraph_enterprise_rag.graph.state import RAGState
from src.langgraph_enterprise_rag.retrieval.reranker import get_reranker


def rerank_node(state: RAGState) -> dict:
    query = state["query"]
    docs = state.get("retrieved_docs", [])

    try:
        reranker = get_reranker()
        reranked_docs = reranker.rerank(query, docs, top_k=5)

        return {
            "reranked_docs": reranked_docs,
            "events": [
                {
                    "node": "rerank",
                    "status": "done",
                    "doc_count": len(reranked_docs),
                }
            ],
        }

    except Exception as exc:
        return {
            "reranked_docs": docs[:5],
            "errors": [f"rerank failed: {exc!r}"],
            "events": [{"node": "rerank", "status": "fallback"}],
        }