#!/usr/bin/env python3
"""GraphRAG vs Vector RAG — Quantitative Comparison.

Runs the same 8 queries against both GraphRAG and Vector RAG,
recording timing and answer quality. Outputs a Markdown report.

Usage:
    PYTHONPATH=. python scripts/06_compare_rag.py \
        --graphrag-root . \
        --vector-store data/vector_store \
        --embedding-model BAAI/bge-m3 \
        --output docs/comparison_report.md
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

from sentence_transformers import SentenceTransformer
import chromadb


TEST_QUERIES = [
    {"query": "What is the Transformer architecture?", "type": "factual", "expected_best": "vector"},
    {"query": "How are Transformer, BERT, GPT, and LoRA related?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What is the relationship between attention and parameter-efficient fine-tuning?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "How do knowledge distillation and quantization relate?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What are the major themes in this knowledge base?", "type": "global", "expected_best": "graphrag"},
    {"query": "What are key research trends in large language models?", "type": "global", "expected_best": "graphrag"},
    {"query": "Summarize the evolution from RNNs to Transformers.", "type": "summary", "expected_best": "graphrag"},
    {"query": "What is masked language modeling in BERT?", "type": "factual", "expected_best": "vector"},
]


def query_graphrag(root: str, query: str, qtype: str) -> tuple:
    """Run a GraphRAG query. Returns (answer, elapsed_seconds, method_used)."""
    method = "local" if qtype in ("multi_hop", "factual") else "global"
    cmd = [
        sys.executable, "-m", "graphrag", "query",
        "--root", root,
        "--method", method,
        query,
    ]
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    elapsed = time.time() - t0

    if result.returncode != 0:
        return f"[ERROR] {result.stderr.strip()[:300]}", elapsed, method

    return result.stdout.strip(), elapsed, method


def query_vector_rag(collection, model, query: str, top_k: int = 5) -> tuple:
    """Run a Vector RAG query. Returns (context_string, elapsed_seconds)."""
    t0 = time.time()
    q_emb = model.encode([query], normalize_embeddings=True)
    results = collection.query(query_embeddings=q_emb.tolist(), n_results=top_k)
    elapsed = time.time() - t0

    docs = results["documents"][0]
    distances = results["distances"][0]
    parts = []
    for j, (doc, dist) in enumerate(zip(docs, distances)):
        score = 1.0 - dist  # cosine distance → similarity
        parts.append(f"[Chunk {j+1}, score={score:.3f}] {doc[:300]}...")
    return "\n\n".join(parts), elapsed


def main():
    parser = argparse.ArgumentParser(
        description="GraphRAG vs Vector RAG — Quantitative Comparison"
    )
    parser.add_argument("--graphrag-root", default=".")
    parser.add_argument("--vector-store", default="data/vector_store")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--collection", default="graphrag_lab_corpus")
    parser.add_argument("--output", default="docs/comparison_report.md")
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()

    graphrag_root = str(Path(args.graphrag_root).resolve())

    # --- Load embedding model ---
    print(f"[Compare] Loading embedding model {args.embedding_model} on {args.device}...")
    model = SentenceTransformer(args.embedding_model, device=args.device)
    print(f"[Compare] Model ready. dim={model.get_sentence_embedding_dimension()}")

    # --- Load Chroma ---
    print(f"[Compare] Loading Chroma vector store from {args.vector_store} ...")
    client = chromadb.PersistentClient(path=args.vector_store)
    try:
        collection = client.get_collection(args.collection)
        print(f"[Compare] Vector store: {collection.count()} vectors in '{args.collection}'")
    except Exception as e:
        print(f"[Compare] ERROR: cannot load collection '{args.collection}': {e}")
        print("[Compare] Run: make run-vector-rag  first.")
        sys.exit(1)

    # --- Run all queries ---
    results = []
    for i, tq in enumerate(TEST_QUERIES):
        print(f"\n  [{i+1}/{len(TEST_QUERIES)}] {tq['type']}: {tq['query'][:80]}...")

        # GraphRAG
        try:
            g_answer, g_time, g_method = query_graphrag(graphrag_root, tq["query"], tq["type"])
            print(f"    GraphRAG ({g_method}): {g_time:.1f}s, {len(g_answer)} chars")
        except Exception as e:
            g_answer, g_time, g_method = f"[ERROR] {e}", 0, "local"
            print(f"    GraphRAG: ERROR — {e}")

        # Vector RAG
        try:
            v_answer, v_time = query_vector_rag(collection, model, tq["query"])
            print(f"    VectorRAG:         {v_time:.1f}s, {len(v_answer)} chars")
        except Exception as e:
            v_answer, v_time = f"[ERROR] {e}", 0
            print(f"    VectorRAG: ERROR — {e}")

        results.append({
            "query": tq["query"],
            "type": tq["type"],
            "expected_best": tq["expected_best"],
            "graphrag_method": g_method,
            "graphrag_time": g_time,
            "graphrag_answer": g_answer[:500],
            "vector_time": v_time,
            "vector_answer": v_answer[:500],
        })

    # --- Generate Markdown report ---
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# GraphRAG vs Vector RAG — Comparison Report\n\n",
        f"**Date**: {now}\n\n",
        f"**Corpus**: {collection.count()} chunks from `data/input/`\n\n",
        f"**GraphRAG LLM**: DeepSeek API (`deepseek-chat`)\n\n",
        f"**Vector RAG**: Chroma + `{args.embedding_model}`\n\n",
        f"**Embedding dim**: {model.get_sentence_embedding_dimension()}\n\n",
        "---\n\n",
        "## Executive Summary\n\n",
        "| # | Type | Expected Best | GraphRAG | VectorRAG | Winner |\n",
        "|:-:|:-----|:------------:|:--------:|:---------:|:------:|\n",
    ]

    for i, r in enumerate(results):
        g_str = f"{r['graphrag_time']:.1f}s ({r['graphrag_method']})"
        v_str = f"{r['vector_time']:.1f}s"
        if r["expected_best"] == "graphrag":
            winner = "🏆 GraphRAG"
        elif r["expected_best"] == "vector":
            winner = "🏆 VectorRAG"
        else:
            winner = "—"
        lines.append(f"| {i+1} | {r['type']} | {r['expected_best']} | {g_str} | {v_str} | {winner} |\n")

    # Stats summary
    g_times = [r["graphrag_time"] for r in results]
    v_times = [r["vector_time"] for r in results]
    lines.append(f"\n**GraphRAG** avg: {sum(g_times)/len(g_times):.1f}s | ")
    lines.append(f"**VectorRAG** avg: {sum(v_times)/len(v_times):.1f}s\n\n")

    lines.append("---\n\n## Detailed Results\n\n")
    for i, r in enumerate(results):
        lines.append(f"### {i+1}. {r['query']}\n\n")
        lines.append(f"- **Type**: `{r['type']}` | **Expected best**: `{r['expected_best']}`\n\n")
        lines.append(f"#### GraphRAG ({r['graphrag_method']}, {r['graphrag_time']:.1f}s)\n\n")
        lines.append(f"> {r['graphrag_answer']}\n\n")
        lines.append(f"#### Vector RAG ({r['vector_time']:.1f}s)\n\n")
        lines.append(f"> {r['vector_answer']}\n\n")
        lines.append("---\n\n")

    # Write report
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"\n[Compare] ✓ Report saved to {out_path}")

    # Console summary
    print("\n" + "=" * 65)
    print("QUICK SUMMARY")
    print("=" * 65)
    for r in results:
        print(f"  [{r['type']:10s}]  GraphRAG={r['graphrag_time']:.1f}s  Vector={r['vector_time']:.1f}s  → {r['expected_best']}")


if __name__ == "__main__":
    main()
