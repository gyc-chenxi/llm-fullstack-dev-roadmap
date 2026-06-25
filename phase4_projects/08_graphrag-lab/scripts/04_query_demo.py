"""
GraphRAG 查询演示
===================

GraphRAG Global Search（社区级摘要）和 Local Search（实体中心遍历）的交互式和批量查询演示。

数据流：
  query → graphrag query --method local|global → subprocess
    → stdout(answer) → print formatted output

测试查询集（8 条）：
  factual(2): 单事实检索 — Vector RAG 更快
  multi_hop(3): 跨实体关系推理 — GraphRAG 更全面
  global/summary(3): 全文总结 — GraphRAG 社区报告更丰富

用法：
  PYTHONPATH=. python scripts/04_query_demo.py --method local --query "What is LoRA?"
  PYTHONPATH=. python scripts/04_query_demo.py --batch
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

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
    """执行一次 graphrag 查询。

    Returns:
        (answer_text, elapsed_seconds)
    """
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

    output_dir = Path(root) / "data" / "output"
    if not output_dir.exists() or not list(output_dir.glob("*.parquet")):
        print("[query] WARNING: No parquet files in data/output/")
        print("[query] The index pipeline may not have completed.")
        print("[query] Run: make run-index")
        print()

    # 批量评估
    if args.batch:
        print("=" * 70)
        print(f"P8 GraphRAG Batch Evaluation — {len(TEST_QUERIES)} queries")
        print("=" * 70)

        for i, tq in enumerate(TEST_QUERIES):
            method = "local" if tq["type"] in ("multi_hop", "factual") else "global"

            answer, elapsed = run_search(root, method, tq["query"])
            border = "-" * 70

            print(f"\n{border}")
            print(f"[{i+1}/{len(TEST_QUERIES)}] {tq['type'].upper()} | method={method} | {elapsed:.1f}s | expected_best={tq['expected_best']}")
            print(f"Q: {tq['query']}")
            print(f"A: {answer[:400]}{'...' if len(answer) > 400 else ''}")
            print(border)

        print("\n[query] Batch evaluation complete.")
        return 0

    # 单查询模式
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
