#!/usr/bin/env python3
"""GraphRAG Query Demo — Global Search + Local Search.

Supports:
- Interactive single query (--method global|local)
- Batch evaluation against a curated test set (--batch)

Usage:
    # Single query
    PYTHONPATH=. python scripts/04_query_demo.py --method global --query "What themes are covered?"
    PYTHONPATH=. python scripts/04_query_demo.py --method local --query "How are BERT and GPT related?"

    # Batch evaluation (8 curated queries)
    PYTHONPATH=. python scripts/04_query_demo.py --batch
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Curated test queries covering different RAG strengths
# ---------------------------------------------------------------------------
TEST_QUERIES = [
    {
        "query": "What is the Transformer architecture and how does self-attention work?",
        "type": "factual",
        "expected_best": "vector",
    },
    {
        "query": "How are Transformer, BERT, GPT-3, and LoRA related in technical lineage?",
        "type": "multi_hop",
        "expected_best": "graphrag",
    },
    {
        "query": "What is the relationship between attention mechanisms and parameter-efficient fine-tuning?",
        "type": "multi_hop",
        "expected_best": "graphrag",
    },
    {
        "query": "How do knowledge distillation and quantization relate as model compression techniques?",
        "type": "multi_hop",
        "expected_best": "graphrag",
    },
    {
        "query": "What are the major themes and topics covered in this knowledge base?",
        "type": "global",
        "expected_best": "graphrag",
    },
    {
        "query": "What are the key research trends in large language models in recent years?",
        "type": "global",
        "expected_best": "graphrag",
    },
    {
        "query": "Summarize the evolution of neural network architectures from RNNs to Transformers.",
        "type": "summary",
        "expected_best": "graphrag",
    },
    {
        "query": "What is the BERT masked language model pre-training objective?",
        "type": "factual",
        "expected_best": "vector",
    },
]


def run_search(root: str, method: str, query: str) -> tuple:
    """Execute a single graphrag query and return (answer, elapsed_seconds)."""
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
        stderr_preview = result.stderr.strip()[:500]
        return f"[ERROR] {stderr_preview}", elapsed

    return result.stdout.strip(), elapsed


def main():
    parser = argparse.ArgumentParser(
        description="GraphRAG Query Demo — Global Search + Local Search"
    )
    parser.add_argument("--method", choices=["global", "local"], default="global",
                        help="Search method: global (community-level) or local (entity-centric)")
    parser.add_argument("--query", type=str, default=None,
                        help="Single query string (interactive if omitted)")
    parser.add_argument("--batch", action="store_true",
                        help="Run all 8 curated test queries")
    parser.add_argument("--root", default=".",
                        help="GraphRAG project root (default: .)")
    args = parser.parse_args()

    root = str(Path(args.root).resolve())

    # Verify index exists
    output_dir = Path(root) / "data" / "output"
    if not output_dir.exists() or not list(output_dir.glob("*.parquet")):
        print("[query] WARNING: No parquet files in data/output/")
        print("[query] The index pipeline may not have completed.")
        print("[query] Run: make run-index")
        print()

    # --- Batch mode ---
    if args.batch:
        print("=" * 70)
        print(f"P8 GraphRAG Batch Evaluation — {len(TEST_QUERIES)} queries")
        print("=" * 70)

        for i, tq in enumerate(TEST_QUERIES):
            # Choose method based on query type
            if tq["type"] in ("multi_hop", "factual"):
                method = "local"
            else:
                method = "global"

            answer, elapsed = run_search(root, method, tq["query"])
            border = "-" * 70

            print(f"\n{border}")
            print(f"[{i+1}/{len(TEST_QUERIES)}] {tq['type'].upper()} | method={method} | {elapsed:.1f}s | expected_best={tq['expected_best']}")
            print(f"Q: {tq['query']}")
            print(f"A: {answer[:400]}{'...' if len(answer) > 400 else ''}")
            print(border)

        print("\n[query] Batch evaluation complete.")
        return 0

    # --- Single-query mode ---
    query = args.query
    if not query:
        try:
            query = input("Enter query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[query] cancelled.")
            return 0

    if not query:
        print("[query] No query provided. Use --query '...' or --batch")
        return 1

    answer, elapsed = run_search(root, args.method, query)

    border = "=" * 70
    print(f"\n{border}")
    print(f"Method : {args.method.upper()} SEARCH")
    print(f"Time   : {elapsed:.1f}s")
    print(f"Query  : {query}")
    print(border)
    print(answer)
    print(border)


if __name__ == "__main__":
    main()
