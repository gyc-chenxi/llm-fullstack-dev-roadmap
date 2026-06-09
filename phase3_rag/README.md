# Phase 3 📚 RAG 检索增强体系 — 工业文档 + 量化评测

> **Day 29-45** | ⏱️ 17 天 | 📊 难度 ⭐⭐⭐⭐

---

## 你将在本阶段学会什么

- ✅ 从零实现完整 RAG 链路（文档→Chunk→Embedding→检索→LLM 生成）
- ✅ 工业级文档解析（PDF/Word/Markdown/TXT/HTML + 表格 + OCR）
- ✅ 多种 Chunk 策略（固定/语义/递归/结构感知/Small-to-Big）
- ✅ FAISS + Chroma 向量索引构建、性能 benchmark、持久化
- ✅ 混合检索（BM25 + 向量 + RRF/加权融合 + Reranker 精排）
- ✅ LangGraph RAG 状态机（8 节点 + 循环路径 + checkpoint）
- ✅ RAG 量化评测（RAGAS/TruLens + A/B 测试管道）
- ✅ LlamaIndex 实战 + RAG Web 应用

## 前置要求

- 完成 [Phase 2](../phase2_llm_internals/)（理解 Embedding/Attention）
- 有 FastAPI 基础（Phase 1）

## 学习天数与任务表

| Day | 主题 | 文件 | 产出 | ✅ |
|:---:|:-----|:-----|:-----|:--:|
| 29-30 | 最简 RAG | `01_naive_rag.md` | 完整可运行的 RAG Demo | ☐ |
| 31-32 | 工业文档解析 | `02_document_loader.md` | 5 格式解析器 + 表格 OCR | ☐ |
| 33-34 | Chunk 策略 | `08_advanced_chunking.md` | 4 种分块策略对比 | ☐ |
| 35 | 数据预处理 | `02_document_loader.md` | MinHash 去重 + 质量过滤 | ☐ |
| 36-37 | 向量索引 | `03_vector_index.md` | FAISS/Chroma + benchmark | ☐ |
| 38-39 | 混合检索 | `04_hybrid_search.md` | BM25+Vector+RRF+Reranker | ☐ |
| 40 | LangGraph RAG | `05_langgraph_rag.md` | 8 节点状态机 | ☐ |
| 41-42 | RAG 评测 | `06_rag_evaluation.md` | RAGAS 报告 + 改进闭环 | ☐ |
| 43-44 | LlamaIndex | `09_llamaindex_basics.md` | IngestionPipeline + QueryEngine | ☐ |
| 45 | RAG Web App | `07_rag_web_app.md` | FastAPI + Vue3 + Docker | ☐ |

## 本阶段核心产出

- 📄 **工业文档解析器** — 支持 PDF 表格/扫描件 OCR
- 🔍 **混合检索引擎** — BM25+Vector+Reranker 三合一
- 📊 **RAG 评测报告** — RAGAS 指标 + A/B 对比
- 🌐 **RAG 知识库 Web 应用**

## 如何运行本阶段 Demo

```bash
# 最简 RAG
cd phase3_rag
pip install sentence-transformers numpy openai
# 按 01_naive_rag.md 中的代码创建 naive_rag.py
python naive_rag.py

# 文档解析
pip install pymupdf python-docx beautifulsoup4
# 按 02_document_loader.md 中的代码测试

# RAG 评测
pip install ragas datasets
# 按 06_rag_evaluation.md 中的代码运行评估
```

## 验收标准

- [ ] 跑通完整 RAG 链路（文档→检索→生成）
- [ ] 能解析 PDF/Word/Markdown 三种格式
- [ ] 实现并对比"纯向量检索 vs 混合检索"的 Top-5 结果
- [ ] 用 Ragas 输出至少一份评估报告

## 常见问题

| 问题 | 解决 |
|:-----|:-----|
| PDF 解析乱序 | 双栏排版用 `page.get_text("blocks")` 排序 |
| 向量检索结果差 | 检查 Embedding 模型是否支持中文（BGE 系列推荐） |
| FAISS 内存占用大 | 换 `IndexIVFFlat` 替代 `IndexFlatIP` |
| Ragas 需要 OpenAI Key | 改用本地 LLM 替代，设置 `LLM_BASE_URL` |

## 面试可讲点

1. "我不是只用向量检索，而是 BM25 + 向量 + RRF 融合 + Reranker 精排"
2. "我的 RAG 系统有完整的 Ragas 量化评测，不是拍脑袋说效果好"
3. "我用 LangGraph 状态机做了可恢复的 RAG 流程，支持检索失败自动改写重试"

## 下一阶段

👉 [Phase 4: 11 大开源项目极限冲刺](../phase4_projects/)
