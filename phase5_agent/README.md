# Phase 5 🤖 Agent 与工作流架构

> **Day 76-84** | ⏱️ 9 天 | 📊 难度 ⭐⭐⭐⭐

---

## 你将在本阶段学会什么

- ✅ ReAct Agent 范式 — Reasoning + Acting 循环
- ✅ Tool Calling — 工具定义/注册/并行调用/错误处理
- ✅ LangGraph 多节点 Agent — 状态机 + Human-in-the-loop
- ✅ Agent 服务化 API — 任务队列 + SSE 实时推送
- ✅ 开源平台实战 — Dify / RAGFlow / Coze
- ✅ 多 Agent 协作模式 — CrewAI / AutoGen
- ✅ Agent 安全 — Prompt Injection 攻防
- ✅ Agent 评估体系 — 可观测性 + 评估指标

## 前置要求

- 完成 [Phase 1-3](../phase3_rag/) — LLM 调用/RAG/工具
- 理解 LLM 的 Tool/Function Calling 机制

## 学习天数与任务表

| Day | 主题 | 文件 | 产出 | ✅ |
|:---:|:-----|:-----|:-----|:--:|
| 76-77 | ReAct Agent | `01_react_agent.md` | 完整 ReAct 循环实现 | ☐ |
| 78-79 | Tool Calling | `02_tool_calling.md` | 5 个真实工具 + 注册中心 | ☐ |
| 80-81 | LangGraph Agent | `03_langgraph_agent.md` | 多节点 + HITL + Checkpoint | ☐ |
| 82 | Agent 安全 | `08_agent_security.md` | Prompt Injection 攻防 | ☐ |
| 82-83 | Agent 服务化 | `04_agent_api.md` | API + 任务队列 + SSE | ☐ |
| 83 | 开源平台实战 | `05_open_source_agent_platforms.md` | Dify/RAGFlow/Coze | ☐ |
| 83-84 | 多 Agent 协作 | `06_multi_agent_patterns.md` | CrewAI 实战 | ☐ |
| 84 | Agent 评估 | `07_agent_evaluation.md` | 评估指标 + 可观测性 | ☐ |

## 本阶段核心产出

- 🤖 **ReAct Agent** — 支持多轮工具调用的自主 Agent
- 🛠️ **Tool Registry** — 装饰器注册 + 自动 Schema 生成
- 🔀 **LangGraph StateMachine** — HITL + Checkpoint 恢复
- 🔒 **Agent 安全方案** — Prompt Injection 防御

## 如何运行本阶段 Demo

```bash
cd phase5_agent

# 安装依赖
pip install langgraph langchain openai httpx

# 按 01_react_agent.md 中的代码创建 react_agent.py
# 填入你的 API Key
python react_agent.py

# 按 03_langgraph_agent.md 中的代码体验 checkpoint 恢复
```

> 🚧 **注意**: Phase 5 当前为文档阶段，完整可运行 Demo 正在补全中。

## 验收标准

- [ ] 实现 ReAct Agent，支持至少 3 种工具
- [ ] Tool 定义含 Pydantic Schema + 错误返回格式
- [ ] LangGraph Agent 支持 checkpoint 恢复
- [ ] 至少体验过一个开源平台（Dify/RAGFlow/Coze）

## 常见问题

| 问题 | 解决 |
|:-----|:-----|
| Agent 死循环 | 设 `max_iterations` + stop token 检测 |
| 工具调用错误 | 工具返回结构化错误 `{"error": "...", "hint": "..."}` |
| LangGraph checkpoint 不生效 | 编译时传 `checkpointer`，invoke 时传 `config` |

## 面试可讲点

1. "我实现了 ReAct 范式 Agent，不是直接用 LangChain AgentExecutor"
2. "我的 Agent 有 Human-in-the-loop 审批节点，危险操作需要人工确认"
3. "我了解 Prompt Injection 的三种攻击方式和对应防御策略"
4. "我在 Dify/RAGFlow 上搭建过工作流 Agent，知道什么时候该用开源平台 vs 自己写"

## 下一阶段

👉 [Phase 6: 终极 AI-Gateway](../final_ai_gateway/)
