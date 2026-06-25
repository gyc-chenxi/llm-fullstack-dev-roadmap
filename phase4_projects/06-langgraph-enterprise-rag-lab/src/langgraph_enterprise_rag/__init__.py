"""
LangGraph Enterprise RAG Lab
=============================

基于 LangGraph 状态机的企业级 RAG 系统，支持查询改写、混合检索、
Cross-Encoder 重排序、带引用的答案生成、忠实性校验和优雅降级。

完整数据流（8 节点状态机）：

  User Query
    │
    ▼
  [classify] ─── 规则分类: simple / needs_retrieval / multi_hop
    │
    ▼
  [rewrite]  ─── LLM 生成 3 个查询变体（关键词+语义+完整问句）
    │
    ▼
  [retrieve] ─── Hybrid Search: Dense (BGE-M3) + BM25 → RRF Fusion
    │
    ▼
  [judge]    ─── 相关性评估: 分词重叠 + dense score + BM25 bonus
    │
    ├── score >= 0.45 → [rerank] ─── Cross-Encoder (BGE-Reranker-v2-m3)
    │                                 │
    │                                 ▼
    │                            [generate] ─── LLM 生成带引用的答案
    │                                 │
    │                                 ▼
    │                            [verify] ─── 忠实性启发式评分
    │                                 │
    │                    ┌────────────┼────────────┐
    │                    │ score<0.70 │ score>=0.70│
    │                    ▼  & retries │            ▼
    │              [generate]        │        [output] → final_answer
    │                    │           │
    │                    └───────────┘
    │
    ├── score < 0.45 & retries left → [rewrite] (循环重试)
    │
    └── score < 0.45 & retries exhausted → [fallback] → 拒绝回答 → [output]

Last node:  [output] → END (RAGResponse JSON / SSE final event)

两层服务架构：
  Client → FastAPI (port 8006) → LangGraph StateGraph → llama.cpp (port 8080)
  Checkpoint: SQLite (AsyncSqliteSaver) — 支持对话状态持久化和断点恢复
"""