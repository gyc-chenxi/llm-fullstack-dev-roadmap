"""
混合检索节点
===============

对改写后的多个查询变体执行混合检索：
  Dense Search (BGE-M3, ChromaDB) + BM25 Sparse (jieba 分词)
  → Reciprocal Rank Fusion (RRF, k=60)
  → 去重排序后返回 top-10

为什么使用混合检索：
  - Dense 擅长语义匹配，但可能漏掉精确关键词
  - BM25 擅长关键词匹配，但无法处理同义词
  - RRF 融合两者优势，不需要调权重超参数

数据流：
  rewritten_queries (3-4 个) → search_many()
    → 每个 query: Dense(top_k=8) + BM25(top_k=8) → RRF(k=60, top_k=10)
    → 多 query 结果再次 RRF 融合 → retrieved_docs (10 篇)
"""

from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState
from langgraph_enterprise_rag.retrieval.hybrid_search import get_hybrid_searcher


def retrieve_node(state: RAGState) -> dict:
    """对改写后的查询执行混合检索。

    如果无 rewritten_queries，回退为原始 query 的单次检索。
    """
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
