# 🚀 从这里开始

> 根据你的时间和目标，选择最适合的学习路径。

---

## ⚡ 我有多少时间？

### 🟢 只有 7 天（快速体验）

| 天数 | 做什么 | 产出 |
|:---:|:-----|:-----|
| Day 1 | [Phase 0](../phase0_foundation/) — 搭建环境 | Git/Docker/Python 环境就绪 |
| Day 2 | [Phase 1](../phase1_prompt_api/) — 调通 API | 能用代码调用 GPT/DeepSeek |
| Day 3 | [Phase 2](../phase2_llm_internals/) — 理解 Transformer | 看懂 Attention 公式，能画维度流动 |
| Day 4 | [Phase 3](../phase3_rag/) — 跑通 RAG | 一个最简 RAG Demo 能跑起来 |
| Day 5 | [Phase 5](../phase5_agent/) — 玩 Agent | ReAct Agent + 工具调用 |
| Day 6-7 | [Phase 6](../final_ai_gateway/) — 理解网关 | 看懂 AI-Gateway 设计文档 |

> 🎯 **结果**：对大模型全栈有宏观认知，能调 API，能讲清楚基本概念。

---

### 🟡 只有 30 天（核心能力）

| 阶段 | 天数 | 做什么 | 产出 |
|:-----|:---:|:-----|:-----|
| Phase 0 | 3天 | 环境搭建 + Git/Docker/Python/PyTorch 复习 | 开发环境就绪 |
| Phase 1 | 7天 | Prompt 工程 + 多厂商 API + FastAPI 服务 | 一个能跑的多模型 API 服务 |
| Phase 2 | 10天 | **核心** Transformer/Attention/KV Cache/RoPE/LoRA/量化 | 手写 Attention + LoRA 微调 |
| Phase 3 | 7天 | RAG 体系（文档→检索→评估） | RAG 知识库问答 Demo |
| Phase 5 | 3天 | Agent 核心（ReAct + Tool Calling） | ReAct Agent Demo |

> 🎯 **结果**：具备大模型应用开发核心能力，能面试基础岗位。

---

### 🔴 完整 100 天（终极路线）

按 [主 README](../README.md) 的 Phase 0→6 顺序完整推进。

> 🎯 **结果**：11 个开源项目 + 1 个企业级 AI-Gateway，能写进简历的完整作品集。

---

## 🎯 我只想做项目

如果你想跳过理论学习，直接做能写进简历的项目：

| 优先级 | 项目 | 位置 | 难度 | 预计时间 |
|:---:|:-----|:-----|:---:|:---:|
| 1 | **个人知识库 RAG** | [Phase 3](../phase3_rag/) | ⭐⭐ | 3-5天 |
| 2 | **Unified LLM Client** | [Phase 1](../phase1_prompt_api/02_llm_client.md) | ⭐⭐ | 2-3天 |
| 3 | **FastAPI Chat Service** | [Phase 1](../phase1_prompt_api/03_fastapi_chat.md) | ⭐⭐ | 2-3天 |
| 4 | **LangGraph RAG Agent** | [Phase 3](../phase3_rag/05_langgraph_rag.md) → [Phase 5](../phase5_agent/) | ⭐⭐⭐ | 5-7天 |
| 5 | **AI-Gateway** | [Phase 6](../final_ai_gateway/) | ⭐⭐⭐⭐⭐ | 10-16天 |

> ⚠️ 做项目时如果卡住，回头补对应的 Phase 理论基础。

---

## 🎤 我只想准备面试

如果时间紧迫，只啃面试高频内容：

### 必看文件

| 优先级 | 文件 | 面试覆盖点 |
|:---:|:-----|:-----|
| ⭐⭐⭐⭐⭐ | [Transformer 架构](../phase2_llm_internals/00_transformer.md) | 面试必问 |
| ⭐⭐⭐⭐⭐ | [Attention 手写](../phase2_llm_internals/09_attention_from_scratch.md) | 手写 Attention |
| ⭐⭐⭐⭐⭐ | [KV Cache 计算](../phase2_llm_internals/04_kv_cache.ipynb) | 显存估算 |
| ⭐⭐⭐⭐ | [RAG 体系](../phase3_rag/) | RAG 原理+评估 |
| ⭐⭐⭐⭐ | [Agent 设计](../phase5_agent/) | Agent 架构+安全 |
| ⭐⭐⭐ | [微调技术全景](../phase2_llm_internals/11_fine-tuning_techniques.md) | SFT/RLHF/DPO 区别 |
| ⭐⭐⭐ | [vLLM 部署](../phase2_llm_internals/12_deployment_vllm.md) | 推理部署方案选型 |

### 面试参考文件

- [42 个 LLM 核心概念术语表](../phase0_foundation/05_llm_concepts_glossary.md) — 快速补概念
- [7 天深度参考](../phase2_llm_internals/_00_7day_deep_dive_reference.md) — 面试拷问 + 排障场景
- [作品集指南](./PORTFOLIO_GUIDE.md) — 怎么把学到的讲给面试官

---

## 📂 仓库导航

| 你想... | 去这里 |
|:--------|:------|
| 看全景路线图 | [README.md](../README.md) |
| 搭建开发环境 | [环境搭建文档](./01_environment_setup.md) |
| 看审计报告 | [PROJECT_AUDIT.md](../PROJECT_AUDIT.md) |
| 看项目路线图 | [ROADMAP.md](../ROADMAP.md) |
| 学会写简历 | [PORTFOLIO_GUIDE.md](./PORTFOLIO_GUIDE.md) |
| 遇到问题 | [TROUBLESHOOTING.md](./05_troubleshooting.md) |
| 看面试指南 | [INTERVIEW_GUIDE.md](./INTERVIEW_GUIDE.md) (TODO) |
| 看项目总览 | [00_overview.md](./00_overview.md) |

---

## 🔧 环境搭建 30 秒速查

```bash
# 1. 克隆仓库
git clone https://github.com/gyc-chenxi/llm-fullstack-dev-roadmap.git
cd llm-fullstack-dev-roadmap

# 2. 创建虚拟环境
conda create -n llm-dev python=3.11
conda activate llm-dev

# 3. 安装核心依赖 (先不装 GPU/MLX 重依赖)
pip install fastapi uvicorn pydantic httpx openai python-dotenv tiktoken rich

# 4. 开始学习！
# Phase 0: cd phase0_foundation/
# Phase 1: cd phase1_prompt_api/
```

> 📖 详细环境搭建请看：[docs/01_environment_setup.md](./01_environment_setup.md)

---

## 📊 项目可运行状态

| Phase | 可运行代码 | 状态 |
|:-----:|:----------|:---:|
| Phase 0 | 3 个 Jupyter Notebook (.ipynb) | ✅ 可直接运行 |
| Phase 1 | 教程文档 + 代码示例 | 📝 文档阶段 |
| Phase 2 | 7 个 Jupyter Notebook + PyTorch Attention 实现 | ✅ 可直接运行 |
| Phase 3 | RAG 教程 + 检索代码示例 | 📝 文档阶段 |
| Phase 4 | MLX LM(✅) + llama.cpp(✅) + 其余 7 个(📝 骨架) | 🚧 部分可运行 |
| Phase 5 | Agent 教程 | 📝 文档阶段 |
| Phase 6 | 设计文档 | 📝 设计阶段 |
