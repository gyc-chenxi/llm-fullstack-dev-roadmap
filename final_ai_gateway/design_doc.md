# 一、项目定位

## 项目名称

```text
AI-Gateway: Lightweight Enterprise LLM / RAG / Agent Serving Governance Gateway
```

中文名：

```text
企业级轻量化大模型智能路由与 Agent 治理网关系统
```

## 技术目标

它不是一个普通 LLM Web UI，也不是一个简单 LangChain Demo，而是一个 **本地 LLM Serving + LangChain RAG + LangGraph Agent 的统一治理层**。

新的整体链路：

```text
Vue 3 Dashboard
    ↓
FastAPI Gateway
    ↓
Request Router
    ├── Chat Completion Runtime
    ├── LangChain RAG Runtime
    ├── LangGraph Agent Runtime
    └── Benchmark / Eval Runtime
    ↓
Admission Controller / Slot Controller / Fault Engine / Metrics Engine / Trace Engine
    ↓
Redis Priority Queue + Stream Session Store + Trace Store + Metrics Store
    ↓
llama.cpp server / Ollama / OpenAI-compatible backend
    ↓
Local GGUF / Ollama Model / Cloud Model，可选
```

## 关键分层原则

```text
LangChain / LangGraph 不是 Gateway 的替代品。

LangChain / LangGraph = 应用编排层：RAG、Tool Calling、Agent 状态机
AI-Gateway = 模型服务治理层：并发、队列、熔断、SSE、Token Budget、Trace、Dashboard
llama.cpp / Ollama = 底层模型执行层
```

也就是说，生产叙事应该是：

```text
业务应用 / Agent Runtime
    ↓
AI-Gateway
    ↓
底层模型服务
```

而不是让每个 LangChain chain 直接裸连本地模型。

------

# 二、最终可展示能力

你最后应该能展示这些功能：

```text
1. 10 / 50 / 100 并发压测
2. 普通 Chat、RAG Query、Agent Run 三类请求都进入统一治理层
3. 请求不会直接压垮本地模型，而是进入优先级队列
4. 实时显示 TTFT、Tokens/s、队列等待时间、熔断次数
5. RAG 请求显示 retrieval latency、top-k chunks、rerank score、citation accuracy
6. Agent 请求显示 LangGraph node 状态、tool calls、失败重试、checkpoint/resume
7. 长 system prompt 命中 prefix cache 后 TTFT 下降
8. SSE 断线后可按 request_id + last_event_id 恢复
9. 模型乱码、复读、不可见字符、输出过长时自动熔断降级
10. Dashboard 上能看到 active slots、queued requests、memory pressure、trace timeline
```

------

# 三、底层模型服务建议

## 优先推荐：llama.cpp server

原因：llama.cpp server 更适合你做 AI Infra 练习，因为它暴露了更底层的 slots、metrics、prompt cache、tokenize、OpenAI-compatible API 等能力。

建议启动方式：

```bash
llama-server \
  -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  -c 8192 \
  -np 4 \
  --metrics \
  --slots \
  --cache-prompt \
  --slot-save-path ./runtime/slot_cache
```

解释：

```text
-c 8192              上下文窗口
-np 4                并行 slots 数
--metrics            暴露 Prometheus 风格指标
--slots              暴露 slot 监控
--cache-prompt       启用 prompt cache
--slot-save-path     保存/恢复 slot prompt cache
```

## Ollama 作为备选

Ollama 的 API 更简单，适合做普通 chat/generate，但它对 slot、prompt cache、metrics 的底层可控性弱一些，不如 llama.cpp 适合这个 AI-Gateway 项目。

## LangChain / LangGraph 接入位置

建议新增一个 `agent_runtime` 层：

```text
FastAPI API
  ↓
Application Use Case
  ↓
LangChainRagRuntime / LangGraphAgentRuntime
  ↓
Gateway LLM Client Port
  ↓
Admission Controller
  ↓
llama.cpp / Ollama
```

这样 LangChain 内部不会直接调模型，而是通过 Gateway 的 LLM client port 统一进入模型治理。

------

# 四、DDD 四层架构目录设计

建议继续严格按 DDD 四层做，和你之前 AIpolish / L-Port 重构经验保持一致。

## 总目录

```text
ai-gateway/
  backend/
    app/
      interface/
      application/
      domain/
      infrastructure/
      main.py
      config.py
    tests/
    scripts/
    pyproject.toml
  frontend/
    src/
    package.json
  docker-compose.yml
  README.md
  docs/
```

