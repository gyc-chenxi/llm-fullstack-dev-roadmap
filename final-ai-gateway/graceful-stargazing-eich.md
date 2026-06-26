# Final AI Gateway — 实施计划

## Context

**项目**：`10_final-ai-gateway` — 企业级轻量化大模型智能路由与 Agent 治理网关系统  
**位置**：`/Users/chenxi/Documents/晨熙个人/0暑期自学大模型/final_ai_gateway/`（需重命名为 `10_final-ai-gateway`）  
**硬件**：MacBook Air M5, 32GB, 1TB SSD, macOS  
**环境**：Conda `cxllm`, Python 3.11  
**现状**：design_doc.md (23KB) 已完成，所有子目录为空  
**目标模型**：qwen2.5-7b-instruct-q4_k_m.gguf (~4.4GB, 已存在于 phase4_projects)

## 核心架构决策

- **DDD 四层**：domain → application → infrastructure → interface
- **GatewayChatModel**：LangChain 的 BaseChatModel 适配器，所有 LLM 调用经过 Gateway 治理
- **Redis Streams**：SSE 事件存储（替代 PostgreSQL）
- **llama.cpp server**：主力后端（暴露 slots/metrics/prompt cache）
- **Vue 3 Dashboard**：纯监控面板，非聊天 UI

## 项目核心能力

1. 多模型统一路由（llama.cpp / Ollama / OpenAI-compatible）
2. Admission Controller + KV Token Budget（防止并发压垮本地模型）
3. Redis 优先级队列（请求排队不丢失）
4. SSE 断线恢复（event_id + Redis Stream replay）
5. LangChain RAG Runtime（检索→重排→引用校验→生成）
6. LangGraph Agent Runtime（状态机→工具调用→checkpoint→resume）
7. 熔断降级（乱码检测/复读检测/Agent 无限循环防护）
8. Trace/Eval/Dashboard（TTFT/TPOT/Recall@K/Citation Accuracy）

## 实施阶段（共 7 个阶段）

### 阶段 1：项目骨架 + 领域层 ✅ (完成于 2026-06-26)
- 重命名项目 → `10_final-ai-gateway`
- 完整 DDD 四层目录树（~36 个 __init__.py）
- 所有 Domain Entities + Value Objects + Ports + Services + Policies
- pyproject.toml, Makefile, configs/*.yaml, docker-compose.yml
- `.env.example`, `.gitignore`

### 阶段 2：基础设施层 ✅ (完成于 2026-06-26)
- Redis 连接池 + 7 个 Repository 实现
- llama.cpp Client + Tokenizer + System Probes
- GatewayChatModel（LangChain 适配器）
- Docker Redis 配置

### 阶段 3：Chat 接入控制管道 ✅ (完成于 2026-06-26)
- Admission Controller + Slot Allocator（完整实现）
- Token Budget Estimator（KV 公式）
- SSE Event Store + Event ID Generator
- Submit/Stream/Resume/Cancel Use Cases
- Queue Worker（后台异步消费）

### 阶段 4：FastAPI 接口层 ✅ (完成于 2026-06-26)
- 全部 HTTP 路由（chat/metrics/slots/trace/admin）
- 3 个中间件（Request ID / Rate Limit / Error Boundary）
- SSE 端点（stream/resume）
- main.py 组装 + startup/shutdown 钩子
- `make smoke` 端到端验证
### 阶段 5：RAG + Agent Runtime ✅ (完成于 2026-06-26)
- 文档加载/分割/向量库/BM25/混合检索/Reranker
- LangChainRagRuntime（检索→重排→生成→引用）
- LangGraph Agent Graph（classify→retrieve→plan→execute→verify）
- Redis Checkpointer + Tool Registry
- RAG Eval（Recall@K, MRR, Citation Accuracy）

### 阶段 6：熔断 + Benchmark + Dashboard ✅ (完成于 2026-06-26)
- Output Guard（乱码/复读/不可见字符检测）
- Circuit Breaker（CLOSED→OPEN→HALF_OPEN 状态机）
- Agent Loop Guard（步数/重复/超时限制）
- 10/50/100 并发压测 + P50/P95/P99 报告
- Vue 3 Dashboard（6 个监控面板）

### 阶段 7：最终封装 ✅ (完成于 2026-06-26)
- README.md（作品集级别，含架构图/API示例/快速启动）
- PROGRESS.md（全7阶段进度追踪）
- TROUBLESHOOTING-*.md（4 个踩坑指南：Redis/llamacpp/RAG/Dashboard）
- INTERVIEW-QUESTIONS.md（3 道核心面试题 + 3 道附加题）
- 完整项目文件 176+，80 个测试全部通过

## 交付物

| 文件 | 说明 |
|------|------|
| `runbook.md` | 核心：所有阶段完整可执行工程手册 |
| `PROGRESS.md` | 进度追踪文档（每阶段完成后更新） |
| `Makefile` | setup / run-all / clean / smoke / bench-* |
| `backend/` | ~140 个 Python 文件，DDD 四层架构 |
| `frontend/` | Vue 3 + Pinia + Chart.js Dashboard |
| `configs/` | app.yaml, model.yaml, rag.yaml, logging.yaml |
| `docker/` | docker-compose.yml + redis.conf |
| `scripts/` | 环境检查/模型准备/服务启停/压测脚本 |
| `docs/` | architecture.md, api.md, eval/benchmark 报告 |

## 验证方式

- 阶段 1：`pytest backend/tests/unit/test_domain/` 全部通过
- 阶段 2：`pytest backend/tests/integration/test_redis_repos.py` 通过
- 阶段 3：`make smoke` — curl POST /api/v1/chat → SSE token 流
- 阶段 5：`make eval-rag` — 生成 Recall@K 等指标报告
- 阶段 6：`make bench-10` — 10 并发 50 请求压测报告
- 阶段 7：`make run-all` — 一键启动全部服务
