"""
节点事件与 Span 追踪
======================

可观测性系统的基础原语：

  NodeEvent: 单节点执行事件的标准化结构
  make_event(): 便捷构造事件 dict
  Span: 轻量级执行 Span（带计时）
  trace_node(): context manager 式节点追踪

事件格式（贯穿整个 RAGState.events 和 SSE 推送）：
  { node, status, timestamp, ...node-specific-payload }
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator, Literal


EventStatus = Literal["running", "done", "failed", "fallback", "no_context"]


@dataclass
class NodeEvent:
    """单个节点执行事件。"""

    node: str
    status: EventStatus
    timestamp: float = field(default_factory=time.monotonic)
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "node": self.node,
            "status": self.status,
            "timestamp": self.timestamp,
            **self.payload,
        }


def make_event(node: str, status: EventStatus, **kwargs) -> dict:
    """便捷构造标准化事件 dict。"""
    return {
        "node": node,
        "status": status,
        "timestamp": time.monotonic(),
        **kwargs,
    }


@dataclass
class Span:
    """轻量级执行 Span，用于追踪单节点耗时。"""

    node: str
    start: float = field(default_factory=time.monotonic)
    end: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def elapsed(self) -> float:
        """已执行时间（秒）。"""
        if self.end > 0:
            return self.end - self.start
        return time.monotonic() - self.start

    def finish(self) -> dict:
        """结束 Span 并返回汇总数据。"""
        self.end = time.monotonic()
        return {
            "node": self.node,
            "elapsed_ms": round(self.elapsed * 1000, 2),
            **self.metadata,
        }


@contextmanager
def trace_node(node: str, **metadata) -> Generator[Span, None, None]:
    """节点追踪 context manager。

    用法：
        with trace_node("retrieve", doc_count=10) as span:
            docs = hybrid_search(query)
            span.metadata["doc_count"] = len(docs)
    """
    span = Span(node=node, metadata=dict(metadata))
    try:
        yield span
    finally:
        span.finish()
