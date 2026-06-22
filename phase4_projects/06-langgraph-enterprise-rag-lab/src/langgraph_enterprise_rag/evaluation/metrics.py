"""RAG evaluation metrics — recall, MRR, faithfulness, citation accuracy."""

from __future__ import annotations

import math


def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int = 5,
) -> float:
    """Compute Recall@K — fraction of relevant docs in top-K results."""
    if not relevant_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    hits = len(top_k & relevant_ids)
    return hits / len(relevant_ids)


def mean_reciprocal_rank(
    queries_retrieved: list[list[str]],
    queries_relevant: list[set[str]],
) -> float:
    """Compute MRR across multiple queries."""
    if not queries_retrieved:
        return 0.0

    total = 0.0
    for retrieved, relevant in zip(queries_retrieved, queries_relevant):
        if not relevant:
            total += 1.0
            continue

        for rank, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant:
                total += 1.0 / rank
                break
        else:
            total += 0.0

    return total / len(queries_retrieved)


def citation_coverage(answer: str, citations: list[dict]) -> float:
    """Heuristic: fraction of citations that appear to be referenced in the answer."""
    if not citations:
        return 0.0

    matched = 0
    for cite in citations:
        label = cite.get("label", "")
        quote = cite.get("quote", "")
        # Check if citation label or a substring of the quote appears in answer.
        if label and label in answer:
            matched += 1
        elif quote and len(quote) >= 10 and quote[:40] in answer:
            matched += 1

    return matched / len(citations)


def ndcg(scores: list[float], k: int | None = None) -> float:
    """Normalized Discounted Cumulative Gain."""
    if not scores:
        return 0.0

    k = k or len(scores)
    dcg = 0.0
    for i, score in enumerate(scores[:k]):
        dcg += score / math.log2(i + 2)

    ideal = sorted(scores, reverse=True)
    idcg = 0.0
    for i, score in enumerate(ideal[:k]):
        idcg += score / math.log2(i + 2)

    return dcg / idcg if idcg > 0 else 0.0
