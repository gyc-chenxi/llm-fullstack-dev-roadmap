"""
相关性评估节点
=================

启发式评估检索结果对用户查询的相关性。

评分公式：
  score = 0.75 × token_overlap + 0.15 × min(best_dense, 1.0) + (0.10 if bm25_hit else 0)

特殊处理：
  - 含"总结/主要/讲了什么/知识库/文档"的宽泛查询直接给 0.70（大量文档都可能相关）
  - 无检索结果时为 0.0

数据流：query + retrieved_docs → estimate_relevance() → relevance_score (0.0-1.0)
"""

from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState
from langgraph_enterprise_rag.retrieval.hybrid_search import estimate_relevance


def judge_node(state: RAGState) -> dict:
    """评估检索结果对用户查询的相关性，返回 0-1 分数。"""
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
