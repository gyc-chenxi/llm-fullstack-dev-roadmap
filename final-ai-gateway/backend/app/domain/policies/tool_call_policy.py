"""
Tool call policy — governs tool execution safety and limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolCallPolicy:
    allowed_tools: set[str] = field(default_factory=set)
    blocked_tools: set[str] = field(default_factory=set)
    max_concurrent_tools: int = 3
    require_confirmation: bool = False

    def is_allowed(self, tool_name: str) -> bool:
        if tool_name in self.blocked_tools:
            return False
        if self.allowed_tools and tool_name not in self.allowed_tools:
            return False
        return True