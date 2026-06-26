"""
Estimates KV cache pressure for a given request using the KV formula:
kv_bytes = 2 × layers × seq_len × num_kv_heads × head_dim × dtype_bytes
"""

from __future__ import annotations

from ..entities.model_profile import ModelProfile
from ..value_objects.token_budget import TokenBudget


class TokenBudgetEstimator:
    def __init__(self, profile: ModelProfile):
        self._profile = profile

    def estimate(self, prompt_tokens: int, max_new_tokens: int = 2048) -> TokenBudget:
        seq_len = prompt_tokens + max_new_tokens
        kv_bytes = self._profile.per_token_bytes * seq_len
        return TokenBudget(
            prompt_tokens=prompt_tokens,
            max_new_tokens=max_new_tokens,
            estimated_kv_bytes=kv_bytes,
        )

    def estimate_agent(self, single_call_budget: TokenBudget, max_llm_calls: int) -> TokenBudget:
        total_kv = single_call_budget.estimated_kv_bytes * max_llm_calls
        return TokenBudget(
            prompt_tokens=single_call_budget.prompt_tokens * max_llm_calls,
            max_new_tokens=single_call_budget.max_new_tokens * max_llm_calls,
            estimated_kv_bytes=total_kv,
        )

    @property
    def safe_kv_budget(self) -> float:
        return self._profile.safe_kv_budget_bytes