# 🗺️ 项目路线图

> 标注了当前状态和后续计划。🟢 = 已完成 | 🟡 = 进行中 | 🔴 = 规划中 | ⚪ = 未开始

---

## 当前版本：v1.0 — 内容基建期

### Phase 0 🟢 工程基建与极速复习

| 文件 | 状态 |
|:-----|:---:|
| 01-11 核心内容 | 🟢 11 篇全部完成 |
| README.md | 🔴 缺失 |

### Phase 1 🟡 Prompt、API 与商业网关雏形

| 文件 | 状态 |
|:-----|:---:|
| 01-08 核心内容 | 🟢 8 篇全部完成 |
| llm_chat_service 项目 | 🔴 代码缺失（仅有 `__init__.py` 空壳） |
| README.md | 🔴 缺失 |

### Phase 2 🟢 大模型底层硬核拆解

| 文件 | 状态 |
|:-----|:---:|
| 00-12 核心内容 | 🟢 13 篇全部完成 |
| 01-07 Notebook | 🟢 7 个完整 notebook |
| LLaMA-Factory 教程 | ⚪ 大纲已规划，内容待补充 |
| vLLM 生产部署教程 | 🟡 基础文档有，详细教程待补充 |
| README.md | 🔴 缺失 |

### Phase 3 🟡 RAG 检索增强体系

| 文件 | 状态 |
|:-----|:---:|
| 01-05 核心内容 | 🟢 5 篇完成 |
| 06 RAG 评测(RAGAS/TruLens) | 🔴 仅有 3.7KB 骨架 |
| 07 RAG Web 应用 | 🔴 仅有 2.7KB 骨架 |
| 08 高级分块策略 | 🔴 仅有 2.0KB 骨架 |
| 09 LlamaIndex 入门 | 🔴 仅有 2.2KB 骨架 |
| README.md | 🔴 缺失 |

### Phase 4 🟡 11 大开源项目极限冲刺

| 文件/目录 | 状态 |
|:----------|:---:|
| 01 MLX LM | 🟢 完整可运行项目（server/frontend/scripts） |
| 02 llama.cpp | 🟢 完整可运行项目（gateway/frontend/tests） |
| 03 Diffusers | 🔴 仅有 760B 骨架 |
| 04 SAM 2 | 🔴 仅有 747B 骨架 |
| 05 Qwen-VL/LLaVA | 🔴 仅有 749B 骨架 |
| 06 LangGraph RAG | 🔴 仅有 778B 骨架 |
| 07 LlamaIndex | 🔴 仅有 752B 骨架 |
| 08 GraphRAG | 🔴 仅有 1.1KB 骨架 |
| 09 SWE-agent | 🔴 仅有 1.2KB 骨架 |
| PROJECTS_SUMMARY.md | 🟢 65KB 完整项目矩阵总结 |
| README.md | 🔴 缺失 |

### Phase 5 🟡 Agent 与工作流架构

| 文件 | 状态 |
|:-----|:---:|
| 01-03 核心内容 | 🟢 3 篇完成 |
| 04 Agent 服务化 API | 🔴 仅有 4.0KB |
| 05 开源 Agent 平台实战 | 🔴 仅有 2.7KB |
| 06 多 Agent 协作 | 🔴 仅有 2.5KB |
| 07 Agent 评估体系 | 🔴 仅有 2.1KB |
| 08 Agent 安全 | 🔴 仅有 1.9KB |
| README.md | 🔴 缺失 |

### Phase 6 🔴 终极 AI-Gateway

| 文件/目录 | 状态 |
|:----------|:---:|
| design_doc.md | 🟢 23KB 设计文档 |
| backend/ | 🔴 空目录 |
| frontend/ | 🔴 空目录 |
| configs/ | 🔴 空目录 |
| docker/ | 🔴 空目录 |
| scripts/ | 🔴 空目录 |
| README.md | 🔴 缺失 |

---

## 接下来 30 天计划

### 第一优先级（本周）
- [x] 创建 PROJECT_AUDIT.md（审计报告）
- [x] 修复 requirements.txt（平台标注）
- [x] 创建 docs/START_HERE.md（学习者入口）
- [x] 创建 docs/PORTFOLIO_GUIDE.md（作品集指南）
- [x] 创建 ROADMAP.md（本文件）
- [ ] 为 7 个 Phase 创建/补全 README.md
- [ ] 为 llm_chat_service 填充可运行代码

### 第二优先级（2 周内）
- [ ] 扩写 Phase 3 的 06-09（RAG 评测/Web 应用/分块/LlamaIndex）
- [ ] 扩写 Phase 5 的 04-08（Agent 服务化/平台/多Agent/评估/安全）
- [ ] 创建 docs/FAQ.md
- [ ] 创建 docs/INTERVIEW_GUIDE.md
- [ ] 创建 CONTRIBUTING.md

### 第三优先级（1 个月内）
- [ ] 为 Phase 4 的 03-09 填充分步教程
- [ ] 开始 Phase 6 AI-Gateway 代码实现
- [ ] 创建 CHANGELOG.md
- [ ] 创建 .env.example 模板

---

## 长期愿景

- [ ] Phase 4 全部 11 个项目达到 MLX LM 的完成度
- [ ] Phase 6 AI-Gateway 从设计文档变成可运行项目
- [ ] 补充 GitHub Actions CI（至少 markdown-link-check + pytest）
- [ ] 录制核心 Demo 视频
- [ ] 建立 GitHub Discussions 学习社区
- [ ] 翻译英文版 README（吸引国际 Star）
