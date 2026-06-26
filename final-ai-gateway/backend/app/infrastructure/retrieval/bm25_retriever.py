"""
BM25 retriever — keyword-based sparse retrieval.
"""

from __future__ import annotations

import logging
import math
from collections import Counter

from app.domain.value_objects.retrieval_hit import RetrievalHit

logger = logging.getLogger(__name__)


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._documents: list[dict] = []
        self._doc_lengths: list[int] = []
        self._avg_doc_length: float = 0.0
        self._term_freqs: list[Counter] = []
        self._doc_freq: Counter = Counter()
        self._total_docs: int = 0

    def index(self, chunks: list[dict]):
        self._documents = chunks
        self._total_docs = len(chunks)
        self._doc_lengths = []
        self._term_freqs = []
        self._doc_freq = Counter()

        for chunk in chunks:
            tokens = self._tokenize(chunk.get("content", ""))
            self._doc_lengths.append(len(tokens))
            tf = Counter(tokens)
            self._term_freqs.append(tf)
            for term in tf:
                self._doc_freq[term] += 1

        self._avg_doc_length = sum(self._doc_lengths) / max(1, self._total_docs)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        if not self._documents:
            return []

        query_tokens = self._tokenize(query)
        scores = []

        for i, doc in enumerate(self._documents):
            tf = self._term_freqs[i]
            doc_len = self._doc_lengths[i]
            score = 0.0
            for token in query_tokens:
                if token not in tf:
                    continue
                f = tf[token]
                df = self._doc_freq.get(token, 0)
                idf = math.log(1 + (self._total_docs - df + 0.5) / (df + 0.5))
                numerator = f * (self.k1 + 1)
                denominator = f + self.k1 * (1 - self.b + self.b * doc_len / max(1, self._avg_doc_length))
                score += idf * numerator / denominator
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        hits = []
        for idx, score in scores[:top_k]:
            if score <= 0:
                continue
            doc = self._documents[idx]
            hits.append(RetrievalHit(
                doc_id=doc.get("doc_id", ""),
                chunk_index=doc.get("chunk_index", idx),
                content=doc.get("content", ""),
                score=score,
                retrieval_method="bm25",
                metadata=doc,
            ))
        return hits

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re
        tokens = re.findall(r'\w+', text.lower())
        return [t for t in tokens if len(t) > 1]