------

## 1. Domain 层：纯业务规则，不依赖 FastAPI / Redis / LangChain / httpx

```text
backend/app/domain/
  entities/
    inference_request.py
    rag_request.py
    agent_run.py
    stream_session.py
    slot.py
    model_profile.py
    queue_ticket.py
    fault_event.py
    trace_run.py
    tool_call.py

  value_objects/
    token_budget.py
    priority.py
    admission_decision.py
    stream_event.py
    prefix_hash.py
    latency_metrics.py
    citation.py
    retrieval_hit.py
    agent_state_snapshot.py

  services/
    token_budget_estimator.py
    admission_controller.py
    token_bucket_limiter.py
    slot_allocator.py
    long_context_planner.py
    prefix_cache_policy.py
    stream_health_detector.py
    output_guard.py
    circuit_breaker.py
    rag_quality_guard.py
    agent_loop_guard.py

  policies/
    priority_policy.py
    degradation_policy.py
    retry_policy.py
    timeout_policy.py
    tool_call_policy.py
    citation_policy.py

  ports/
    llm_client.py
    queue_repository.py
    metrics_repository.py
    slot_repository.py
    prompt_cache_repository.py
    tokenizer_port.py
    system_probe.py
    rag_runtime_port.py
    agent_runtime_port.py
    retriever_port.py
    tool_registry_port.py
    trace_repository.py
```

### 新增核心实体

#### RagRequest

表示一次检索增强问答请求：

```text
request_id
tenant_id
question
knowledge_base_id
retrieval_top_k
rerank_top_k
required_citations
stream
created_at
```

#### AgentRun

表示一次 Agent 执行：

```text
run_id
tenant_id
agent_type
goal
state
max_steps
current_step
tool_calls
checkpoint_id
created_at
updated_at
```

#### TraceRun

表示一次可观测执行链路：

```text
trace_id
request_id
run_type: chat / rag / agent / benchmark
spans
latency_ms
token_usage
retrieval_hits
tool_calls
errors
final_status
```

#### ToolCall

表示一次工具调用：

```text
tool_call_id
run_id
tool_name
input_schema
input_payload
output_payload
latency_ms
status
error
```

------

## 2. Application 层：用例编排

```text
backend/app/application/
  use_cases/
    submit_chat_use_case.py
    stream_chat_use_case.py
    resume_stream_use_case.py
    admit_request_use_case.py
    dequeue_request_use_case.py
    cancel_request_use_case.py
    run_benchmark_use_case.py
    collect_metrics_use_case.py

    submit_rag_query_use_case.py
    stream_rag_answer_use_case.py
    evaluate_rag_use_case.py

    submit_agent_run_use_case.py
    stream_agent_run_use_case.py
    resume_agent_run_use_case.py
    cancel_agent_run_use_case.py

  dto/
    chat_request_dto.py
    chat_response_dto.py
    rag_request_dto.py
    rag_response_dto.py
    agent_run_dto.py
    stream_resume_dto.py
    benchmark_config_dto.py
    metrics_snapshot_dto.py
    trace_snapshot_dto.py

  orchestrators/
    inference_orchestrator.py
    rag_orchestrator.py
    agent_orchestrator.py
    benchmark_orchestrator.py
    queue_worker.py
    metrics_collector.py
    trace_collector.py
```

### SubmitRagQueryUseCase

```text
1. 接收用户问题和 knowledge_base_id
2. 调 tokenizer 估算 query + prompt tokens
3. 调 AdmissionController 判断是否放行
4. 调 RagRuntimePort 执行 LangChain RAG
5. 边生成边写 StreamSession checkpoint
6. 同时写 TraceRun：retrieval、rerank、LLM answer、citation
7. 返回 request_id / stream_url / trace_id
```

### SubmitAgentRunUseCase

```text
1. 接收用户目标 goal 和 agent_type
2. 创建 AgentRun
3. 调 AdmissionController 做模型资源准入
4. 调 AgentRuntimePort 执行 LangGraph 状态机
5. 每个节点写 checkpoint 和 trace span
6. 每个 tool call 经过 ToolCallPolicy 和 timeout 控制
7. 返回 run_id / stream_url / trace_id
```

------

## 3. Infrastructure 层：外部系统适配

