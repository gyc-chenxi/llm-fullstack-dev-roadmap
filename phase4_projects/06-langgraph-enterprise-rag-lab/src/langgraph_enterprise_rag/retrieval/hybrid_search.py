"""
混合检索引擎
===============

融合 Dense (BGE-M3 语义向量) 和 BM25 (jieba 关键词) 两种检索方式，
通过 Reciprocal Rank Fusion (RRF) 去重排序。

RRF 公式：
  RRF_score(d) = Σᵣ 1/(k + rankᵣ(d))
  其中 k=60（平滑参数），rank 从 1 开始

为什么 RRF 不直接加权求和：
  - Dense 的余弦距离 [0,2] 和 BM25 的原始分数尺度不同
  - RRF 只关心排名，忽略绝对分数差异
  - 不需要调权重超参数，鲁棒性更好

数据流：
  query → Dense(BGE-M3 → ChromaDB) → dense_docs (top-8)
       → BM25(jieba → BM25Okapi)    → bm25_docs (top-8)
       → RRF(60, top-10)            → fused_docs
"""

from __future__ import annotations

from functools import lru_cache

from langgraph_enterprise_rag.retrieval.bm25 import BM25Index, tokenize
from langgraph_enterprise_rag.retrieval.chroma_store import build_chroma_store


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    rrf_k: int = 60,
    final_top_k: int = 10,
) -> list[dict]:
    """对多个有序结果列表执行 Reciprocal Rank Fusion。

    Args:
        ranked_lists: 多个排序文档列表（每个列表已按分数降序排列）
        rrf_k: RRF 平滑参数，默认 60（经验值，稳定性好）
        final_top_k: 最终返回的文档数

    Returns:
        按 rrf_score 降序排列的 top-K 文档列表
    """
    fused: dict[str, dict] = {}

    for ranked_docs in ranked_lists:
        for rank, doc in enumerate(ranked_docs, start=1):
            doc_id = doc["doc_id"]
            score = 1.0 / (rrf_k + rank)

            if doc_id not in fused:
                fused[doc_id] = dict(doc)
                fused[doc_id]["rrf_score"] = 0.0

            fused[doc_id]["rrf_score"] += score

            # 保留各阶段的原始分数供 downstream 使用
            for key in ["dense_score", "bm25_score"]:
                if key in doc:
                    fused[doc_id][key] = doc[key]

    return sorted(
        fused.values(),
        key=lambda x: float(x.get("rrf_score", 0.0)),
        reverse=True,
    )[:final_top_k]


class HybridSearcher:
    """混合检索引擎（单例模式）。

    ChromaStore 立即初始化，BM25Index 延迟初始化（需要从 Chroma 加载所有文档）。
    """

    def __init__(self) -> None:
        self.store = build_chroma_store()
        self._bm25: BM25Index | None = None

    @property
    def bm25(self) -> BM25Index:
        """延迟初始化 BM25Index（首次调用时从 Chroma 加载全量文档到内存）。"""
        if self._bm25 is None:
            self._bm25 = BM25Index(self.store.all_docs())
        return self._bm25

    def search(
        self,
        query: str,
        dense_top_k: int = 8,
        bm25_top_k: int = 8,
        final_top_k: int = 10,
    ) -> list[dict]:
        """单查询混合检索：Dense + BM25 → RRF 融合。"""
        dense_docs = self.store.dense_search(query, top_k=dense_top_k)
        bm25_docs = self.bm25.search(query, top_k=bm25_top_k)

        return reciprocal_rank_fusion(
            [dense_docs, bm25_docs],
            rrf_k=60,
            final_top_k=final_top_k,
        )

    def search_many(
        self,
        queries: list[str],
        dense_top_k: int = 8,
        bm25_top_k: int = 8,
        final_top_k: int = 10,
    ) -> list[dict]:
        """多查询混合检索（配合 query rewriting）。

        每个 query 独立执行 search()，然后对所有结果做第二轮 RRF 融合。
        这确保改写后不同角度的查询结果公平竞争。
        """
        ranked_lists = []

        for query in queries:
            ranked_lists.append(
                self.search(
                    query=query,
                    dense_top_k=dense_top_k,
                    bm25_top_k=bm25_top_k,
                    final_top_k=final_top_k,
                )
            )

        return reciprocal_rank_fusion(
            ranked_lists,
            rrf_k=60,
            final_top_k=final_top_k,
        )


def estimate_relevance(query: str, docs: list[dict]) -> float:
    """启发式相关性分数（不调用 LLM，用于 judge 节点快速判断）。

    评分公式：
      score = 0.75 × best_token_overlap + 0.15 × min(best_dense, 1.0)
      + (0.10 if any BM25 hit)

    宽泛总结类问题特殊处理：直接返回 0.70（大量文档都可能相关）。
    """
    if not docs:
        return 0.0

    q_terms = set(tokenize(query))
    if not q_terms:
        return 0.55 if docs else 0.0

    best_overlap = 0.0

    for doc in docs[:5]:
        d_terms = set(tokenize(doc.get("content", "")[:1500]))
        if not d_terms:
            continue

        overlap = len(q_terms & d_terms) / max(len(q_terms), 1)
        best_overlap = max(best_overlap, overlap)

    best_dense = max(float(x.get("dense_score", 0.0)) for x in docs[:5])
    best_bm25 = max(float(x.get("bm25_score", 0.0)) for x in docs[:5])

    broad_summary_words = ["总结", "主要", "讲了什么", "知识库", "文档"]
    if any(word in query for word in broad_summary_words) and docs:
        return 0.70

    score = 0.75 * best_overlap + 0.15 * min(best_dense, 1.0)

    if best_bm25 > 0:
        score += 0.10

    return max(0.0, min(score, 1.0))


@lru_cache(maxsize=1)
def get_hybrid_searcher() -> HybridSearcher:
    """单例 HybridSearcher（LRU 缓存防止重复创建）。
    ChromaDB 连接和 BM25 索引复用同一实例。
    """
    return HybridSearcher()
