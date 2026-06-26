"""
Timeout policy — defines timeout values for different operation types.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TimeoutPolicy:
    chat_timeout_ms: int = 60000
    rag_timeout_ms: int = 90000
    agent_timeout_ms: int = 300000
    tool_call_timeout_ms: int = 30000
    llm_call_timeout_ms: int = 60000
    queue_wait_timeout_ms: int = 120000
    connection_timeout_ms: int = 10000

    def for_request_type(self, request_type: str) -> int:
        mapping = {
            "chat": self.chat_timeout_ms,
            "rag": self.rag_timeout_ms,
            "agent": self.agent_timeout_ms,
        }
        return mapping.get(request_type, self.chat_timeout_ms)