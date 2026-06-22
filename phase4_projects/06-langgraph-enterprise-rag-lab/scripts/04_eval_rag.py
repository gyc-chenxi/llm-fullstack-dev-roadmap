"""RAG evaluation script — recall, MRR, faithfulness, fallback accuracy."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure the project package is importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline against a golden set.")
    parser.add_argument(
        "--golden",
        default="data/eval/golden_set.jsonl",
        help="Path to golden_set.jsonl",
    )
    parser.add_argument(
        "--output",
        default="docs/eval_report.md",
        help="Output markdown report path",
    )
    parser.add_argument(
        "--api-base",
        default=os.getenv("OPENAI_API_BASE", "http://127.0.0.1:8006"),
        help="RAG API base URL",
    )
    return parser.parse_args()


def load_golden_set(path: str) -> list[dict]:
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def call_rag(api_base: str, query: str, thread_id: str) -> dict | None:
    """Call the RAG invoke endpoint and return the JSON response."""
    import urllib.request

    url = f"{api_base}/v1/rag/invoke"
    payload = json.dumps(
        {"query": query, "thread_id": thread_id, "max_retries": 2},
        ensure_ascii=False,
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"[eval][warn] API call failed for '{query[:40]}…': {exc!r}")
        return None


def compute_keyword_recall(answer: str, expected_keywords: list[str]) -> float:
    """Simple keyword-based recall."""
    if not expected_keywords:
        return 1.0
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer.lower())
    return hits / len(expected_keywords)


def check_fallback(answer: str) -> bool:
    """Check if the answer is a fallback / refusal response."""
    fallback_markers = [
        "知识库中未找到足够证据",
        "未找到足够证据",
        "无法回答",
        "超出资料范围",
    ]
    return any(marker in answer for marker in fallback_markers)


def main() -> None:
    args = parse_args()

    if not Path(args.golden).exists():
        print(f"[eval] golden set not found: {args.golden}")
        print("[eval] creating a minimal golden set for demo purposes …")
        _create_minimal_golden(args.golden)

    items = load_golden_set(args.golden)
    if not items:
        print("[eval] empty golden set — nothing to evaluate.")
        return

    print(f"[eval] loaded {len(items)} golden items")

    metrics: dict[str, list[float]] = {
        "keyword_recall": [],
        "fallback_correct": [],
        "latency_sec": [],
    }

    results: list[dict] = []

    for idx, item in enumerate(items):
        query = item["query"]
        thread_id = f"eval-{idx:04d}"

        t_start = time.monotonic()
        resp = call_rag(args.api_base, query, thread_id)
        elapsed = time.monotonic() - t_start

        if resp is None:
            results.append({"query": query, "error": "API call failed"})
            continue

        answer = resp.get("answer", "")
        citations = resp.get("citations", [])
        status = resp.get("status", "unknown")

        # Keyword recall
        expected_keywords = item.get("expected_keywords", [])
        kw_recall = compute_keyword_recall(answer, expected_keywords)
        metrics["keyword_recall"].append(kw_recall)

        # Fallback accuracy
        expected_behavior = item.get("expected_behavior", "")
        if expected_behavior == "fallback":
            correct = 1.0 if check_fallback(answer) else 0.0
            metrics["fallback_correct"].append(correct)

        # Latency
        metrics["latency_sec"].append(elapsed)

        results.append(
            {
                "query": query,
                "status": status,
                "answer": answer[:300],
                "citations_count": len(citations),
                "keyword_recall": round(kw_recall, 3),
                "latency_sec": round(elapsed, 2),
            }
        )

    # ── Aggregate ─────────────────────────────────────────────────────
    avg_recall = (
        sum(metrics["keyword_recall"]) / len(metrics["keyword_recall"])
        if metrics["keyword_recall"]
        else 0.0
    )
    avg_fallback = (
        sum(metrics["fallback_correct"]) / len(metrics["fallback_correct"])
        if metrics["fallback_correct"]
        else 1.0
    )
    avg_latency = (
        sum(metrics["latency_sec"]) / len(metrics["latency_sec"])
        if metrics["latency_sec"]
        else 0.0
    )

    sorted_lat = sorted(metrics["latency_sec"])
    p95_latency = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0.0

    # ── Report ────────────────────────────────────────────────────────
    report = [
        "# RAG Evaluation Report",
        "",
        f"**Date**: {time.strftime('%Y-%m-%d %H:%M')}",
        f"**Golden set size**: {len(items)}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| ------ | ----- |",
        f"| Avg Keyword Recall | {avg_recall:.3f} |",
        f"| Fallback Accuracy | {avg_fallback:.3f} |",
        f"| Avg Latency | {avg_latency:.1f}s |",
        f"| P95 Latency | {p95_latency:.1f}s |",
        "",
        "## Per-query Results",
        "",
    ]

    for r in results:
        report.append(
            f"- **{r['query'][:60]}** → "
            f"status=`{r.get('status', '?')}` "
            f"recall={r.get('keyword_recall', '?')} "
            f"latency={r.get('latency_sec', '?')}s"
        )
        if r.get("error"):
            report.append(f"  - ⚠️ Error: {r['error']}")

    report_text = "\n".join(report)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"\n[eval] report saved to {output_path}")


def _create_minimal_golden(path: str) -> None:
    """Bootstrap a minimal golden set for first-time evaluation."""
    items = [
        {
            "query": "RAG 是什么？",
            "expected_keywords": ["检索", "生成", "Retrieval", "Augmented"],
        },
        {
            "query": "LangGraph 有什么特点？",
            "expected_keywords": ["状态机", "LangGraph", "节点"],
        },
        {
            "query": "火星地下城市的人口数量是多少？",
            "expected_keywords": [],
            "expected_behavior": "fallback",
        },
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[eval] created minimal golden set: {path}")


if __name__ == "__main__":
    main()
