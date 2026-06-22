from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState


def classify_node(state: RAGState) -> dict:
    query = state.get("query", "").strip()

    if not query:
        return {
            "query_type": "simple",
            "errors": ["empty query"],
            "events": [{"node": "classify", "status": "failed"}],
        }

    retrieval_keywords = [
        "文档",
        "知识库",
        "资料",
        "引用",
        "根据",
        "总结",
        "解释",
        "对比",
        "来源",
        "报告",
    ]

    multi_hop_keywords = ["对比", "综合", "分别", "关系", "区别", "影响", "原因"]

    if any(word in query for word in multi_hop_keywords):
        query_type = "multi_hop"
    elif any(word in query for word in retrieval_keywords):
        query_type = "needs_retrieval"
    else:
        query_type = "needs_retrieval"

    return {
        "query_type": query_type,
        "events": [
            {
                "node": "classify",
                "status": "done",
                "query_type": query_type,
            }
        ],
    }