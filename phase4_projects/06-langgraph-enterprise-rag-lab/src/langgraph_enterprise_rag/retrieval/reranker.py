"""
Cross-Encoder 重排序器
========================

使用 BAAI/bge-reranker-v2-m3 的 Cross-Encoder 架构进行精排。

架构对比：
  Bi-Encoder (BGE-M3):
    encode(query) → [1024] vec
    encode(doc)   → [1024] vec
    score = cos(query_vec, doc_vec)
    优点：doc 可以预编码存储，检索速度快
    缺点：query 和 doc 缺乏细粒度交互

  Cross-Encoder (BGE-Reranker):
    encode(query + doc) → score
    输入是 query 和 doc 拼接后一起编码，建模深度交互
    优点：精度显著高于 Bi-Encoder，适合精排阶段
    缺点：每对 (query, doc) 都需要单独编码，不能预计算

数据流：
  docs (10) → pairs = [[query, doc_content] for each doc]
  → model.compute_score(pairs, normalize=True)
  → [{doc, rerank_score}] sorted by score desc → top-5

回退策略：模型未加载 → 按 rrf_score 排名 → top-k
"""

from __future__ import annotations

from functools import lru_cache


class SafeReranker:
    """BGE-Reranker 封装，带优雅降级。

    模型加载失败时回退为 RRF 分数排序（保留精排前的结果质量）。
    """

    def __init__(self) -> None:
        self.model = None

        try:
            from FlagEmbedding import FlagReranker

            self.model = FlagReranker(
                "BAAI/bge-reranker-v2-m3",
                use_fp16=False,  # MPS 上 bf16 支持不完整，保守使用 fp32
            )
            print("[reranker] loaded: BAAI/bge-reranker-v2-m3")
        except Exception as exc:
            print(f"[reranker][warn] fallback to heuristic rerank: {exc!r}")

    def rerank(self, query: str, docs: list[dict], top_k: int = 5) -> list[dict]:
        """对检索文档进行 Cross-Encoder 精排。

        Args:
            query: 用户原始查询
            docs: 待精排的文档列表
            top_k: 返回文档数

        Returns:
            按 rerank_score 降序排列的 top-k 文档
        """
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
            # 旧版 FlagEmbedding 可能不支持 normalize 参数
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
    """单例 SafeReranker。"""
    return SafeReranker()