```text
backend/app/infrastructure/
  llm_clients/
    llamacpp_client.py
    ollama_client.py
    openai_compatible_client.py
    gateway_chat_model.py

  langchain_runtime/
    langchain_rag_runtime.py
    langchain_retriever_adapter.py
    langchain_tool_adapter.py
    langchain_callback_handler.py

  langgraph_runtime/
    graph_factory.py
    rag_agent_graph.py
    code_agent_graph.py
    redis_checkpointer.py
    graph_event_mapper.py

  retrieval/
    document_loader.py
    text_splitter.py
    vector_store_repo.py
    bm25_retriever.py
    hybrid_retriever.py
    reranker.py

  redis/
    redis_priority_queue.py
    redis_stream_session_repo.py
    redis_slot_repo.py
    redis_metrics_repo.py
    redis_token_bucket.py
    redis_trace_repo.py

  tokenizer/
    llamacpp_tokenizer.py
    tiktoken_estimator.py
    fallback_estimator.py

  probes/
    macos_memory_probe.py
    llamacpp_metrics_probe.py
    ollama_probe.py

  prompt_cache/
    llamacpp_slot_cache_repo.py
    prefix_hash_repo.py

  sse/
    sse_event_store.py
    event_id_generator.py

  benchmark/
    locust_runner.py
    asyncio_load_generator.py
    rag_eval_runner.py
```

### gateway_chat_model.py

它的作用是把 LangChain 的 ChatModel 调用转成 Gateway 内部 LLM Client 调用：

```text
LangChain Chain / Agent
    ↓
GatewayChatModel
    ↓
LLMClientPort
    ↓
AdmissionController + SlotAllocator
    ↓
llama.cpp / Ollama
```

这样你可以在简历里说清楚：

```text
我没有让 LangChain 直接裸连模型，而是实现了一个 Gateway-managed ChatModel adapter，
把 LangChain 调用纳入统一限流、熔断、追踪和 token budget 管理。
```

------

## 4. Interface 层：FastAPI + SSE + WebSocket

```text
backend/app/interface/
  http/
    routes_chat.py
    routes_rag.py
    routes_agent.py
    routes_metrics.py
    routes_slots.py
    routes_benchmark.py
    routes_trace.py
    routes_admin.py

  sse/
    stream_endpoint.py
    resume_endpoint.py
    agent_stream_endpoint.py

  websocket/
    metrics_ws.py
    trace_ws.py

  middlewares/
    request_id_middleware.py
    rate_limit_middleware.py
    error_boundary_middleware.py
```

### 建议接口

```text
POST /api/v1/chat
GET  /api/v1/chat/{request_id}/stream
GET  /api/v1/chat/{request_id}/resume?last_event_id=xxx
POST /api/v1/chat/{request_id}/cancel

POST /api/v1/rag/query
GET  /api/v1/rag/{request_id}/stream
POST /api/v1/rag/evaluate

POST /api/v1/agent/run
GET  /api/v1/agent/{run_id}/stream
GET  /api/v1/agent/{run_id}/resume?last_event_id=xxx
POST /api/v1/agent/{run_id}/cancel

GET  /api/v1/trace/{trace_id}
GET  /api/v1/metrics/snapshot
GET  /api/v1/metrics/live
GET  /api/v1/slots
POST /api/v1/benchmark/run
GET  /api/v1/benchmark/{run_id}
```

------

# 五、整体数据流

## 普通 Chat 请求链路

```text
用户提交 prompt
    ↓
FastAPI 接收 ChatRequest
    ↓
Tokenizer 估算 prompt tokens
    ↓
TokenBudgetEstimator 估算峰值 KV 压力
    ↓
AdmissionController 判断是否允许进入 active slots
    ↓
允许：分配 slot，调用 LLM streaming API
    ↓
不允许：写入 Redis Priority Queue
    ↓
SSE 向前端流式返回 token
    ↓
OutputGuard 实时检查乱码/复读/敏感词
    ↓
StreamSession checkpoint 写 Redis
    ↓
TraceRun 写入 token usage、latency、error
    ↓
请求结束，释放 slot，更新 metrics
```

## LangChain RAG 请求链路

```text
用户提交问题 + knowledge_base_id
    ↓
FastAPI 接收 RagRequest
    ↓
AdmissionController 做模型资源准入
    ↓
LangChainRagRuntime 启动
    ↓
Document Retriever 召回 top-k chunks
    ↓
Reranker 重排
    ↓
CitationPolicy 检查 evidence 是否足够
    ↓
GatewayChatModel 调用底层 LLM
    ↓
SSE 输出 token + retrieval events + citations
    ↓
TraceRun 记录 retrieval score、rerank score、LLM latency、citation accuracy
```

