"""
Admission controller — decides whether to admit, queue, reject, or degrade a request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..entities.model_profile import ModelProfile
from ..entities.slot import Slot, SlotStatus
from ..value_objects.admission_decision import AdmissionDecision, DecisionType
from ..value_objects.token_budget import TokenBudget
from .token_budget_estimator import TokenBudgetEstimator


@dataclass
class AdmissionController:
    estimator: TokenBudgetEstimator
    slots: list[Slot] = field(default_factory=list)
    active_kv_bytes: float = 0.0
    queue_depth: int = 0
    memory_pressure_high: bool = False

    def evaluate(self, prompt_tokens: int, max_new_tokens: int = 2048,
                 max_context_tokens: Optional[int] = None) -> AdmissionDecision:
        if max_context_tokens and prompt_tokens > max_context_tokens:
            return AdmissionDecision(
                decision=DecisionType.LONG_CONTEXT,
                reason=f"prompt_tokens {prompt_tokens} > max_context {max_context_tokens}",
            )

        budget = self.estimator.estimate(prompt_tokens, max_new_tokens)
        idle_slots = [s for s in self.slots if s.status == SlotStatus.IDLE]

        if not idle_slots:
            return AdmissionDecision(
                decision=DecisionType.QUEUE,
                reason="no idle slots",
                estimated_kv_bytes=budget.estimated_kv_bytes,
                queue_position=self.queue_depth + 1,
            )

        if self.active_kv_bytes + budget.estimated_kv_bytes > self.estimator.safe_kv_budget:
            return AdmissionDecision(
                decision=DecisionType.QUEUE,
                reason="kv budget exceeded",
                estimated_kv_bytes=budget.estimated_kv_bytes,
                queue_position=self.queue_depth + 1,
            )

        if self.memory_pressure_high:
            return AdmissionDecision(
                decision=DecisionType.DEGRADE,
                reason="high memory pressure",
                estimated_kv_bytes=budget.estimated_kv_bytes,
            )

        slot = idle_slots[0]
        return AdmissionDecision(
            decision=DecisionType.ADMIT,
            reason="ok",
            slot_id=slot.slot_id,
            estimated_kv_bytes=budget.estimated_kv_bytes,
        )