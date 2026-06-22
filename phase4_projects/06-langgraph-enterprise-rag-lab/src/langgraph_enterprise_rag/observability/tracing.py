"""Simple tracing utilities for LangGraph node execution timing."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator


@dataclass
class Span:
    """A lightweight execution span for a single node."""

    node: str
    start: float = field(default_factory=time.monotonic)
    end: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def elapsed(self) -> float:
        if self.end > 0:
            return self.end - self.start
        return time.monotonic() - self.start

    def finish(self) -> dict:
        self.end = time.monotonic()
        return {
            "node": self.node,
            "elapsed_ms": round(self.elapsed * 1000, 2),
            **self.metadata,
        }


@contextmanager
def trace_node(node: str, **metadata) -> Generator[Span, None, None]:
    """Context manager that produces a Span for the given node.

    Usage:
        with trace_node("retrieve", doc_count=10) as span:
            # … do work …
            span.metadata["doc_count"] = len(docs)
    """
    span = Span(node=node, metadata=dict(metadata))
    try:
        yield span
    finally:
        span.finish()
