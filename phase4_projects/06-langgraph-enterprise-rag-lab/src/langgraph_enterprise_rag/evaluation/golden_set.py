"""
Golden Set 加载器
====================

评估黄金数据集 — JSONL 格式，每行一个测试用例：
  - query: 用户问题
  - expected_keywords: 答案中应出现的关键词列表
  - expected_sources: 应引用到的文档来源（可选）
  - expected_behavior: "fallback"（应拒绝回答）或 "answer"（应有答案）

数据流：data/eval/golden_set.jsonl → JSONL 逐行解析 → [golden_item]
如果 JSONL 不存在，回退到内置最小数据集（3 个测试用例）。
"""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_GOLDEN_PATH = "data/eval/golden_set.jsonl"


def load_golden_set(path: str | None = None) -> list[dict]:
    """加载评估黄金数据集。

    Args:
        path: JSONL 文件路径，默认 data/eval/golden_set.jsonl

    Returns:
        黄金测试用例列表。文件不存在时返回内置默认集合。
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
    """内置最小黄金数据集（无需外部 JSONL 即可运行评估）。"""
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