## LangGraph Agent 请求链路

```text
用户提交 goal
    ↓
FastAPI 接收 AgentRunRequest
    ↓
创建 AgentRun + TraceRun
    ↓
LangGraphAgentRuntime 执行 StateGraph
    ↓
每个 node 执行前检查 step limit / timeout / tool policy
    ↓
需要调用模型时走 GatewayChatModel
    ↓
需要调用工具时走 ToolRegistry + ToolCallPolicy
    ↓
每个 node 后写 checkpoint
    ↓
SSE 输出 node_start / tool_call / token / warning / node_end / done
    ↓
断线后可按 run_id + last_event_id 恢复
```

------

# 六、核心模块 1：动态显存流控与卡槽管理

## 设计目标

不要让普通 Chat、RAG、Agent 请求直接打到底层 LLM，而是在网关层先做 admission control。

你要控制的不是“真实显存分配”，而是一个**近似的 KV Token Budget**：

```text
当前所有 active requests 的预计 KV 占用
+
新请求预计峰值 KV 占用
<=
安全阈值
```

## KV Cache 估算公式

```text
kv_bytes = 2 × layers × seq_len × num_kv_heads × head_dim × dtype_bytes
```

其中：

```text
2 = K 和 V 两份
seq_len = prompt_tokens + max_new_tokens
num_kv_heads = GQA/MQA 下真实 KV head 数，不一定等于 attention heads
```

## Admission Decision 规则

```text
如果 prompt_tokens > max_context_tokens:
    进入 long_context_planner，压缩或切片

如果 active_slots >= max_slots:
    QUEUE

如果 active_kv_bytes + request_reserved_kv_bytes > safe_kv_budget:
    QUEUE

如果 tenant token bucket 不足:
    QUEUE 或 REJECT

如果系统 memory_pressure 高:
    DEGRADE 或 QUEUE

否则:
    ADMIT
```

## Agent 特殊准入规则

Agent 请求不能只看一次 LLM 调用，因为它可能多步循环：

```text
agent_peak_budget = estimated_single_call_budget × max_planned_llm_calls
```

更稳的策略是：

```text
1. AgentRun 先占用一个 execution ticket
2. 每次 node 调模型前重新做 admission check
3. 超过 max_steps 或 max_tokens 后强制停止
4. tool call 不占用 LLM slot，但占用 tool concurrency budget
```

------

# 七、核心模块 2：LangChain RAG Runtime

## 设计目标

把 LangChain RAG 纳入 Gateway 治理，而不是让 RAG demo 自己裸跑。

## RAG Runtime 结构

```text
LangChainRagRuntime
  ├── loader: 加载 md / txt / pdf
  ├── splitter: chunk size / overlap
  ├── embeddings: 本地或 API embedding
  ├── vector store: Chroma / FAISS / pgvector，可选
  ├── retriever: vector / bm25 / hybrid
  ├── reranker: cross-encoder 或规则版
  ├── answer chain: GatewayChatModel
  └── callback handler: 事件转 SSE + Trace
```

## 关键输出

RAG 不能只返回答案，必须返回：

```text
answer
citations
retrieved_docs
retrieval_scores
rerank_scores
latency_breakdown
trace_id
```

## RAG 质量守卫

```text
如果没有足够相关证据：拒答或请求更多上下文
如果答案没有 citation：标记 warning
如果 citation 不在 retrieved_docs 中：拦截
如果回答包含未被证据支持的强事实判断：标记 low_confidence
```

------

# 八、核心模块 3：LangGraph Agent Runtime

## 设计目标

把复杂 Agent 做成显式状态机，而不是一个黑盒 while loop。

## 推荐第一个 Agent Graph

```text
START
  ↓
classify_task
  ↓
retrieve_context
  ↓
plan_tool_calls
  ↓
execute_tool
  ↓
answer_or_continue
  ↓
verify_final_answer
  ↓
END
```

## AgentState

```python
from typing import TypedDict, Any

class AgentState(TypedDict):
    run_id: str
    goal: str
    task_type: str | None
    messages: list[dict]
    retrieved_docs: list[dict]
    planned_tools: list[str]
    tool_results: list[dict]
    draft_answer: str | None
    final_answer: str | None
    step: int
    errors: list[dict]
```

