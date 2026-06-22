"""Golden set loader — reads JSONL evaluation data."""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_GOLDEN_PATH = "data/eval/golden_set.jsonl"


def load_golden_set(path: str | None = None) -> list[dict]:
    """Load the evaluation golden set from a JSONL file.

    Each line should be a JSON object with at least:
      - query (str)
      - expected_keywords (list[str])
      - expected_sources (list[str], optional)
      - expected_behavior (str, optional: "fallback" or "answer")

    Returns:
        List of golden items.
    """
    target = Path(path or DEFAULT_GOLDEN_PATH)

    if not target.exists():
        return _default_golden_set()

    items: list[dict] = []
    with target.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return items or _default_golden_set()


def _default_golden_set() -> list[dict]:
    """Return a built-in minimal golden set for bootstrapping."""
    return [
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
