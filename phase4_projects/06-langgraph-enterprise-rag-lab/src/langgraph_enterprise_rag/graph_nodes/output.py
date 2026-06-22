from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState


def output_node(state: RAGState) -> dict:
    status = state.get("status") or "ok"
    answer = state.get("generated_answer") or "未生成答案。"

    return {
        "final_answer": answer,
        "status": status,
        "events": [
            {
                "node": "output",
                "status": status,
            }
        ],
    }