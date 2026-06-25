"""
Cross-Encoder 重排序节点
==========================

使用 BAAI/bge-reranker-v2-m3（Cross-Encoder 架构）对检索文档进行精排。

与 Bi-Encoder (BGE-M3) 的区别：
  - Bi-Encoder: query 和 doc 独立编码，速度快但交互弱
  - Cross-Encoder: query+doc 拼接编码，速度慢但精度高

数据流：
  retrieved_docs (10) → [query, doc_content] pairs → Cross-Encoder → rerank_score
  → 按 rerank_score 降序排列 → reranked_docs (top_k=5)

回退策略：
  - 模型未加载 → 按 rrf_score 重新排序
  - compute_score 失败 → 返回前 top_k 篇原文
"""

from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState
from langgraph_enterprise_rag.retrieval.reranker import get_reranker


def rerank_node(state: RAGState) -> dict:
    """对检索结果进行 Cross-Encoder 精排，输出 top-5。

    失败时回退：rrf_score 排序 → 前 5 篇原文（不做精排）。
    """
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