## Agent Loop Guard

```text
max_steps
max_llm_calls
max_tool_calls
tool_timeout_ms
same_tool_repeat_limit
same_message_repeat_limit
max_runtime_seconds
```

## Checkpoint / Resume

每个节点执行后都写 checkpoint：

```text
run_id
node_name
state_snapshot
event_id
created_at
```

断线后恢复：

```text
1. 按 run_id 找到 AgentRun
2. 读取最后 checkpoint
3. 回放 SSE missed events
4. 如果 graph 仍 active，继续执行
5. 如果 graph 已 failed，返回 structured error + fallback answer
```

------

# 九、核心模块 4：Long-Context Router 与 Prompt Cache

## 设计目标

解决两个问题：

```text
1. 重复 system prompt / agent instruction / tool schema 导致 TTFT 高
2. 长文档直接塞入上下文导致 prefill 慢、KV 爆炸
```

## Prefix Hash

对稳定前缀做 hash：

```text
prefix = system_prompt + shared_background + tool_instructions + graph_node_instruction
prefix_hash = sha256(normalized_prefix)
```

缓存元数据：

```json
{
  "prefix_hash": "abc123",
  "model": "qwen2.5-7b-q4",
  "slot_id": 2,
  "cache_file": "abc123_slot2.bin",
  "prefix_tokens": 1832,
  "last_used_at": "...",
  "hit_count": 17
}
```

## 长文本动态滑窗与检索压缩

```text
如果 prompt_tokens <= 0.6 * max_context:
    原样进入

如果 prompt_tokens <= max_context:
    保留 system prompt + 最近用户输入 + 文档摘要

如果 prompt_tokens > max_context:
    文档切块
    query-aware retrieval
    top-k chunks
    chunk summaries
    final compressed context
```

RAG 请求应优先走 retrieval compression，而不是盲目把全部文档塞进 prompt。

------

# 十、核心模块 5：熔断断连与 SSE 全链路防崩溃

## SSE Event 类型

```text
meta
token
heartbeat
retrieval_start
retrieval_result
rerank_result
tool_start
tool_end
node_start
node_end
warning
error
circuit_break
done
```

## SSE Event 结构

```json
{
  "event_id": 1024,
  "request_id": "req_xxx",
  "run_id": "run_xxx",
  "type": "token",
  "delta": "hello",
  "span_id": "span_xxx",
  "created_at": 1710000000
}
```

## SSE 断线恢复协议

```text
GET /api/v1/chat/{request_id}/resume?last_event_id=1024
GET /api/v1/agent/{run_id}/resume?last_event_id=1024
```

后端逻辑：

```text
1. 从 Redis Stream 读取 event_id > 1024 的事件
2. 先补发 missed events
3. 如果请求仍 active，继续接实时 channel
4. 如果请求已 done，补发 done
5. 如果请求 failed，发 error / fallback
```

------

# 十一、核心模块 6：Trace、Eval 与 Dashboard

## Trace 需要记录什么？

```text
request_id
trace_id
run_type: chat / rag / agent / benchmark
prompt_tokens
completion_tokens
ttft_ms
total_latency_ms
model_backend
slot_id
queue_wait_ms
retrieved_docs
retrieval_scores
rerank_scores
citations
tool_calls
node_timeline
errors
final_status
```

## RAG Eval 指标

```text
Recall@K
MRR
Context Precision
Faithfulness
Answer Correctness
Citation Accuracy
Latency P95
No-answer Accuracy
```

## Agent Eval 指标

```text
Task Success Rate
Step Count
Tool Success Rate
Tool Error Recovery Rate
Loop Break Count
Human Intervention Rate
End-to-end Latency
```

## Dashboard 页面

```text
1. Overview：active slots、queued requests、memory pressure、error rate
2. Chat Monitor：TTFT、tokens/s、prompt cache hit
3. RAG Monitor：top-k docs、rerank score、citation accuracy
4. Agent Monitor：graph timeline、tool calls、checkpoint、resume 状态
5. Benchmark：并发压测曲线、P50/P95/P99、失败类型
6. Trace Detail：一次请求的完整 span tree
```

------

# 十二、两周渐进式开发计划

## Week 10：AI-Gateway v1 —— 本地模型统一网关 + LangChain RAG Runtime

### Day 1：项目骨架

