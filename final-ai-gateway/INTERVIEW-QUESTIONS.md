# AI-Gateway 面试高频问题

## 问题 1：为什么 LangChain 不直接裸连模型？GatewayChatModel 解决了什么问题？

### 面试回答框架

**核心观点**：LangChain 是应用编排层，不是服务治理层。如果让 LangChain 直接调用底层模型 API，会缺失限流、熔断、追踪、队列等企业级能力。

### 详细展开

**1. LangChain 的角色定位**

LangChain 的设计目标是让开发者方便地组合 prompt → model → parser chain。它的 `BaseChatModel` 只关心"发请求、收回复"，不关心：
- 并发控制了没有？会不会把本地模型打崩？
- 输出质量检测了没有？乱码/复读是否需要熔断？
- 有没有 trace？能不能断线恢复？

**2. GatewayChatModel 的设计**

我实现了一个 `GatewayChatModel(BaseChatModel)`，它包装了底层 LLM Client，并注入三个治理组件：

```python
class GatewayChatModel(BaseChatModel):
    llm_client: LLMClientPort        # 底层模型客户端
    admission_controller: AdmissionController  # 准入控制
    output_guard: OutputGuard         # 输出质量检测
    circuit_breaker: CircuitBreaker   # 熔断器
```

调用链路：
```
LangChain Chain/Agent
    ↓
GatewayChatModel._astream()
    ↓
1. AdmissionController.evaluate()   → 判断是否放行/排队/拒绝
2. LLMClientPort.chat_completion()  → 实际调用模型
3. OutputGuard.check() per token    → 实时检测乱码/复读
4. CircuitBreaker.call()            → 熔断保护
```

**3. 面试加分点**

- "我理解 LangChain 和 Gateway 的分工——前者编排业务逻辑，后者治理服务质量"
- "我的 GatewayChatModel 可以同时用于 Chat、RAG、Agent 三种场景，LangChain 里的任何 chain 都能接入治理层"
- "如果没有这一层，每个 chain 都要自己处理限流、熔断、trace——重复而且容易遗漏"

---

## 问题 2：Agent 如何防止无限循环？

### 面试回答框架

**核心观点**：Agent 不能做成黑盒 while loop。我实现了 4 层防护：状态机显式化、AgentLoopGuard 多维度限制、Checkpoint 可恢复、Circuit Breaker 兜底。

### 详细展开

**1. 显式状态机而非黑盒循环**

Agent 执行是预定义的 6 节点图，不是 while True:

```
START → classify_task → retrieve_context → plan_tool_calls
     → execute_tools → generate_answer → verify_answer → END
```

每个节点都有明确的输入/输出，不会出现"模型自己决定要不要再调一次"的不可控情况。

**2. AgentLoopGuard 多维度限制**

```python
class AgentLoopGuard:
    max_steps: int = 20              # 总步数限制
    max_llm_calls: int = 15          # LLM 调用次数限制
    max_tool_calls: int = 10         # 工具调用次数限制
    tool_timeout_ms: int = 30000     # 单次工具超时
    same_tool_repeat_limit: int = 3  # 同一工具连续调用上限
    same_message_repeat_limit: int = 5 # 同一消息重复上限
    max_runtime_seconds: int = 300   # 总运行时间限制
```

每个 node 执行前都会检查：
- `check_step()` — 步数是否超限
- `check_llm_call()` — LLM 调用是否超限
- `check_tool_call()` — 工具调用是否超限 + 是否陷入重复调用

**3. Checkpoint + Resume**

每个 node 执行后写 checkpoint 到 Redis。如果 Agent 因 loop guard 触发而终止，可以从最后一个合法 checkpoint 恢复，而不是从头再来。

**4. Circuit Breaker 兜底**

如果同一类型的 Agent 任务反复触发 loop guard，Circuit Breaker 会直接 OPEN，拒绝后续请求，防止资源浪费。

### 面试加分点

- "我设计的是显式状态机，每个 node 的转换条件是预定义的"
- "AgentLoopGuard 不是简单的 max_steps，而是多维度的——步数、LLM 调用、工具调用、重复检测、总时间"
- "我用了 Redis Checkpoint，断了可以恢复，不是一次性执行"

---

## 问题 3：KV Token Budget 如何估算？为什么用这个公式？

### 面试回答框架

**核心观点**：不能只看请求数，要看显存压力。KV Cache 是推理服务的第一瓶颈。我用一个近似公式估算每个请求的 KV Cache 占用，累计判断是否超过安全阈值。

### 详细展开

**1. KV Cache 估算公式**

```
kv_bytes = 2 × layers × seq_len × num_kv_heads × head_dim × dtype_bytes
```

逐项解释：
- `2` = K 和 V 两份 cache
- `layers` = Transformer 层数（Qwen 2.5 7B 有 28 层）
- `seq_len` = prompt_tokens + max_new_tokens（预估总序列长度）
- `num_kv_heads` = GQA/MQA 下的 KV head 数（不等于 attention head 数）
- `head_dim` = 每个 head 的维度
- `dtype_bytes` = 量化精度（Q4_K_M → 实际存储为 fp16 KV cache，所以是 2 bytes）

**2. Admission Decision 逻辑**

```python
def evaluate(prompt_tokens, max_new_tokens):
    budget = estimator.estimate(prompt_tokens, max_new_tokens)

    if active_slots >= max_slots:
        return QUEUE  # 没有空闲 slot

    if active_kv_bytes + budget.kv_bytes > safe_kv_budget:
        return QUEUE  # KV Cache 不够

    if memory_pressure_high:
        return DEGRADE  # 系统内存紧张

    return ADMIT
```

**3. Agent 特殊处理**

Agent 可能多步调用 LLM，不能只看一次调用：

```
agent_peak_budget = single_call_budget × max_planned_llm_calls
```

更稳的做法是每个 node 调模型前重新做 admission check。

**4. 为什么不用 GPU 显存监控？**

因为我们是 MacBook + llama.cpp 的场景，没有 nvidia-smi。用公式估算是跨平台的、零依赖的。即使有 GPU 显存监控，公式估算也是一个有价值的"软限制"，可以在打到硬件限制之前就排队。

### 面试加分点

- "我理解 KV Cache 是推理服务的第一瓶颈，不是算力"
- "我的 Admission Controller 不是简单的 max_concurrency，而是基于显存压力估算"
- "Agent 请求有特殊处理——峰值预算是单次调用的 N 倍"
- "这个公式可以适配任何模型，只需要改 num_layers/num_kv_heads/head_dim/dtype_bytes"

---

## 附加问题

### Q4: SSE 断线恢复怎么实现？

每个 SSE event 带 `event_id`，所有事件写 Redis Stream。客户端断开后重连：
```
GET /api/v1/chat/{request_id}/resume?last_event_id=42
```
后端从 Redis Stream 读取 event_id > 42 的事件补发，然后继续实时流。

### Q5: Redis ZSET 优先级队列怎么排序？

`score = priority × 10^15 + timestamp × 10^6`。优先级（1-10）主导排序，时间戳用于同优先级 FCFS。使用 `ZPOPMIN` 原子弹出队。

### Q6: Hybrid RAG 检索怎么做？

向量检索（ChromaDB cosine similarity）+ BM25 稀疏检索，按 `0.6 × vector_score + 0.4 × bm25_normalized_score` 加权融合，最后 Reranker 二次排序。
