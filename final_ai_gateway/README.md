# Phase 6 🏗️ 终极项目：企业级 AI-Gateway

> **Day 85-100** | ⏱️ 16 天 | 📊 难度 ⭐⭐⭐⭐⭐

---

## 你将在这个项目中学会什么

- ✅ 多模型统一路由 — 一个 API 接入 5+ 厂商 + 本地模型
- ✅ Redis 滑动窗口限流 — 按用户/按 Key 精细化控制
- ✅ 熔断降级机制 — 主模型故障自动 Fallback
- ✅ Token 计费引擎 — 实时统计用量与成本
- ✅ RAG/Agent 运行时接入 — LangChain + LangGraph 通过 Gateway 治理
- ✅ 监控 Dashboard — Vue3 可视化后台
- ✅ Docker Compose 一键部署

## 前置要求

- 完成 Phase 0-5 全部内容
- 理解 FastAPI/Redis/PostgreSQL/Docker
- 理解 LLM API 调用（Phase 1）
- 理解 RAG/Agent 架构（Phase 3/5）

## 项目架构

```
Vue3 Dashboard → FastAPI Gateway → 路由层 → 治理层(限流/熔断/计费)
                                              → 模型层(云端API + 本地模型)
                                              → RAG/Agent 运行时
```

详细架构见 [design_doc.md](./design_doc.md)

## 当前状态：🚧 设计阶段

| 模块 | 状态 | 说明 |
|:-----|:---:|:-----|
| `design_doc.md` | 🟢 Done | 23KB 完整设计文档 |
| `backend/` | 🔴 空目录 | FastAPI 网关后端待实现 |
| `frontend/` | 🔴 空目录 | Vue3 Dashboard 待实现 |
| `configs/` | 🔴 空目录 | 路由/模型配置文件待创建 |
| `docker/` | 🔴 空目录 | Docker Compose 待创建 |
| `scripts/` | 🔴 空目录 | 部署/压测脚本待创建 |

## 学习路线

| Day | 主题 | 产出 |
|:---:|:-----|:-----|
| 85-88 | 需求设计 + 统一路由层 | 多 Provider 适配 + 路由分发 |
| 89-92 | 治理层 | Redis 限流 + 熔断降级 + API Key 管理 |
| 93-96 | 计费系统 + Dashboard | Token 统计 + 可视化后台 |
| 97-100 | RAG/Agent 接入 + 部署 | Docker Compose + 压测 |

## 技术亮点（面试必讲）

| # | 亮点 | 解决什么痛点 |
|:--:|:-----|:-----|
| 1 | 多模型统一路由 | 一个 API 地址接入所有模型 |
| 2 | 容灾降级 | 主模型故障自动切换备选 |
| 3 | 限流熔断 | 防止恶意调用 + 保护上游 |
| 4 | Token 计费 | 实时成本控制 + 预算预警 |
| 5 | 监控 Dashboard | TTFT/TPOT/QPS 一目了然 |
| 6 | Docker 一键部署 | 生产就绪 |

## 如何开始

当前阶段建议先阅读：
1. [design_doc.md](./design_doc.md) — 理解整体设计
2. Phase 1 的 [FastAPI Chat Service](../phase1_prompt_api/03_fastapi_chat.md) — 理解单个模型的 API 封装
3. Phase 1 的 [Unified LLM Client](../phase1_prompt_api/02_llm_client.md) — 理解多 Provider 统一调用

## 验收标准

- [ ] 理解 AI-Gateway 的分层架构（应用编排 vs 服务治理 vs 模型执行）
- [ ] 能画出 Gateway 的请求流程图
- [ ] 能说清楚为什么 LangChain 不是 Gateway 的替代品

## 面试可讲点

1. "我设计了一个企业级 AI-Gateway，不是只会调 API"
2. "我的 Gateway 有分层架构——LangChain 做应用编排，Gateway 做服务治理，vLLM 做模型执行"
3. "我理解限流/熔断/计费是企业级 API 的基础，不是可选项"

## 关联项目

- 回顾 [Phase 1 llm_chat_service](../phase1_prompt_api/llm_chat_service/) — 单模型 API
- 回顾 [Phase 4 llama.cpp Gateway](../phase4_projects/02_llama_cpp/) — 本地模型 Gateway
