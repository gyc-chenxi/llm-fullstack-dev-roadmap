#!/usr/bin/env python3
"""RAG Comparison Engine — GraphRAG vs Vector RAG.

Provides a programmatic API for running the same query set against
both GraphRAG and Vector RAG, collecting timing and answer data,
and generating a comparison report.

Usage:
    from graphrag_lab.comparator import RAGComparator
    comp = RAGComparator(graphrag_root=".", vector_store="data/vector_store")
    report = comp.run_comparison()
    comp.save_report(report, "docs/comparison_report.md")
"""

import time
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default test queries
# ---------------------------------------------------------------------------
DEFAULT_QUERIES = [
    {"query": "What is the Transformer architecture?", "type": "factual", "expected_best": "vector"},
    {"query": "How are Transformer, BERT, GPT, and LoRA related?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What is the relationship between attention and PEFT?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "How do knowledge distillation and quantization relate?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What are the major themes in this knowledge base?", "type": "global", "expected_best": "graphrag"},
    {"query": "What are key research trends in LLMs?", "type": "global", "expected_best": "graphrag"},
    {"query": "Summarize the evolution from RNNs to Transformers.", "type": "summary", "expected_best": "graphrag"},
    {"query": "What is masked language modeling in BERT?", "type": "factual", "expected_best": "vector"},
]


class RAGComparator:
    """Run side-by-side GraphRAG vs Vector RAG comparison."""

    def __init__(
        self,
        graphrag_root: str = ".",
        vector_store: str = "data/vector_store",
        collection_name: str = "graphrag_lab_corpus",
        embedding_model: str = "BAAI/bge-m3",
        device: str = "mps",
    ):
        self.graphrag_root = str(Path(graphrag_root).resolve())
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.device = device

        # Lazy-loaded
        self._model = None
        self._collection = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading %s on %s ...", self.embedding_model, self.device)
            self._model = SentenceTransformer(self.embedding_model, device=self.device)
        return self._model

    @property
    def collection(self):
        if self._collection is None:
            import chromadb
            client = chromadb.PersistentClient(path=self.vector_store)
            self._collection = client.get_collection(self.collection_name)
            logger.info("Vector store: %d vectors", self._collection.count())
        return self._collection

    def query_graphrag(self, query: str, query_type: str = "factual") -> dict:
        """Run a GraphRAG query. Returns dict with answer, time, method."""
        import subprocess

        method = "local" if query_type in ("multi_hop", "factual") else "global"
        cmd = [
            sys.executable, "-m", "graphrag", "query",
            "--root", self.graphrag_root,
            "--method", method,
            query,
        ]

        t0 = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.graphrag_root)
        elapsed = time.time() - t0

        if result.returncode != 0:
            return {
                "answer": f"[ERROR] {result.stderr.strip()[:300]}",
                "time": elapsed,
                "method": method,
                "error": True,
            }

        return {
            "answer": result.stdout.strip(),
            "time": elapsed,
            "method": method,
            "error": False,
        }

    def query_vector_rag(self, query: str, top_k: int = 5) -> dict:
        """Run a Vector RAG query. Returns dict with context, time."""
        t0 = time.time()
        q_emb = self.model.encode([query], normalize_embeddings=True)
        results = self.collection.query(
            query_embeddings=q_emb.tolist(), n_results=top_k
        )
        elapsed = time.time() - t0

        docs = results["documents"][0]
        distances = results["distances"][0]
        parts = []
        for j, (doc, dist) in enumerate(zip(docs, distances)):
            score = 1.0 - dist
            parts.append(f"[Chunk {j+1}, score={score:.3f}] {doc[:300]}...")

        return {
            "answer": "\n\n".join(parts),
            "time": elapsed,
            "top_k": top_k,
            "error": False,
        }

    def run_comparison(self, queries: list | None = None) -> list:
        """Run all queries against both systems. Returns list of result dicts."""
        queries = queries or DEFAULT_QUERIES
        results = []

        for i, tq in enumerate(queries):
            logger.info("[%d/%d] %s: %s", i+1, len(queries),
                         tq["type"], tq["query"][:60])

            g_result = self.query_graphrag(tq["query"], tq["type"])
            v_result = self.query_vector_rag(tq["query"])

            results.append({
                "query": tq["query"],
                "type": tq["type"],
                "expected_best": tq["expected_best"],
                "graphrag": g_result,
                "vector_rag": v_result,
            })

        return results

    def generate_report(self, results: list) -> str:
        """Generate a Markdown comparison report."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        dim = self.model.get_sentence_embedding_dimension()

        lines = [
            f"# GraphRAG vs Vector RAG — Comparison Report\n\n",
            f"**Date**: {now}\n\n",
            f"**GraphRAG LLM**: DeepSeek API\n\n",
            f"**Vector RAG**: Chroma + {self.embedding_model} (dim={dim})\n\n",
            f"**Queries**: {len(results)}\n\n",
            "---\n\n",
            "## Summary\n\n",
            "| # | Type | Expected | GraphRAG | VectorRAG | Winner |\n",
            "|:-:|:-----|:--------:|:--------:|:---------:|:------:|\n",
        ]

        for i, r in enumerate(results):
            g_str = f"{r['graphrag']['time']:.1f}s ({r['graphrag'].get('method', '?')})"
            v_str = f"{r['vector_rag']['time']:.1f}s"
            winner = (
                "🏆 GraphRAG" if r["expected_best"] == "graphrag"
                else "🏆 VectorRAG" if r["expected_best"] == "vector"
                else "—"
            )
            lines.append(
                f"| {i+1} | {r['type']} | {r['expected_best']} "
                f"| {g_str} | {v_str} | {winner} |\n"
            )

        g_times = [r["graphrag"]["time"] for r in results]
        v_times = [r["vector_rag"]["time"] for r in results]
        lines.append(f"\n**GraphRAG avg**: {sum(g_times)/len(g_times):.1f}s | ")
        lines.append(f"**VectorRAG avg**: {sum(v_times)/len(v_times):.1f}s\n\n")

        lines.append("---\n\n## Detailed Results\n\n")
        for i, r in enumerate(results):
            lines.append(f"### {i+1}. {r['query']}\n\n")
            lines.append(f"- Type: `{r['type']}` | Expected: `{r['expected_best']}`\n\n")
            lines.append(f"#### GraphRAG ({r['graphrag'].get('method', '?')}, {r['graphrag']['time']:.1f}s)\n\n")
            lines.append(f"> {r['graphrag']['answer'][:500]}\n\n")
            lines.append(f"#### Vector RAG ({r['vector_rag']['time']:.1f}s)\n\n")
            lines.append(f"> {r['vector_rag']['answer'][:500]}\n\n")
            lines.append("---\n\n")

        return "".join(lines)

    def save_report(self, report: str, output_path: str):
        """Write the comparison report to disk."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        logger.info("Report saved to %s", out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="GraphRAG vs Vector RAG — Comparison Engine"
    )
    parser.add_argument("--graphrag-root", default=".")
    parser.add_argument("--vector-store", default="data/vector_store")
    parser.add_argument("--collection", default="graphrag_lab_corpus")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--output", default="docs/comparison_report.md")
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="[comparator] %(asctime)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    comparator = RAGComparator(
        graphrag_root=args.graphrag_root,
        vector_store=args.vector_store,
        collection_name=args.collection,
        embedding_model=args.embedding_model,
        device=args.device,
    )

    logger.info("Running comparison (%d queries)...", len(DEFAULT_QUERIES))
    results = comparator.run_comparison()

    report = comparator.generate_report(results)
    comparator.save_report(report, args.output)

    # Print quick summary
    print("\n" + "=" * 60)
    print("QUICK SUMMARY")
    print("=" * 60)
    for r in results:
        g_t = r["graphrag"]["time"]
        v_t = r["vector_rag"]["time"]
        print(f"  [{r['type']:10s}]  GraphRAG={g_t:.1f}s  Vector={v_t:.1f}s  → {r['expected_best']}")


if __name__ == "__main__":
    main()
