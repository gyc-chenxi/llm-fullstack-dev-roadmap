# ⭐ Circuit Breaker: 熔断器状态机

## 核心理念

> 熔断不是"出错就关"，而是一个**三态状态机**——在"正常"、"降级"、"试探恢复"之间自动转换。目的是防止级联故障：如果下游模型已经挂了，不要再往里发请求加重负担。

## 三态状态机

```
    ┌─────────────────────────────────────┐
    │           CLOSED (关闭)               │
    │  正常状态, 请求全部放行                │
    │  错误计数: failure_count++            │
    │                                     │
    │  当 failure_count >= threshold       │
    │  ──────────────────────────────►     │
    │                                     │
    └─────────────────────────────────────┘
                      │
                      │ failure_threshold=5
                      ▼
    ┌─────────────────────────────────────┐
    │           OPEN (断开)                 │
    │  拒绝所有请求 (抛出异常)               │
    │  启动 recovery_timeout 计时器          │
    │                                     │
    │  计时器到时                          │
    │  ──────────────────────────────►     │
    └─────────────────────────────────────┘
                      │
                      │ recovery_timeout=30s
                      ▼
    ┌─────────────────────────────────────┐
    │         HALF_OPEN (半开)              │
    │  放行 1 个探测请求                     │
    │                                     │
    │  成功 → 回到 CLOSED (重置计数)         │
    │  失败 → 回到 OPEN (延长等待)           │
    └─────────────────────────────────────┘
```

## 核心代码结构 (backend/app/domain/services/circuit_breaker.py)

```python
class CircuitBreaker:
    """三态熔断器 — 保护下游模型不被无效请求压垮。

    与普通 try-except 的区别:
    - try-except: 错了再处理 (反映式)
    - circuit-breaker: 预测会错就不发请求 (主动式)
    """

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    half_open_requests: int = 0

    def call(self, func, *args, **kwargs):
        # 状态检查
        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitState.HALF_OPEN
                self.half_open_requests = 0
            else:
                raise CircuitBreakerOpenError()

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_requests >= self.half_open_max_requests:
                raise CircuitBreakerOpenError()

        # 执行实际调用
        try:
            self.half_open_requests += 1
            result = func(*args, **kwargs)
            self._on_success()       # 成功 → 关闭熔断器
            return result
        except Exception as e:
            self._on_failure()       # 失败 → 计数+1
            raise e

    def _on_success(self):
        """探针成功: 说明下游已恢复, 关闭熔断器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0

    def _on_failure(self):
        """探针失败: 继续熔断"""
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

## Gateway 中的熔断场景

| 熔断触发器 | 阈值 | 恢复策略 | 熔断期间表现 |
|:----------|:----|:---------|:------------|
| 连续 5 次请求超时 | `failure_threshold=5` | 30s 后尝试恢复 | 路由跳过该模型 → fallback |
| 模型返回乱码/空回复 | `output_guard` 触发 | 60s 后尝试 | 消息: "模型异常,已切换备用" |
| 连续 3 次 Rate Limited | `rate_limit_threshold=3` | 120s (估计限流窗口) | 同厂商降级到更小模型 |
| 持续高延迟 (P99>10s) | `latency_threshold_p99=10000` | 渐进恢复 | 不熔断, 但降低该模型优先级 |

## 集成到 Router 中的流程

```python
async def route(self, request_context):
    for model_name in fallback_chain:
        endpoint = self.endpoints.get(model_name)
        cb = self.circuit_breakers.get(model_name)

        # Step 1: 熔断器检查 (零开销, O(1))
        if cb and cb.state == "open":
            logger.info("Skipping %s (circuit OPEN, retry in %ds)",
                        model_name, cb.recovery_timeout_sec)
            continue

        # Step 2: 尝试路由
        selected, reason = await strategy.select(request_context, [endpoint])
        if selected:
            # Step 3: 通过熔断器包裹实际调用
            # router 不直接 call, 而是把 cb 传给调用层
            return selected, decision

    raise NoSuitableModelError(...)
```

## 与普通 try-except 的对比

```
场景: 模型 API 连续返回 503

普通 try-except:
    请求 1 → 503 → 重试 → 503 → 放弃
    请求 2 → 503 → 重试 → 503 → 放弃
    请求 3 → 503 → 重试 → 503 → 放弃
    ... 每次请求都在浪费连接池和等待时间

Circuit Breaker:
    请求 1 → 503 → failure_count=1
    请求 2 → 503 → failure_count=2
    请求 3 → 503 → failure_count=3
    请求 4 → 503 → failure_count=4
    请求 5 → 503 → failure_count=5 → OPEN!
    请求 6 → CircuitBreakerOpenError (0ms) → 立即 fallback
    请求 7 → CircuitBreakerOpenError (0ms) → 立即 fallback
    ... 30秒后 → HALF_OPEN → 放行探针 → 成功 → CLOSED
```

## 生产级考虑

- **指数退避恢复**：每次连续熔断后，recovery_timeout 指数增长 (30s→60s→120s→...)
- **熔断事件写入 Trace**：Dashboard 上能看到"哪个模型什么时候被熔断、为什么"
- **手动重置信道**：Admin API 提供 `POST /admin/circuit-breaker/{model}/reset`
- **慢调用检测**：不是只有错误才熔断——P99 > 5s 持续 1 分钟也触发降级