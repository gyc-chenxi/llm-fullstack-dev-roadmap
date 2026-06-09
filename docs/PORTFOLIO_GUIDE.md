# 🎯 作品集指南：如何把学习过程变成面试素材

> 本指南教你如何从"我学了很多"升级为"我能证明我做了很多"。

---

## 一、核心原则

面试官不会因为你"看过 Transformer 论文"给你加分。但如果你能说：

> "我手写了 Multi-Head Attention，和 PyTorch 官方实现对比误差小于 1e-4，还用 KV Cache 公式精确计算过 7B 模型在 8K 上下文下的显存占用。"

**这才是面试官要的。**

### 四个"必须有"

| 原则 | 反面教材 | 正面教材 |
|:-----|:--------|:--------|
| **做了什么** | "我学了 Transformer" | "我手写了 MHA + GQA，验证代码在 `phase2_llm_internals/09_attention_from_scratch.md`" |
| **如何验证** | "效果应该还行" | "与 `nn.MultiheadAttention` 对比，误差 < 1e-4" |
| **踩过什么坑** | "挺顺利的" | "最初 transpose 后没 contiguous()，view 报维度不匹配" |
| **面试怎么讲** | "我会调 API" | "我封装了 5 个厂商的统一调用层，支持容灾切换和实时计费" |

---

## 二、作品集证据矩阵

> 🟢 Done = 可展示 | 🟡 Doing = 进行中 | 🔴 TODO = 未开始

| Phase | 项目/产出 | 可展示证据 | 面试一句话讲法 | 状态 |
|:---:|:---------|:---------|:--------------|:---:|
| 0 | Git/Docker/Python 环境 | 仓库 `.gitignore` + `Dockerfile`/`docker-compose.yml` | 我能从零搭建 LLM 开发环境 | 🟢 Done |
| 1 | Prompt Cookbook | `01_prompt_cookbook.md` 25+ 模板 | 我整理了 6 大类可复用 Prompt 模板 | 🟢 Done |
| 1 | Unified LLM Client | `02_llm_client.md` 多 Provider 代码 | 我封装了 5+ 厂商的统一 LLM 调用层 | 🟡 Doing |
| 1 | FastAPI Chat Service | `llm_chat_service/` | 我搭建了兼容 OpenAI 格式的聊天 API | 🔴 TODO |
| 2 | 手写 Attention | `09_attention_from_scratch.md` | 我手写了 MHA + GQA，与官方误差<1e-4 | 🟢 Done |
| 2 | KV Cache 显存计算 | `04_kv_cache.ipynb` | 我能精确计算任意模型在任意上下文下的显存 | 🟢 Done |
| 2 | LoRA 微调实战 | `10_lora_demo.md` + 微调脚本 | 我用 LoRA 微调过模型，懂的参数调优 | 🟢 Done |
| 2 | LLaMA-Factory 微调 | 大纲已规划 | 我用工业级工具完成过垂直领域微调 | 🔴 TODO |
| 2 | vLLM 部署压测 | 大纲已规划 | 我部署过 vLLM 生产集群并做了并发压测 | 🔴 TODO |
| 3 | 文档解析器 | `02_document_loader.md` | 我能处理 PDF/表格/扫描件等多格式文档 | 🟡 Doing |
| 3 | 混合检索 | `04_hybrid_search.md` | 我实现了 BM25+Vector+RRF+Reranker 四合一 | 🟡 Doing |
| 3 | LangGraph RAG | `05_langgraph_rag.md` | 我用状态机编排了可恢复的 RAG 流程 | 🟡 Doing |
| 3 | RAGAS 评测 | `06_rag_evaluation.md` | 我不是只做 RAG，而是做可量化评测 | 🔴 TODO |
| 4 | MLX LM | `phase4/01_mlx_lm/` 完整项目 | 我在 Apple Silicon 上跑通了本地模型推理+微调 | 🟢 Done |
| 4 | llama.cpp Gateway | `phase4/02_llama_cpp/` 完整项目 | 我封装了 llama.cpp 的 OpenAI 兼容 API+Gateway | 🟢 Done |
| 4 | Diffusers/SAM2 等 7 项 | 骨架文件 | — | 🔴 TODO |
| 5 | ReAct Agent | `01_react_agent.md` | 我实现了 ReAct 范式的 Agent 循环 | 🟡 Doing |
| 5 | Agent 安全 | `08_agent_security.md` | 我懂 Prompt Injection 攻防 | 🔴 TODO |
| 6 | AI-Gateway | `design_doc.md` 设计文档 | 我设计了一个企业级多模型网关的架构 | 🟡 Doing |

---

## 三、每个项目的"面试讲法"模板

面试被问到某个项目时，用 STAR 框架：

```
S - Situation:  我在学习什么的时候
T - Task:       决定做什么
A - Action:     具体怎么做、踩了什么坑
R - Result:     怎么验证效果、有什么产出
```

### 示例：手写 Attention

```
S: 我在学 Transformer 底层原理时，发现光看公式不够
T: 决定用 PyTorch 从零手写 Multi-Head Attention
A: 按 Q/K/V 投影 → 拆头 → QKᵀ → √dₖ → Mask → Softmax → V 六步实现
   遇到 transpose 后不 contiguous 导致 view 报错，排查了一小时
   后来又实现了 GQA，理解了 K/V repeat_interleave 的逻辑
R: 与 PyTorch 官方 nn.MultiheadAttention 对比，误差 < 1e-4
   代码在 GitHub 的 phase2_llm_internals/09_attention_from_scratch.md
```

---

## 四、GitHub 主页优化建议

| 操作 | 说明 |
|:-----|:-----|
| 📌 **Pin 这个仓库** | Settings → Customize your pins |
| 🌱 **填绿点墙** | 每天一个小 commit，证明持续学习 |
| 📝 **完善 Profile README** | 在个人首页展示这个路线的进度 |
| 🏷️ **加 Topics** | `llm` `rag` `agent` `ai-gateway` `transformer` `lora` `vllm` |

---

## 五、简历上一句话怎么写

| 项目 | 简历写法 |
|:-----|:--------|
| 手写 Attention | "手写实现 Multi-Head Attention + GQA，与 PyTorch 官方实现误差 < 1e-4" |
| LoRA 微调 | "使用 LoRA/QLoRA 在 7B 模型上完成身份问答微调，参数仅训练 1%" |
| RAG 系统 | "搭建完整 RAG 知识库问答系统，混合检索(BM25+向量+Reranker)+SSE 流式输出" |
| AI-Gateway | "自研多模型 AI-Gateway：统一路由/Redis 限流/熔断降级/Token 计费，Docker 一键部署" |

---

## 六、面试展示清单

面试时打开 GitHub，按以下顺序展示：

1. 🔗 **仓库首页 README** → 让面试官看到路线全景
2. 🧠 **手写 Attention 代码** → 证明底层能力
3. 📊 **KV Cache 显存计算** → 证明工程直觉
4. 🤖 **RAG/Agent Demo** → 证明应用能力
5. 🏗️ **AI-Gateway 设计文档** → 证明系统架构能力
6. ✍️ **weekly_logs/** → 证明持续学习和复盘习惯
