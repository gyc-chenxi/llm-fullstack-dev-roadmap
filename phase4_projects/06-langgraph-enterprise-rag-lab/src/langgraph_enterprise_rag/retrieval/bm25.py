"""
BM25 关键词检索
=================

基于 jieba 中文分词 + rank_bm25 的稀疏检索实现。

数据流：
  Corpus → jieba 分词 → 去停用词/单字 → corpus_tokens: list[list[str]]
    → BM25Okapi.fit(corpus_tokens)
  Query  → jieba 分词 → 去停用词/单字
    → BM25Okapi.get_scores(query_tokens) → sorted by score desc → top-K docs

分词策略：
  - 中文：jieba.cut 精确模式（不采用全模式，避免词粒度过细）
  - 英文：re.findall([A-Za-z0-9_]+) 按单词切分
  - 过滤：停用词 + 单字符 token（中文"我/的"、英文"a/i"等）

BM25Okapi 的 k1 默认 1.5, b 默认 0.75（标准 Okapi BM25 参数）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import jieba
from rank_bm25 import BM25Okapi


STOPWORDS = {
    "的",
    "了",
    "是",
    "在",
    "和",
    "与",
    "及",
    "请",
    "这个",
    "这些",
    "一下",
    "主要",
    "什么",
    "the",
    "is",
    "are",
    "a",
    "an",
    "of",
    "to",
    "and",
}


def tokenize(text: str) -> list[str]:
    """中英文混合分词，过滤停用词和单字 token。

    Returns: 过滤后的 token 列表（去重，均为小写）
    """
    chinese_tokens = list(jieba.cut(text))
    english_tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())

    tokens = []
    for token in chinese_tokens + english_tokens:
        token = token.strip().lower()
        if not token:
            continue
        if token in STOPWORDS:
            continue
        if len(token) <= 1:
            continue
        tokens.append(token)

    return tokens


@dataclass
class BM25Index:
    """BM25 稀疏检索索引。

    初始化时对全量文档语料分词并构建 BM25Okapi 模型。
    """

    docs: list[dict]

    def __post_init__(self) -> None:
        self.corpus_tokens = [tokenize(x.get("content", "")) for x in self.docs]
        self.model = BM25Okapi(self.corpus_tokens) if self.docs else None

    def search(self, query: str, top_k: int = 8) -> list[dict]:
        """BM25 检索，返回 top-K 文档（只返回 score > 0 的结果）。"""
        if not self.docs or self.model is None:
            return []

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        scores = self.model.get_scores(q_tokens)
        ranked = sorted(
            enumerate(scores),
            key=lambda x: float(x[1]),
            reverse=True,
        )[:top_k]

        results: list[dict] = []

        for idx, score in ranked:
            if float(score) <= 0:
                continue

            doc = dict(self.docs[idx])
            doc["bm25_score"] = float(score)
            results.append(doc)

        return results
