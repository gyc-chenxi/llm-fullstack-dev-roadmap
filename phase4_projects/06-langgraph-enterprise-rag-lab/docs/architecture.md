# LangGraph Enterprise RAG — 架构文档

## 整体架构

```
┌─────────────────────────────────────────────────┐
│                    User / Client                  │
└─────────────────┬───────────────────────────────┘
                  │ HTTP (REST + SSE)
┌─────────────────▼───────────────────────────────┐
│              FastAPI Gateway (port 8006)          │
│  /health  /v1/rag/invoke  /v1/rag/stream         │
│  /v1/rag/state/{thread_id}                       │
└────────┬──────────────────────────────┬──────────┘
         │                              │
         │ lifespan()                   │
         │ AsyncSqliteSaver             │
         │                              │
┌────────▼──────────────────────────────▼──────────┐
│            LangGraph StateGraph (8 nodes)         │
│                                                  │
│  START → classify → rewrite → retrieve → judge   │
│            ▲                      │    │    │     │
│            │ (retry)              │    │    │     │
│            └──────────────────────┘    │    │     │
│                                        │    │     │
│            rerank ←────────────────────┘    │     │
│              │                               │     │
│          generate → verify ──(retry)────────┘     │
│              │         │                         │
│              │         └──→ output ←── fallback  │
│              │                    ▲              │
│              └────────────────────┘              │
│                         END                      │
└─────────────────────────────────────────────────┘
```

## 节点职责

### 1. classify（问题分类）

**输入**：`query`
**输出**：`query_type ∈ {simple, needs_retrieval, multi_hop}`

基于关键词规则判断问题是否需要检索。当前实现使用中文关键词匹配（"文档"、"知识库"、"对比"等），可替换为 LLM 分类器。

### 2. rewrite（查询改写）

**输入**：`query` + 当前 `retrieve_retry_count`
**输出**：`rewritten_queries: list[str]`

调用 LLM 生成 3 个检索查询变体（关键词型、语义型、完整问句型）。包含 JSON 解析容错和正则 fallback。每次调用递增 `retrieve_retry_count`。

### 3. retrieve（混合检索）

**输入**：`rewritten_queries`
**输出**：`retrieved_docs: list[RetrievedDoc]`

- **Dense 检索**：BGE-M3 embedding → Chroma 向量相似度
- **BM25 检索**：jieba 分词 + rank-bm25 稀疏检索
- **RRF 融合**：Reciprocal Rank Fusion (k=60)

### 4. judge（相关性判断）

**输入**：`query` + `retrieved_docs`
**输出**：`relevance_score: float`

基于 query-doc 词汇重叠率 + dense/bm25 score 加权计算相关性。阈值 0.45 以上进入 rerank，否则触发 rewrite retry 或 fallback。

### 5. rerank（重排序）

**输入**：`query` + `retrieved_docs`
**输出**：`reranked_docs` (top-5)

使用 BAAI/bge-reranker-v2-m3 CrossEncoder 精排。如果模型加载失败，退化为 RRF score 排序。

### 6. generate（答案生成）

**输入**：`query` + `reranked_docs`（或 `retrieved_docs[:5]`）
**输出**：`generated_answer` + `citations`

基于上下文拼接的 LLM 生成，要求必须带引用标记 `[来源1]`，超范围问题时明确拒答。

### 7. verify（忠实性校验）

**输入**：`generated_answer` + `citations` + `docs`
**输出**：`faithfulness_score: float`

基于规则启发式评分：包含引用标记为 0.85，拒答为 1.0，无引用为 0.30。阈值 0.70 以上通过。

### 8. fallback / output（兜底 & 输出）

- **fallback**：设置 `generated_answer` 为拒答文案，`status=fallback`
- **output**：将 `generated_answer` 赋值给 `final_answer`，固化最终状态

## 条件路由

### route_after_judge

```
relevance_score >= 0.45  →  rerank
relevance_score < 0.45 && retries < max  →  rewrite
relevance_score < 0.45 && retries >= max  →  fallback
```

### route_after_verify

```
faithfulness_score >= 0.70  →  output
faithfulness_score < 0.70 && retries < max  →  generate
faithfulness_score < 0.70 && retries >= max  →  output
```

## Checkpoint 策略

| 场景 | Checkpointer | 导入路径 |
|------|-------------|----------|
| 同步（脚本/invoke） | `SqliteSaver` | `langgraph.checkpoint.sqlite` |
| 异步（FastAPI/SSE） | `AsyncSqliteSaver` | `langgraph.checkpoint.sqlite.aio` |

每个 thread_id 对应一个独立的 checkpoint 记录。checkpoint 包含完整的 `RAGState`（查询、改写历史、检索结果、生成答案、重试计数、事件日志、错误日志）。

## 检索管线

```
data/raw/ (PDF, MD, TXT, HTML)
    │
    ▼
[loaders.py] 文档加载 (pypdf, bs4, markdown-it)
    │
    ▼
[chunking.py] 文本切分 (700 chars, 120 overlap)
    │
    ▼
[embeddings.py] BGE-M3 embedding (MPS/CUDA/CPU)
    │
    ▼
[chroma_store.py] Chroma PersistentClient 持久化
    │
    ▼
[bm25.py] jieba 分词 + BM25Okapi 建索
    │
    ▼
[hybrid_search.py] RRF 融合 + 多查询聚合
    │
    ▼
[reranker.py] CrossEncoder 精排 (BAAI/bge-reranker-v2-m3)
```

## 可观测性

- **events**：每个节点的 `RAGState.events` 附加到 state，通过 `operator.add` 累加
- **SSE**：`/v1/rag/stream` 端点使用 `astream_events(v2)` 推送节点级事件
- **tracing**：`observability/tracing.py` 提供 `trace_node` context manager
- **logging**：`observability/logging.py` 提供 loguru/标准日志统一入口
