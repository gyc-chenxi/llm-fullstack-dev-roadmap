"""
Model profile capturing known constants of a served model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelProfile:
    model_name: str
    model_path: str = ""
    backend: str = "llamacpp"
    context_length: int = 8192
    max_slots: int = 4
    num_layers: int = 28
    num_kv_heads: int = 4
    head_dim: int = 128
    dtype_bytes: int = 2
    safe_kv_budget_bytes: int = 8_589_934_592
    cache_prompt: bool = True
    description: str = ""

    @property
    def per_token_bytes(self) -> float:
        return 2.0 * self.num_layers * self.num_kv_heads * self.head_dim * self.dtype_bytes
