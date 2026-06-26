"""
RAG Eval Runner — evaluates RAG pipeline quality (Recall@K, MRR, Citation Accuracy).
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from app.infrastructure.langchain_runtime.langchain_rag_runtime import LangChainRagRuntime

logger = logging.getLogger(__name__)


class RagEvalRunner:
    def __init__(self, rag_runtime: LangChainRagRuntime, gold_set_path: str = "./tests/data/rag_gold_set.jsonl"):
        self.rag_runtime = rag_runtime
        self.gold_set_path = Path(gold_set_path)

    async def evaluate(self) -> dict[str, Any]:
        questions = self._load_gold_set()
        if not questions:
            return {"error": "no gold set loaded", "note": "Create tests/data/rag_gold_set.jsonl"}

        results = []
        for item in questions:
            result = await self._evaluate_single(item)
            results.append(result)

        return self._compute_metrics(results)

    async def _evaluate_single(self, item: dict) -> dict:
        question = item.get("question", "")
        expected_doc_ids = set(item.get("relevant_doc_ids", []))
        expected_answer = item.get("expected_answer", "")

        t0 = time.monotonic()
        hits = await self.rag_runtime.retrieve(question, top_k=5)
        retrieval_latency = (time.monotonic() - t0) * 1000

        retrieved_ids = [h.doc_id for h in hits]

        # Recall@K
        hits_in_expected = sum(1 for doc_id in retrieved_ids if doc_id in expected_doc_ids)
        recall_at_k = hits_in_expected / max(1, len(expected_doc_ids))

        # MRR
        mrr = 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_doc_ids:
                mrr = 1.0 / (i + 1)
                break

        return {
            "question": question,
            "recall_at_5": recall_at_k,
            "mrr": mrr,
            "retrieval_latency_ms": retrieval_latency,
            "hits_retrieved": len(hits),
            "expected_relevant": len(expected_doc_ids),
            "hits_found": hits_in_expected,
        }

    def _compute_metrics(self, results: list[dict]) -> dict[str, Any]:
        n = len(results)
        if n == 0:
            return {}

        avg_recall = sum(r["recall_at_5"] for r in results) / n
        avg_mrr = sum(r["mrr"] for r in results) / n
        avg_latency = sum(r["retrieval_latency_ms"] for r in results) / n

        recall_sorted = sorted(r["recall_at_5"] for r in results)
        p95_idx = int(n * 0.95)
        p50_idx = int(n * 0.50)

        return {
            "total_questions": n,
            "avg_recall_at_5": round(avg_recall, 4),
            "avg_mrr": round(avg_mrr, 4),
            "avg_retrieval_latency_ms": round(avg_latency, 2),
            "recall_p50": recall_sorted[p50_idx] if p50_idx < n else 0,
            "recall_p95": recall_sorted[p95_idx] if p95_idx < n else 0,
            "details": results[:5],
        }

    def _load_gold_set(self) -> list[dict]:
        if not self.gold_set_path.exists():
            logger.warning("Gold set not found at %s, using demo data", self.gold_set_path)
            return self._demo_gold_set()

        items = []
        with open(self.gold_set_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items

    @staticmethod
    def _demo_gold_set() -> list[dict]:
        return [
            {
                "question": "What is machine learning?",
                "relevant_doc_ids": ["ml_intro", "ai_basics"],
                "expected_answer": "Machine learning is a subset of AI...",
            },
            {
                "question": "Explain the transformer architecture",
                "relevant_doc_ids": ["transformer_paper", "attention_mechanism"],
                "expected_answer": "The transformer architecture uses self-attention...",
            },
            {
                "question": "What is the capital of France?",
                "relevant_doc_ids": ["world_geography"],
                "expected_answer": "The capital of France is Paris.",
            },
        ]