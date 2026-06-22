from __future__ import annotations

from functools import lru_cache


class SafeReranker:
    def __init__(self) -> None:
        self.model = None

        try:
            from FlagEmbedding import FlagReranker

            self.model = FlagReranker(
                "BAAI/bge-reranker-v2-m3",
                use_fp16=False,
            )
            print("[reranker] loaded: BAAI/bge-reranker-v2-m3")
        except Exception as exc:
            print(f"[reranker][warn] fallback to heuristic rerank: {exc!r}")

    def rerank(self, query: str, docs: list[dict], top_k: int = 5) -> list[dict]:
        if not docs:
            return []

        if self.model is None:
            ranked = sorted(
                docs,
                key=lambda x: float(x.get("rrf_score", 0.0)),
                reverse=True,
            )
            return ranked[:top_k]

        pairs = [[query, doc.get("content", "")] for doc in docs]

        try:
            scores = self.model.compute_score(pairs, normalize=True)
        except TypeError:
            scores = self.model.compute_score(pairs)
        except Exception as exc:
            print(f"[reranker][warn] compute failed: {exc!r}")
            return docs[:top_k]

        if isinstance(scores, float):
            scores = [scores]

        ranked_docs = []

        for doc, score in zip(docs, scores):
            item = dict(doc)
            item["rerank_score"] = float(score)
            ranked_docs.append(item)

        return sorted(
            ranked_docs,
            key=lambda x: float(x.get("rerank_score", 0.0)),
            reverse=True,
        )[:top_k]


@lru_cache(maxsize=1)
def get_reranker() -> SafeReranker:
    return SafeReranker()
