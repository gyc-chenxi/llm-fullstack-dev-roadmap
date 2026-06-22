from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState
from langgraph_enterprise_rag.retrieval.hybrid_search import get_hybrid_searcher


def retrieve_node(state: RAGState) -> dict:
    queries = state.get("rewritten_queries") or [state["query"]]

    try:
        searcher = get_hybrid_searcher()
        docs = searcher.search_many(
            queries=queries,
            dense_top_k=8,
            bm25_top_k=8,
            final_top_k=10,
        )

        return {
            "retrieved_docs": docs,
            "events": [
                {
                    "node": "retrieve",
                    "status": "done",
                    "doc_count": len(docs),
                }
            ],
        }
    except Exception as exc:
        return {
            "retrieved_docs": [],
            "errors": [f"retrieve failed: {exc!r}"],
            "events": [{"node": "retrieve", "status": "failed"}],
        }