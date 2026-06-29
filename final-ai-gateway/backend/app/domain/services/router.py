"""
Multi-Model Dynamic Router — intelligent request dispatching across model providers.

This is THE core differentiator of the AI-Gateway: it decides WHICH model handles
WHICH request, WHEN to fallback, and HOW to fail gracefully.

Architecture pattern: Strategy + Chain of Responsibility + Circuit Breaker
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. Domain Model — the routing primitives
# ──────────────────────────────────────────────

class TaskComplexity(Enum):
    """Classifies request complexity for intelligent routing."""
    SIMPLE = "simple"           # Translation, summarization → cheap model
    MEDIUM = "medium"           # Code generation, analysis → balanced model
    COMPLEX = "complex"         # Reasoning, planning → strongest model
    CRITICAL = "critical"       # Production-critical → highest reliability


@dataclass
class ModelEndpoint:
    """A single model deployment (cloud API or local server)."""
    name: str                    # e.g. "gpt-4o", "deepseek-chat", "local-qwen"
    provider: str                # "openai" | "deepseek" | "qwen" | "claude" | "llamacpp" | "vllm"
    model_id: str                # Provider-specific model identifier
    base_url: str                # API endpoint URL
    priority: int                # Lower = preferred first
    max_tokens: int              # Context window limit
    cost_per_1k_input: float     # USD per 1K input tokens
    cost_per_1k_output: float    # USD per 1K output tokens
    avg_latency_p50_ms: float    # Historical P50 latency (updated by monitor)
    avg_latency_p99_ms: float    # Historical P99 latency
    is_available: bool = True    # Health check result
    current_load: int = 0        # In-flight requests
    capabilities: set[str] = field(default_factory=lambda: {"chat"})
    # e.g. {"chat", "vision", "function_calling", "streaming", "json_mode"}


@dataclass
class RoutingDecision:
    """Immutable record of a routing decision for audit/tracing."""
    request_id: str
    original_model: str
    selected_model: str
    fallback_chain: list[str]    # Full chain tried
    decision_reason: str         # e.g. "primary_available", "timeout_fallback", "cost_optimized"
    routing_latency_ms: float
    estimated_cost: float

    def to_trace(self) -> dict:
        return {
            "request_id": self.request_id,
            "routing": {
                "original": self.original_model,
                "selected": self.selected_model,
                "chain": self.fallback_chain,
                "reason": self.decision_reason,
                "latency_ms": self.routing_latency_ms,
                "estimated_cost_usd": self.estimated_cost,
            },
        }


# ──────────────────────────────────────────────
# 2. Routing Strategies (Strategy Pattern)
# ──────────────────────────────────────────────

class RoutingStrategy(ABC):
    """Abstract strategy for selecting a model endpoint."""

    @abstractmethod
    async def select(
        self,
        request_context: dict,
        endpoints: list[ModelEndpoint],
    ) -> tuple[ModelEndpoint | None, str]:
        ...


class TaskBasedRouter(RoutingStrategy):
    """
    Strategy 1: Route by task complexity.

    SIMPLE → cheapest available
    MEDIUM → balanced (gpt-4o-mini level)
    COMPLEX → strongest available
    CRITICAL → highest reliability + multi-fallback
    """

    COMPLEXITY_MODEL_MAP = {
        TaskComplexity.SIMPLE:   {"min_capability": "chat",          "max_cost": 0.5},
        TaskComplexity.MEDIUM:   {"min_capability": "chat",          "max_cost": 2.0},
        TaskComplexity.COMPLEX:  {"min_capability": "function_calling", "max_cost": 15.0},
        TaskComplexity.CRITICAL: {"min_capability": "function_calling", "max_cost": 30.0},
    }

    async def select(
        self,
        request_context: dict,
        endpoints: list[ModelEndpoint],
    ) -> tuple[ModelEndpoint | None, str]:
        complexity = request_context.get("complexity", TaskComplexity.MEDIUM)
        config = self.COMPLEXITY_MODEL_MAP[complexity]

        eligible = [
            ep for ep in endpoints
            if ep.is_available
            and config["min_capability"] in ep.capabilities
            and ep.cost_per_1k_input <= config["max_cost"]
        ]

        if not eligible:
            return None, f"no_eligible_model_for_{complexity.value}"

        # For SIMPLE/MEDIUM: pick cheapest
        # For COMPLEX/CRITICAL: pick most capable (highest cost within budget)
        if complexity in (TaskComplexity.SIMPLE, TaskComplexity.MEDIUM):
            selected = min(eligible, key=lambda e: e.cost_per_1k_input)
        else:
            selected = max(eligible, key=lambda e: e.cost_per_1k_input)

        return selected, f"task_based_{complexity.value}"


class LatencyAwareRouter(RoutingStrategy):
    """
    Strategy 2: Route by latency budget.

    If request has a max_latency_ms constraint, exclude models whose
    P99 exceeds it. Among survivors, pick the cheapest.
    """

    async def select(
        self,
        request_context: dict,
        endpoints: list[ModelEndpoint],
    ) -> tuple[ModelEndpoint | None, str]:
        max_latency = request_context.get("max_latency_ms")
        if max_latency is None:
            return None, "no_latency_constraint"

        eligible = [
            ep for ep in endpoints
            if ep.is_available
            and ep.avg_latency_p99_ms <= max_latency
        ]

        if not eligible:
            return None, "all_models_exceed_latency_budget"

        selected = min(eligible, key=lambda e: e.cost_per_1k_input)
        return selected, "latency_aware"


class LoadBalancingRouter(RoutingStrategy):
    """
    Strategy 3: Load-balance across equivalent endpoints.

    Used when multiple endpoints serve the same model (e.g., multi-replica).
    Picks the one with fewest in-flight requests.
    """

    async def select(
        self,
        request_context: dict,
        endpoints: list[ModelEndpoint],
    ) -> tuple[ModelEndpoint | None, str]:
        target_model = request_context.get("model")

        eligible = [
            ep for ep in endpoints
            if ep.is_available and ep.name == target_model
        ]

        if not eligible:
            return None, f"no_available_replica_for_{target_model}"

        # Least-loaded first
        selected = min(eligible, key=lambda e: e.current_load)
        return selected, "load_balanced"


# ──────────────────────────────────────────────
# 3. Fallback Chain (Chain of Responsibility)
# ──────────────────────────────────────────────

@dataclass
class FallbackPolicy:
    """
    Defines the fallback chain for a given primary model.

    Example YAML equivalent:
    ```yaml
    models:
      gpt-4o:
        fallback_chain:
          - model: gpt-4o-mini
            reason: "同厂商阶梯降级，成本降低 20x"
            condition: "any_error"
          - model: deepseek-chat
            reason: "跨厂商 failover"
            condition: "timeout_or_5xx"
          - model: local-qwen
            reason: "本地模型兜底，无需网络"
            condition: "any_error"
    ```
    """
    primary_model: str
    fallbacks: list[FallbackStep]


@dataclass
class FallbackStep:
    model: str
    reason: str
    condition: str                   # "any_error" | "timeout" | "5xx" | "rate_limited"
    timeout_override_ms: int | None = None


# ──────────────────────────────────────────────
# 4. Main Router Engine
# ──────────────────────────────────────────────

class ModelRouter:
    """
    The central routing engine. Coordinates strategies + fallback chain.

    Flow:
      1. Normalize request → extract routing hints (model, complexity, latency budget)
      2. Primary strategy: try to route to the requested model
      3. If primary fails → walk fallback chain with each step:
           a. Check circuit breaker for target model
           b. Apply routing strategy
           c. If endpoint selected → validate with admission controller
           d. On success → record routing decision & return
      4. If ALL fallbacks exhausted → raise NoSuitableModelError

    This is the difference between "an API wrapper" and "an AI-Gateway" —
    production routing is not if-else, it's a stateful decision engine.
    """

    def __init__(
        self,
        endpoints: list[ModelEndpoint],
        fallback_policies: dict[str, FallbackPolicy],
        strategies: list[RoutingStrategy] | None = None,
        circuit_breaker_registry: dict[str, Any] | None = None,
    ):
        self.endpoints = {ep.name: ep for ep in endpoints}
        self.fallback_policies = fallback_policies
        self.strategies = strategies or [
            TaskBasedRouter(),
            LatencyAwareRouter(),
            LoadBalancingRouter(),
        ]
        self.circuit_breakers = circuit_breaker_registry or {}
        self._routing_cache: dict[str, RoutingDecision] = {}
        logger.info(
            "ModelRouter initialized: %d endpoints, %d fallback policies, %d strategies",
            len(self.endpoints), len(self.fallback_policies), len(self.strategies),
        )

    async def route(
        self,
        request_context: dict,
    ) -> tuple[ModelEndpoint, RoutingDecision]:
        """
        Route a request to the optimal model endpoint.

        Args:
            request_context: Dict with keys:
                - request_id: str (required)
                - model: str | None (requested model name, optional)
                - complexity: TaskComplexity (default: MEDIUM)
                - max_latency_ms: int | None
                - capabilities: set[str] (required capabilities)

        Returns:
            Tuple of (selected ModelEndpoint, RoutingDecision)

        Raises:
            NoSuitableModelError: When all paths exhausted
        """
        start_time = time.monotonic()
        request_id = request_context.get("request_id", "unknown")
        requested_model = request_context.get("model")

        # Build fallback chain starting from requested model
        fallback_chain: list[str] = []

        if requested_model and requested_model in self.fallback_policies:
            policy = self.fallback_policies[requested_model]
            fallback_chain = [policy.primary_model] + [f.model for f in policy.fallbacks]
        else:
            # No explicit policy — try all available endpoints ordered by priority
            fallback_chain = [
                ep.name for ep in sorted(
                    self.endpoints.values(), key=lambda e: e.priority
                )
            ]

        attempted_models: list[str] = []

        for model_name in fallback_chain:
            endpoint = self.endpoints.get(model_name)
            if not endpoint:
                continue

            # Circuit breaker check
            cb = self.circuit_breakers.get(model_name)
            if cb and cb.state == "open":
                logger.warning("Circuit OPEN for %s, skipping", model_name)
                attempted_models.append(f"{model_name}(circuit_open)")
                continue

            # Apply routing strategies
            for strategy in self.strategies:
                selected, reason = await strategy.select(
                    {**request_context, "model": model_name},
                    [endpoint],
                )
                if selected:
                    # Charge one token for the circuit breaker probe
                    if cb:
                        try:
                            cb.call(lambda: None)
                        except Exception:
                            continue

                    routing_latency = (time.monotonic() - start_time) * 1000
                    decision = RoutingDecision(
                        request_id=request_id,
                        original_model=requested_model or "auto",
                        selected_model=selected.name,
                        fallback_chain=fallback_chain,
                        decision_reason=reason,
                        routing_latency_ms=round(routing_latency, 2),
                        estimated_cost=self._estimate_cost(selected, request_context),
                    )

                    logger.info(
                        "Route[%s] %s → %s (reason=%s, chain=%s, latency=%.1fms)",
                        request_id[:8], decision.original_model, selected.name,
                        reason, "→".join(fallback_chain), routing_latency,
                    )
                    return selected, decision

            attempted_models.append(model_name)

        # All paths exhausted — critical failure
        routing_latency = (time.monotonic() - start_time) * 1000
        raise NoSuitableModelError(
            request_id=request_id,
            attempted_models=attempted_models,
            routing_latency_ms=round(routing_latency, 2),
            fallback_chain=fallback_chain,
        )

    def _estimate_cost(self, endpoint: ModelEndpoint, ctx: dict) -> float:
        """Rough cost estimation before the actual call."""
        input_tokens = ctx.get("estimated_input_tokens", 1000)
        output_tokens = ctx.get("estimated_output_tokens", 500)
        return (
            input_tokens / 1000 * endpoint.cost_per_1k_input
            + output_tokens / 1000 * endpoint.cost_per_1k_output
        )

    def update_latency_stats(self, model_name: str, latency_ms: float):
        """Feed back observed latency for adaptive routing."""
        endpoint = self.endpoints.get(model_name)
        if not endpoint:
            return
        # Exponential moving average for P50
        alpha = 0.3
        endpoint.avg_latency_p50_ms = (
            alpha * latency_ms + (1 - alpha) * endpoint.avg_latency_p50_ms
        )
        # Track P99 via reservoir sampling (simplified)
        endpoint.avg_latency_p99_ms = max(endpoint.avg_latency_p99_ms * 0.95, latency_ms * 0.05)


class NoSuitableModelError(Exception):
    """Raised when ALL routing paths and fallbacks are exhausted."""

    def __init__(
        self,
        request_id: str,
        attempted_models: list[str],
        routing_latency_ms: float,
        fallback_chain: list[str],
    ):
        self.request_id = request_id
        self.attempted_models = attempted_models
        self.routing_latency_ms = routing_latency_ms
        self.fallback_chain = fallback_chain
        super().__init__(
            f"Request {request_id}: no suitable model after trying "
            f"{' → '.join(attempted_models)} "
            f"(full chain: {' → '.join(fallback_chain)})"
        )


# ──────────────────────────────────────────────
# 5. Usage Example
# ──────────────────────────────────────────────

async def demo_router_usage():
    """Illustrates how the router plugs into the Gateway startup."""

    # Configure endpoints (loaded from models.yaml at startup)
    endpoints = [
        ModelEndpoint(
            name="gpt-4o", provider="openai",
            model_id="gpt-4o-2024-11-20",
            base_url="https://api.openai.com/v1",
            priority=1, max_tokens=128000,
            cost_per_1k_input=0.0025, cost_per_1k_output=0.01,
            avg_latency_p50_ms=800, avg_latency_p99_ms=3000,
            capabilities={"chat", "vision", "function_calling", "streaming", "json_mode"},
        ),
        ModelEndpoint(
            name="deepseek-chat", provider="deepseek",
            model_id="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            priority=2, max_tokens=64000,
            cost_per_1k_input=0.0005, cost_per_1k_output=0.002,
            avg_latency_p50_ms=1200, avg_latency_p99_ms=5000,
            capabilities={"chat", "function_calling", "streaming"},
        ),
        ModelEndpoint(
            name="local-qwen", provider="llamacpp",
            model_id="qwen2.5-7b-instruct-q4_k_m",
            base_url="http://127.0.0.1:8080/v1",
            priority=3, max_tokens=8192,
            cost_per_1k_input=0.0, cost_per_1k_output=0.0,
            avg_latency_p50_ms=200, avg_latency_p99_ms=500,
            capabilities={"chat", "streaming"},
        ),
    ]

    # Fallback policy: gpt-4o → gpt-4o-mini → deepseek → local
    fallback_policies = {
        "gpt-4o": FallbackPolicy(
            primary_model="gpt-4o",
            fallbacks=[
                FallbackStep("gpt-4o-mini", "同厂商降级", "any_error"),
                FallbackStep("deepseek-chat", "跨厂商 failover", "timeout_or_5xx"),
                FallbackStep("local-qwen", "本地模型兜底", "any_error"),
            ],
        ),
    }

    router = ModelRouter(
        endpoints=endpoints,
        fallback_policies=fallback_policies,
    )

    # Route a simple translation request
    endpoint, decision = await router.route({
        "request_id": "req_abc123",
        "model": "gpt-4o",
        "complexity": TaskComplexity.SIMPLE,
        "capabilities": {"chat"},
    })

    print(f"Routed to: {endpoint.name}")
    print(f"Decision: {decision.decision_reason}")
    print(f"Fallback chain: {' → '.join(decision.fallback_chain)}")
    print(f"Routing latency: {decision.routing_latency_ms}ms")
