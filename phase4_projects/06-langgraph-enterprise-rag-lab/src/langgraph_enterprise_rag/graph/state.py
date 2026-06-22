from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict


class RetrievedDoc(TypedDict, total=False):
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

    events: Annotated[list[dict], operator.add]
    errors: Annotated[list[str], operator.add]