# 🚀 100-Day LLM Full-Stack Hardcore Roadmap: 从底层撕起，手搓企业级 AI-Gateway

这是一个专为想深入大模型算法与工程落地的同学设计的极速学习路线。拒绝只做一个“会调用 API 的调包侠”，我们将用 100 天的时间，用最高效的节奏复习深度学习，经由 9 大主流生态项目复现（1个月冲刺），最终落地一个高并发、高可用的企业级 AI-Gateway。

## 🌟 路线特色

- **极速温故知新：** 针对已有基础的同学，提供现成的 `.ipynb` 进行 3 天极速复习。
- **贴近工业界真实场景：** 强化 Docker/Redis 基建、API 中转调度、Token 计费以及 Claude Code 自动化工作流。
- **高强度项目冲刺：** 1 个月内强攻 9 大顶流开源项目，完成从多模态到 Agent 闭环的跨越。
- **工程化大收官：** 拒绝写完脚本就扔，最终所有模块全部接入自研的 AI-Gateway。

## 🗺️ 学习路线大纲

### Phase 0: 工程师基建与极速复习 (建议 3-5 天)

> 目标：用最短时间唤醒数学与机器学习记忆，并搭建坚不可摧的工程基建。

- **Day 1: Python 与深度学习极速唤醒 (配套 `.ipynb` 食用)**
  - Python 进阶：异步编程 (asyncio)、类型注解、装饰器。
  - DL 核心：PyTorch 张量操作、反向传播、梯度下降直觉。
- **Day 2: 容器化与部署基石**
  - Docker 进阶：不只是 `run`，掌握 Docker Compose 容器编排、网络隔离与 Volume 数据持久化。
- **Day 3: 中间件与数据库实战**
  - Redis 深度实战：不只是缓存！掌握 Redis Pub/Sub（发布订阅机制）、KV 存储（为后续大模型流式输出与对话上下文 Memory 做准备）。
  - MySQL / PostgreSQL 基础：存储结构化业务数据。

### Phase 1: 提示词工程与 API 生产力 (建议 4 天)

> 目标：在深入底层前，先成为顶尖的“大模型使用者”和 AI 辅助开发者。

- **Day 1: 提示词工程进阶 (Prompt Engineering)**
  - 从 Zero-shot 到 Few-shot。
  - 掌握思维链 (CoT, Chain-of-Thought) 与指令约束技巧。
- **Day 2: 主流大模型 API 实战**
  - 深度调用 OpenAI / DeepSeek V4 / Qwen API。
  - 剖析 Token 计费机制与上下文窗口限制。
- **Day 3: 工业级 API 中转与调度**
  - 学习如何配置 API 中转站（OneAPI / 各种第三方代理）。
- **Day 4: AI 辅助编程工作流**
  - Claude Code 高级配置与自动化实战。
  - 利用大模型进行代码重构与日常 Skill 分享。

### Phase 2: 大模型底层硬核拆解 (建议 7 天)

> 目标：建立数学与显存的底层直觉，理解 LLM 为什么能“涌现”智能。

- **Day 1:** Transformer 架构透视（自注意力 Self-Attention / 前馈网络）。
- **Day 2:** 进阶注意力机制（MHA / MQA / GQA）。
- **Day 3:** 位置编码（RoPE）与上下文扩展原理。
- **Day 4:** 推理加速核心（KV Cache 与 PagedAttention）。
- **Day 5:** 混合专家模型（MoE）路由原理。
- **Day 6:** 极致显存压缩（量化技术：GPTQ / AWQ / int8 原理）。
- **Day 7:** 参数高效微调（LoRA / QLoRA 理论与数据准备策略）。

### Phase 3: 核心开源生态大冲刺 (1 个月极限挑战)

> 目标：四周时间，拿下 9 大硬核开源项目，掌握 RAG、Agent 与多模态核心。

- **Week 1: 本地推理与微调基建**
  - **MLX LM:** 针对 Apple Silicon M 系列芯片的本地极限微调与推理。
  - **llama.cpp:** GGUF 格式解析、Prompt Cache、本地性能极限榨干。
- **Week 2: 视觉与多模态模型突破**
  - **Diffusers & SAM 2:** 视觉预处理与图像生成底层逻辑。
  - **Qwen-VL & LLaVA-NeXT:** 多模态理解、图文检索与 Prompt 反推。
- **Week 3: RAG 进阶与复杂知识检索**
  - **LangChain / LangGraph:** 搭建带循环和条件判断的企业级 RAG（Query -> 检索 -> 增强 -> 生成）。深入学习向量数据库（Faiss/Chroma）。
  - **GraphRAG:** 打破传统检索局限，探索长文本检索压缩与知识图谱摘要问答。
- **Week 4: 智能体闭环探索 (Agent)**
  - **SWE-agent:** 攻克代码 Agent 的长任务调度、日志恢复与测试反馈闭环。理解 ReAct (思考+行动+观察) 框架。

*(注：在此阶段可以穿插体验 Coze / Dify 等低代码平台，快速验证 Agent 想法，但生产环境依然以代码写熟为准。)*

### Phase 4: 终极收官 - 企业级 AI-Gateway (建议 3 周)

> 目标：将前面所有的散装能力模块化，接入统一的高并发调度治理层。

- **Week 1 (v1 路由与基础调度):**
  - 混合模型路由池：同时兼容本地 llama.cpp 端点与外部 DeepSeek / Claude API。
  - 跑通最小 LangGraph 状态机，封装统一对外的 RESTful 接口。
- **Week 2 (v2 缓存、限流与高可用):**
  - 引入 Redis：实现高并发流控（Rate Limiting）、会话保持（Memory）以及 API 密钥池的轮询与熔断。
  - 完善 Streaming：实现流式 token 输出与 SSE 断线恢复。
- **Week 3 (v3 工程化部署与大屏监控):**
  - 使用 Vue3 + TS 开发前端 Dashboard。
  - 记录并可视化 TTFT (首字响应时间)、tokens/s、检索延迟等核心压测指标。
  - 全面 Docker Compose 容器化一键部署。

## 💡 如何食用本项目？

1. Fork & Star ⭐️ 本项目。
2. Phase 0 提供了现成的 `.ipynb` 和环境配置清单，请务必先跑通。
3. 遇到环境坑？直接查阅每个子目录下的 `troubleshooting.md` 避坑指南。