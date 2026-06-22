"""Observability event types used across the RAG pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal


EventStatus = Literal["running", "done", "failed", "fallback", "no_context"]


@dataclass
class NodeEvent:
    """A single node execution event."""

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
    """Convenience helper to create a standardised event dict."""
    return {
        "node": node,
        "status": status,
        "timestamp": time.monotonic(),
        **kwargs,
    }
