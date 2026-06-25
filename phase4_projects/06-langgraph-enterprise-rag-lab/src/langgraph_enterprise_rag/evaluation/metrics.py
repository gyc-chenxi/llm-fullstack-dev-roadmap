"""
评估指标
==========

RAG 管线离线评估的 4 个标准指标：

  - Recall@K: top-K 结果中包含的相关文档比例
  - MRR: 第一个相关文档的倒数排名的平均值
  - Citation Coverage: 引用出现在答案中的比例（启发性检查 LLM 是否真的用了引用）
  - NDCG: 归一化折损累积增益（综合评分和排名的指标）
"""

from __future__ import annotations

import math


def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int = 5,
) -> float:
    """Recall@K — 相关文档在 top-K 中被检索到的比例。

    recall@K = |retrieved[:k] ∩ relevant| / |relevant|
    """
    if not relevant_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    hits = len(top_k & relevant_ids)
    return hits / len(relevant_ids)


def mean_reciprocal_rank(
    queries_retrieved: list[list[str]],
    queries_relevant: list[set[str]],
) -> float:
    """MRR — 多查询平均的倒数排名。

    MRR = (1/|Q|) * Σ rank_first_relevant
    第一个相关文档排第 1 得 1.0，排第 n 得 1/n。
    """
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
    """引用覆盖度 — 评估 LLM 是否确实使用了引用标记。

    检查 citation label 或 quote 前 40 字符是否出现在答案中。
    """
    if not citations:
        return 0.0

    matched = 0
    for cite in citations:
        label = cite.get("label", "")
        quote = cite.get("quote", "")
        if label and label in answer:
            matched += 1
        elif quote and len(quote) >= 10 and quote[:40] in answer:
            matched += 1

    return matched / len(citations)


def ndcg(scores: list[float], k: int | None = None) -> float:
    """NDCG — 归一化折损累积增益。

    DCG = Σ score_i / log2(i+2)
    NDCG = DCG / IDCG，其中 IDCG 是最理想排序下的 DCG。
    """
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
