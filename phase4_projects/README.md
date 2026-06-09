# Phase 4 🔥 11 大开源项目极限冲刺

> **Day 46-75** | ⏱️ 30 天 | 📊 难度 ⭐⭐⭐⭐⭐

---

## 你将在本阶段学会什么

- ✅ MLX LM — Apple Silicon 原生推理与 LoRA 微调
- ✅ llama.cpp — GGUF 量化 + 本地 Serving + OpenAI 兼容 API
- ✅ LLaMA-Factory — 工业级微调流水线（Web UI + CLI）
- ✅ vLLM — 生产级推理集群（Prefix Cache + Multi-LoRA）
- ✅ Diffusers — Stable Diffusion 图像生成
- ✅ SAM 2 — 视觉分割
- ✅ Qwen-VL/LLaVA — 多模态理解
- ✅ LangGraph RAG — 企业级实战
- ✅ LlamaIndex — 知识库框架
- ✅ GraphRAG — 图谱检索增强
- ✅ SWE-agent — AI 代码修复

## 前置要求

- 完成 [Phase 0-3](../phase3_rag/) — 全部前置
- 有命令行操作能力

## 项目列表与状态

| # | 项目 | 天数 | 状态 | 产出 | ✅ |
|:--:|:-----|:---:|:---:|:-----|:--:|
| 1 | 🆕 LLaMA-Factory | 4 | 📝 大纲 | 微调适配器+评测 | ☐ |
| 2 | MLX LM | 4 | 🟢 完整 | Chat UI + LoRA | ☐ |
| 3 | vLLM 推理集群 | 3 | 📝 大纲 | 压测报告 | ☐ |
| 4 | llama.cpp | 4 | 🟢 完整 | Gateway + 前端 | ☐ |
| 5 | Diffusers | 3 | 📝 骨架 | SD 图像生成 | ☐ |
| 6 | SAM 2 | 3 | 📝 骨架 | 视觉分割 | ☐ |
| 7 | Qwen-VL/LLaVA | 3 | 📝 骨架 | 多模态理解 | ☐ |
| 8 | LangGraph RAG | 2 | 📝 骨架 | 企业级 RAG | ☐ |
| 9 | LlamaIndex | 2 | 📝 骨架 | 知识库 | ☐ |
| 10 | GraphRAG | 2 | 📝 骨架 | 图谱检索 | ☐ |
| 11 | SWE-agent | 2 | 📝 骨架 | 代码修复 | ☐ |

> 🟢 = 完整可运行 · 🟡 = 部分完成 · 📝 = 大纲/骨架阶段

## 如何运行已完成的 Demo

### MLX LM（🍎 Apple Silicon only）

```bash
cd phase4_projects/01_mlx_lm
pip install mlx mlx-lm
bash scripts/setup_check.sh
bash scripts/start_all.sh
# 前端: http://localhost:5173
# API: http://localhost:8000/docs
```

### llama.cpp Gateway

```bash
cd phase4_projects/02_llama_cpp
bash scripts/build_llamacpp.sh    # 编译 llama.cpp
bash scripts/serve_q4.sh           # 启动 GGUF 服务
pip install fastapi uvicorn httpx
python gateway/app.py              # 启动 Gateway
# 测试: bash scripts/smoke_openai.sh
```

## 本阶段核心产出

- 🏗️ **2 个完整可运行项目**（MLX LM + llama.cpp Gateway）
- 📊 **项目对比矩阵**（见 `PROJECTS_SUMMARY.md`）
- 📝 **其余项目的 Runbook 文档**

## 验收标准

- [ ] 至少跑通 2 个项目的最小 Demo
- [ ] 读完全部 `PROJECTS_SUMMARY.md`
- [ ] 能说出每个项目解决什么问题、技术栈是什么

## 面试可讲点

1. "我在 Apple Silicon 上用 MLX LM 跑通了 7B 模型推理+LoRA 微调"
2. "我封装了 llama.cpp 的 OpenAI 兼容 API Gateway，支持 SSE 流式和健康检查"
3. "我理解 vLLM 的 PagedAttention 为什么能提升 3x 吞吐"

## 下一阶段

👉 [Phase 5: Agent 与工作流架构](../phase5_agent/)
