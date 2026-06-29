# ⭐ ModelRouter: 多模型动态路由引擎

## 核心理念

> 一个 API 接入 5+ 厂商 + 本地模型，前端无感知切换。这不是普通的 if-else 路由，而是一个**策略模式 + 责任链 + 熔断器**组合驱动的状态决策引擎。

## 架构设计

```
请求到达
    │
    ▼
┌─────────────────────────────────────────────┐
│       1. 请求上下文标准化                      │
│       model=?, complexity=?, latency_budget=? │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│       2. 构建 Fallback Chain                  │
│       [primary → step1 → step2 → ... → last] │
│       从 fallback_policy.yaml 加载             │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│       3. 遍历 Fallback Chain                  │
│                                              │
│   for each model in chain:                   │
│       ├─ 熔断器检查 → OPEN? → 跳过            │
│       ├─ 策略1: TaskBasedRouter               │
│       │   SIMPLE→最便宜 / COMPLEX→最强        │
│       ├─ 策略2: LatencyAwareRouter             │
│       │   排除 P99 > max_latency 的模型        │
│       ├─ 策略3: LoadBalancingRouter            │
│       │   多副本选 in-flight 最少的            │
│       └─ 任一策略选中 → 返回 endpoint          │
│                                              │
│   全部跳过 → raise NoSuitableModelError       │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│       4. 记录 RoutingDecision 到 Trace        │
│       → 请求 ID、选中模型、决策原因、延迟、      │
│         预估成本（Dashboard 可查）              │
└─────────────────────────────────────────────┘
```

## 核心代码结构 (backend/app/domain/services/router.py)

```python
class ModelRouter:
    """
    Flow:
      ① Normalize request → extract routing hints (model, complexity, latency budget)
      ② Primary strategy: try to route to the requested model
      ③ If primary fails → walk fallback chain with each step:
           a. Check circuit breaker for target model
           b. Apply each RoutingStrategy
           c. If endpoint selected → validate with admission controller
           d. On success → record routing decision & return
      ④ If ALL fallbacks exhausted → raise NoSuitableModelError
    """

    async def route(self, request_context: dict) -> tuple[ModelEndpoint, RoutingDecision]:
        start_time = time.monotonic()
        fallback_chain = self._build_fallback_chain(request_context.get("model"))

        for model_name in fallback_chain:
            endpoint = self.endpoints.get(model_name)
            if not endpoint:
                continue

            # Circuit breaker check
            cb = self.circuit_breakers.get(model_name)
            if cb and cb.state == "open":
                continue

            # Apply routing strategies
            for strategy in self.strategies:
                selected, reason = await strategy.select(request_context, [endpoint])
                if selected:
                    return selected, RoutingDecision(...)

        raise NoSuitableModelError(...)
```

## 三种路由策略

| 策略 | 类名 | 适用场景 | 决策逻辑 |
|:-----|:-----|:---------|:---------|
| 任务类型路由 | `TaskBasedRouter` | 简单/复杂请求分类 | SIMPLE→最便宜，COMPLEX→最强 |
| 延迟感知路由 | `LatencyAwareRouter` | 响应时间敏感场景 | 排除 P99 超预算的模型 |
| 负载均衡路由 | `LoadBalancingRouter` | 多副本部署 | 选 in-flight 最少的 replica |

## Fallback 链示例 (fallback_policy.yaml)

```yaml
models:
  gpt-4o:
    fallback_chain:
      - model: gpt-4o-mini
        reason: "同厂商阶梯降级，成本降低 20x"
        condition: "any_error"
      - model: deepseek-chat
        reason: "跨厂商 failover，不同 API 减少共同故障"
        condition: "timeout_or_5xx"
      - model: local-qwen
        reason: "本地模型兜底，不依赖外网"
        condition: "any_error"
```

## 生产级考虑

- **预热路由**：启动时发送健康探针到所有 endpoint，标记不可用者
- **自适应降级**：连续 3 次超时 → 自动将该模型优先级降级，7 分钟后恢复
- **成本感知**：相同能力等级下优先选便宜的（gpt-4o-mini < deepseek < claude-haiku）
- **可观测性**：每次路由决策写入 Trace，Dashboard 上能看到"为什么选了这个模型"