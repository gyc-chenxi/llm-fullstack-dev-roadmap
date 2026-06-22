from __future__ import annotations

from functools import lru_cache

from langgraph_enterprise_rag.retrieval.bm25 import BM25Index, tokenize
from langgraph_enterprise_rag.retrieval.chroma_store import build_chroma_store


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]],
    rrf_k: int = 60,
    final_top_k: int = 10,
) -> list[dict]:
    fused: dict[str, dict] = {}

    for ranked_docs in ranked_lists:
        for rank, doc in enumerate(ranked_docs, start=1):
            doc_id = doc["doc_id"]
            score = 1.0 / (rrf_k + rank)

            if doc_id not in fused:
                fused[doc_id] = dict(doc)
                fused[doc_id]["rrf_score"] = 0.0

            fused[doc_id]["rrf_score"] += score

            for key in ["dense_score", "bm25_score"]:
                if key in doc:
                    fused[doc_id][key] = doc[key]

    return sorted(
        fused.values(),
        key=lambda x: float(x.get("rrf_score", 0.0)),
        reverse=True,
    )[:final_top_k]


class HybridSearcher:
    def __init__(self) -> None:
        self.store = build_chroma_store()
        self._bm25: BM25Index | None = None

    @property
    def bm25(self) -> BM25Index:
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
    return HybridSearcher()