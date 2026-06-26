# AI-Gateway

> **企业级轻量化大模型智能路由与 Agent 治理网关**
>
> A production-style governance layer for local LLM serving, LangChain RAG, and LangGraph Agent — with admission control, circuit breaking, SSE resilience, and a real-time monitoring dashboard.

[![Tests](https://img.shields.io/badge/tests-87%20passed-brightgreen)](./backend/tests)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4-42b883)](https://vuejs.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D)](https://redis.io/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

---

## What is this?

AI-Gateway is **not** a chatbot UI or a LangChain demo. It's a governance gateway that sits between your application and the model backend, providing:

```
Your Application / LangChain / LangGraph
              ↓
      ╔═════ AI-Gateway ═════╗
      ║  Admission Control    ║  ← KV Token Budget gate
      ║  Priority Queue       ║  ← Redis ZSET, no lost requests
      ║  Slot Allocation      ║  ← Model compute slot management
      ║  Output Guard         ║  ← Garbled/repetition detection
      ║  Circuit Breaker      ║  ← CLOSED→OPEN→HALF_OPEN
      ║  SSE Stream + Resume  ║  ← event_id, Redis Stream replay
      ║  Trace + Metrics      ║  ← Full observability
      ╚═══════════════════════╝
              ↓
    llama.cpp / Ollama / OpenAI
```

The key insight: **LangChain orchestrates application logic; AI-Gateway governs service quality.** They're different concerns, and production systems need both.

## Verified Status

| Metric | Value |
|--------|-------|
| Tests | **87 passed**, 0 failed |
| API Routes | 13 (chat, RAG, agent, metrics, slots, trace, benchmark, admin) |
| Ollama E2E | Working — `qwen2.5:7b`, SSE streaming verified |
| TTFT (single request) | ~260ms on M5 32GB |
| Redis | 7 repositories, all integration tests pass |
| Dashboard | 6 monitoring panels, Pinia + Chart.js |

## Quick Start

**Prerequisites**: Python 3.11+, Node.js 18+, Docker (for Redis), Ollama

```bash
# 1. Start Redis
docker run -d --name ai-gateway-redis -p 6379:6379 redis:7-alpine

# 2. Pull model (if not already)
ollama pull qwen2.5:7b

# 3. Install & run backend
cd backend
pip install -e ".[dev,test]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Run tests
python -m pytest tests/ -v

# 5. Test with curl
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"stream":false}'

# 6. Dashboard (optional)
cd frontend && npm install && npm run dev
# Open http://localhost:3000
```

## API Reference

```bash
# Chat — with SSE streaming
POST /api/v1/chat                          # Submit chat request
GET  /api/v1/chat/{id}/stream              # SSE token stream
GET  /api/v1/chat/{id}/resume?last_event_id=N  # Resume after disconnect
POST /api/v1/chat/{id}/cancel              # Cancel request

# RAG — retrieval-augmented generation
POST /api/v1/rag/query                     # Submit RAG query

# Agent — LangGraph state machine
POST /api/v1/agent/run                     # Submit agent run

# Observability
GET  /api/v1/metrics/snapshot              # System + model metrics
GET  /api/v1/slots                         # Model slot status
GET  /api/v1/trace/{trace_id}              # Full trace detail
GET  /api/v1/trace                         # Recent traces

# Operations
POST /api/v1/benchmark/run                 # 10/50/100 concurrency test
GET  /api/v1/admin/health                  # Health check
GET  /api/v1/admin/queue-info              # Queue depth + next ticket
```

## Architecture: DDD Four-Layer

```
backend/app/
├── domain/                    # Pure business rules — zero framework deps
│   ├── entities/              # 10 entities (InferenceRequest, AgentRun, Slot...)
│   ├── value_objects/         # 9 VOs (TokenBudget, AdmissionDecision, Priority...)
│   ├── services/              # 11 domain services (AdmissionController, CircuitBreaker...)
│   ├── policies/              # 6 policies (Priority, Degradation, Retry, Timeout...)
│   └── ports/                 # 12 abstract interfaces (LLMClient, QueueRepo...)
├── application/               # Use case orchestration
│   ├── use_cases/             # SubmitChat, StreamChat, ResumeStream, Cancel, Dequeue
│   ├── dto/                   # Request/response models
│   └── orchestrators/         # InferenceOrchestrator, QueueWorker, MetricsCollector
├── infrastructure/            # External system adapters
│   ├── redis/                 # 7 repos (Queue, Stream, Slot, Metrics, TokenBucket, Trace, Cache)
│   ├── llm_clients/           # llama.cpp + Ollama + OpenAI + GatewayChatModel
│   ├── retrieval/             # DocumentLoader, TextSplitter, BM25, VectorStore, Hybrid, Reranker
│   ├── langchain_runtime/     # RAG runtime + LangChain retriever adapter
│   ├── langgraph_runtime/     # 6-node agent graph + Redis checkpointer + Tool registry
│   ├── tokenizer/             # llama.cpp tokenize, tiktoken estimator, fallback
│   ├── probes/                # macOS memory, llama.cpp metrics, Ollama health
│   ├── sse/                   # EventIdGenerator, Redis Stream event store
│   └── benchmark/             # AsyncIO load generator + RAG eval runner
└── interface/                 # External API surface
    ├── http/                  # 8 route modules
    ├── sse/                   # Stream + resume endpoint handlers
    └── middlewares/            # RequestId, ErrorBoundary
```

## Technical Highlights (Interview Ready)

### 1. GatewayChatModel — LangChain Doesn't Talk to Models Directly

I built a `GatewayChatModel(BaseChatModel)` adapter. Every LLM call from LangChain chains or LangGraph agents passes through admission control, output guard, and circuit breaker:

```python
class GatewayChatModel(BaseChatModel):
    llm_client: LLMClientPort           # Backend client
    admission_controller: AdmissionController  # Admission gate
    output_guard: OutputGuard            # Quality detection per token
    circuit_breaker: CircuitBreaker      # Failure protection
```

### 2. KV Token Budget — Prevent Overload with Math, Not Magic

Instead of guessing "max concurrent requests," I estimate actual KV cache pressure:

```
kv_bytes = 2 × layers × seq_len × num_kv_heads × head_dim × dtype_bytes
```

Admission decision: if `active_kv_bytes + request_kv_bytes > safe_budget` → queue it.

### 3. Redis ZSET Priority Queue

Score formula: `priority × 10^15 + timestamp × 10^6`. High-priority requests (lower value) pop first; same priority → FCFS. Atomic `ZPOPMIN` ensures no race conditions.

### 4. SSE Resume — Never Lose a Token

Every SSE event carries an `event_id`. All events are persisted in Redis Stream. Client reconnects with `?last_event_id=N` → missed events replayed, then live stream continues.

### 5. Agent as Explicit State Machine, Not a Black-Box Loop

```
START → classify_task → retrieve_context → plan_tool_calls
     → execute_tools → generate_answer → verify_answer → END
```

Each node is protected by `AgentLoopGuard`: max steps, max LLM calls, max tool calls, repetition detection, total runtime cap. Every node writes a checkpoint to Redis.

### 6. Hybrid RAG Retrieval

Vector (ChromaDB cosine) + BM25 (sparse IDF) → weighted fusion (0.6/0.4) → Reranker scoring. Citations are anchored to retrieved documents and validated.

## Dashboard (6 Panels)

| Panel | What it shows |
|-------|--------------|
| **Overview** | Active slots, queue depth, TTFT, tokens/s, memory pressure, error rate |
| **Chat Monitor** | Request trace table with TTFT/TPOT/token counts |
| **RAG Monitor** | Recall@K, MRR, citation accuracy, retrieval latency |
| **Agent Monitor** | Active runs, step counts, tool success rate, loop breaks |
| **Benchmark** | Configurable 10/50/100 concurrency runner with P50/P95/P99 reports |
| **Trace Detail** | Full span tree with latency breakdown for a single request |

## Project Stats

```
Python source files:  80+
Vue components:        7
Tests:                87 (87 passed, 0 failed)
API routes:           13
DDD layers:            4
Domain entities:      10
Domain services:      11
Domain policies:       6
Redis repositories:    7
LLM backends:          3
Dashboard panels:      6
Total files:         170+
```

## Interview Questions

See [INTERVIEW-QUESTIONS.md](./INTERVIEW-QUESTIONS.md) for detailed answers to:

1. Why doesn't LangChain call models directly? What does GatewayChatModel solve?
2. How does the Agent prevent infinite loops?
3. How is KV Token Budget estimated — and why this formula?
4. How does SSE resume work after a disconnection?
5. How does the Redis ZSET priority queue order requests?

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, LangChain, LangGraph, httpx, Pydantic |
| Data | Redis 7 (ZSET, Stream, Hash, Lua scripting) |
| Models | Ollama (qwen2.5:7b), llama.cpp, OpenAI-compatible |
| Frontend | Vue 3, Pinia, Vue Router, Chart.js, Vite |
| Retrieval | ChromaDB, BM25, Hybrid fusion, Reranker |
| Infra | Docker (Redis), macOS Apple Silicon (M5 32GB) |
| Testing | pytest (87 tests), pytest-asyncio |

## Related Docs

- [design_doc.md](./design_doc.md) — Full architecture design (23KB)
- [PROGRESS.md](./PROGRESS.md) — Phase-by-phase implementation tracking
- [INTERVIEW-QUESTIONS.md](./INTERVIEW-QUESTIONS.md) — Interview Q&A
- [TROUBLESHOOTING-redis.md](./TROUBLESHOOTING-redis.md) — Redis issues
- [TROUBLESHOOTING-llamacpp.md](./TROUBLESHOOTING-llamacpp.md) — Model server issues
- [TROUBLESHOOTING-rag.md](./TROUBLESHOOTING-rag.md) — RAG quality issues
- [TROUBLESHOOTING-dashboard.md](./TROUBLESHOOTING-dashboard.md) — Frontend issues

## License

MIT
