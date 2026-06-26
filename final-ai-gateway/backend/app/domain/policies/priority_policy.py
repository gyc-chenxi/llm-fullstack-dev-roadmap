"""
Priority policy — determines request priority based on request type and tenant.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..value_objects.priority import Priority


@dataclass
class PriorityPolicy:
    agent_priority_boost: int = -2
    rag_priority_boost: int = -1
    tenant_overrides: dict[str, int] = None

    def __post_init__(self):
        if self.tenant_overrides is None:
            self.tenant_overrides = {}

    def compute(self, request_type: str, tenant_id: str = "default") -> Priority:
        base = Priority.normal()
        if tenant_id in self.tenant_overrides:
            base = Priority(self.tenant_overrides[tenant_id])
        if request_type == "agent":
            base = Priority(max(1, base.value + self.agent_priority_boost))
        elif request_type == "rag":
            base = Priority(max(1, base.value + self.rag_priority_boost))
        return base