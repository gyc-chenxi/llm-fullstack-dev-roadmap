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
    docs: list[dict]

    def __post_init__(self) -> None:
        self.corpus_tokens = [tokenize(x.get("content", "")) for x in self.docs]
        self.model = BM25Okapi(self.corpus_tokens) if self.docs else None

    def search(self, query: str, top_k: int = 8) -> list[dict]:
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