```text
FastAPI backend
Vue Dashboard skeleton
DDD 四层目录
Redis docker-compose
request_id middleware
```

### Day 2：llama.cpp / Ollama Client

```text
OpenAI-compatible chat completions
streaming API
/tokenize 或 fallback tokenizer
/metrics /slots probe
```

### Day 3：Admission Controller

```text
ModelProfile
TokenBudgetEstimator
SlotAllocator
Redis Queue
基础 chat submit / stream
```

### Day 4：SSE Event Store

```text
event_id
Redis Stream
heartbeat
done/error
resume endpoint
```

### Day 5：LangChain RAG Runtime

```text
document ingestion
splitter
vector store
retriever
GatewayChatModel adapter
RAG streaming events
citations
```

### Day 6：Trace v1

```text
TraceRun
Span
retrieval latency
LLM latency
token usage
trace detail API
```

### Day 7：RAG Eval v1

```text
rag_gold_set.jsonl
Recall@K
Citation Accuracy
Faithfulness 人工/规则评估
eval_report.md
```

------

## Week 11：AI-Gateway v2 —— LangGraph Agent Runtime + 高并发治理 + Dashboard

### Day 1：LangGraph Agent Skeleton

```text
AgentState
classify_task
retrieve_context
answer
verify
checkpoint
```

### Day 2：Tool Registry

```text
tool schema
timeout
retry
tool call trace
calculator / file_search / web_search mock tool
```

### Day 3：Agent SSE

```text
node_start
node_end
tool_start
tool_end
token
warning
resume agent stream
```

### Day 4：Fault Engine

```text
repeat detector
unicode anomaly detector
long silence timeout
tool loop breaker
circuit breaker
fallback answer
```

### Day 5：Benchmark

```text
10 / 50 / 100 concurrency
chat benchmark
rag benchmark
agent benchmark
P50/P95/P99
queue wait time
```

### Day 6：Dashboard

```text
metrics overview
slot panel
RAG trace panel
Agent graph timeline
benchmark report panel
```

### Day 7：README + 作品集包装

```text
architecture diagram
quick start
API examples
screenshots
eval report
benchmark report
interview notes
```

------

# 十三、推荐最终 README 展示结构

```text
# AI-Gateway

## 1. 项目定位
本地 LLM / RAG / Agent 的轻量企业级治理网关。

## 2. 核心能力
- llama.cpp / Ollama 统一接入
- LangChain RAG Runtime
- LangGraph Agent Runtime
- Admission Control
- KV Token Budget
- Priority Queue
- SSE Resume
- Prefix Cache Router
- Trace / Eval / Dashboard

## 3. 架构图
Vue Dashboard → FastAPI Gateway → Runtime Router → Governance Engines → Model Backends

## 4. 快速启动
llama-server 启动
Redis 启动
Backend 启动
Frontend 启动

## 5. API 示例
Chat
RAG Query
Agent Run
Trace
Benchmark

## 6. 压测报告
10 / 50 / 100 并发对比
TTFT
Tokens/s
P95 latency
Queue wait

## 7. RAG Eval 报告
Recall@K
Citation Accuracy
Faithfulness

## 8. Agent Eval 报告
Task Success
Tool Error Recovery
Loop Break

## 9. 面试高频问题
为什么 LangChain 不直接裸连模型？
为什么需要 GatewayChatModel？
Agent 如何防止无限循环？
RAG 如何评估？
SSE 如何恢复？
KV Budget 如何估算？
```

------

# 十四、你这个项目的关键技术亮点

最终你要把亮点压缩成这几句话：

```text
1. 我实现的不是普通聊天 Web UI，而是本地 LLM、RAG、Agent 的统一治理网关。
2. 我把 LangChain / LangGraph 接入 Gateway，不让它们直接裸连底层模型。
3. 我用 Admission Controller 和 KV Token Budget 控制本地模型并发，避免长上下文请求压垮服务。
4. 我支持 SSE 断线恢复，每个 token、tool call、graph node 都有 event_id 和 trace。
5. 我把 RAG 的 retrieval、rerank、citation、answer verification 做成可观测链路。
6. 我把 Agent 的 node、tool call、checkpoint、resume 做成显式状态机，而不是黑盒循环。
7. 我用 Dashboard 展示 TTFT、tokens/s、队列等待、slot 状态、RAG 质量和 Agent 执行轨迹。
```

这就是一个比普通 LangChain 项目更有层次的 AI Infra + LLM Application 工程作品。
