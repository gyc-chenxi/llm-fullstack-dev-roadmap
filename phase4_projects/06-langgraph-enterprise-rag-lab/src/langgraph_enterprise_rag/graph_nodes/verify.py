from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState


def verify_node(state: RAGState) -> dict:
    answer = state.get("generated_answer", "")
    citations = state.get("citations", [])
    docs = state.get("reranked_docs") or state.get("retrieved_docs", [])

    if "知识库中未找到足够证据" in answer:
        score = 1.0
    elif citations and docs and "来源" in answer:
        score = 0.85
    elif citations and docs:
        score = 0.72
    else:
        score = 0.30

    return {
        "faithfulness_score": score,
        "events": [
            {
                "node": "verify",
                "status": "done",
                "faithfulness_score": score,
            }
        ],
    }