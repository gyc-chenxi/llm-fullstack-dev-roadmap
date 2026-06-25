"""
LangGraph 状态定义
====================

RAGState 是 LangGraph 状态机的核心数据结构，贯穿所有 8 个节点。

状态传递机制：
  - 每个节点返回 dict，LangGraph 自动合并到全局 state
  - events/errors 使用 Annotated[list, operator.add] 实现累加（而非覆盖）
  - 其他字段使用覆盖语义，节点返回的新值替换旧值

数据流中的关键状态转换：
  query → classify → query_type → rewrite → rewritten_queries (×3)
  → retrieve → retrieved_docs (10) → judge → relevance_score
  → rerank → reranked_docs (5) → generate → generated_answer + citations
  → verify → faithfulness_score → output → final_answer
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict


class RetrievedDoc(TypedDict, total=False):
    """单个检索文档的完整信息。

    dense_score / bm25_score: 各自检索阶段的原始分数
    rrf_score: 经过 Reciprocal Rank Fusion 后的融合分数
    rerank_score: Cross-Encoder 重排序后的分数（仅 rerank 阶段填充）
    """
    doc_id: str
    source: str
    title: str
    content: str
    dense_score: float
    bm25_score: float
    rrf_score: float
    rerank_score: float
    metadata: dict


class RAGState(TypedDict, total=False):
    """LangGraph 全局状态。

    字段分为三类：
      - 输入: query, thread_id, max_retries
      - 中间状态: query_type, rewritten_queries, retrieved_docs, reranked_docs,
                   relevance_score, generated_answer, citations, faithfulness_score
      - 累加器: events (Annotated[list, operator.add]), errors (同上)
    """
    query: str
    thread_id: str

    query_type: Literal["simple", "needs_retrieval", "multi_hop"]
    rewritten_queries: list[str]

    retrieved_docs: list[RetrievedDoc]
    reranked_docs: list[RetrievedDoc]
    relevance_score: float

    generated_answer: str
    citations: list[dict]
    faithfulness_score: float

    retrieve_retry_count: int
    generate_retry_count: int
    max_retries: int

    final_answer: str
    status: Literal["ok", "fallback", "failed"]

    # 累加器：每个节点都会追加事件，不会被覆盖
    events: Annotated[list[dict], operator.add]
    errors: Annotated[list[str], operator.add]