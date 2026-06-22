from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState


def fallback_node(state: RAGState) -> dict:
    answer = (
        "知识库中未找到足够证据回答该问题。\n\n"
        "为了避免幻觉，本系统不会基于模型自身知识强行编造答案。"
    )

    return {
        "generated_answer": answer,
        "citations": [],
        "status": "fallback",
        "events": [{"node": "fallback", "status": "done"}],
    }