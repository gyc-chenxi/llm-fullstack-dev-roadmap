# LangGraph Enterprise RAG — API 文档

## 基本信息

| 项目 | 值 |
|------|-----|
| Base URL | `http://127.0.0.1:8006` |
| OpenAPI 文档 | `http://127.0.0.1:8006/docs` |
| 协议 | HTTP/1.1 REST + SSE |

---

## 端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/v1/rag/invoke` | 非流式 RAG 问答 |
| POST | `/v1/rag/stream` | SSE 流式 RAG 问答 |
| GET | `/v1/rag/state/{thread_id}` | 查询 checkpoint 状态 |

---

## GET /health

健康检查。

**请求**

```bash
curl http://127.0.0.1:8006/health
```

**响应** `200 OK`

```json
{
  "status": "ok"
}
```

---

## POST /v1/rag/invoke

非流式 RAG 问答。完整执行 8 节点状态机后返回结果。

**请求体** `application/json`

```json
{
  "query": "这批文档主要讲了什么？",
  "thread_id": "user-session-001",
  "max_retries": 3
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `query` | string | ✅ | 用户问题（≥1 字符） |
| `thread_id` | string | ✅ | 会话 ID，用作 checkpoint 隔离键 |
| `max_retries` | int | ❌ | 检索/生成最大重试次数，默认 3，范围 0-5 |

**响应** `200 OK`

```json
{
  "thread_id": "user-session-001",
  "status": "ok",
  "answer": "根据知识库资料，这批文档主要涵盖……",
  "citations": [
    {
      "label": "来源1",
      "doc_id": "abc123def456",
      "source": "data/raw/RAG_Survey.pdf",
      "title": "RAG_Survey.pdf",
      "quote": "Retrieval-Augmented Generation (RAG) is ..."
    }
  ],
  "debug": {
    "query_type": "needs_retrieval",
    "rewritten_queries": ["RAG 综述", "检索增强生成 调研", "RAG 技术调研报告"],
    "relevance_score": 0.72,
    "faithfulness_score": 0.85,
    "retrieve_retry_count": 1,
    "generate_retry_count": 1,
    "errors": [],
    "events": [
      {"node": "classify", "status": "done", "query_type": "needs_retrieval"},
      {"node": "rewrite", "status": "done", "rewritten_queries": ["..."]},
      {"node": "retrieve", "status": "done", "doc_count": 10}
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | `ok` / `fallback` / `failed` |
| `answer` | string | 最终答案 |
| `citations` | list | 引用来源列表 |
| `debug.query_type` | string | 问题分类结果 |
| `debug.relevance_score` | float | 检索相关性分数 (0-1) |
| `debug.faithfulness_score` | float | 答案忠实性分数 (0-1) |
| `debug.events` | list | 每个节点的执行事件 |

**示例**

```bash
curl -s http://127.0.0.1:8006/v1/rag/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "请总结知识库内容",
    "thread_id": "demo-001"
  }' | python -m json.tool --no-ensure-ascii
```

---

## POST /v1/rag/stream

SSE 流式 RAG 问答。实时推送每个节点的运行状态。

**请求体** `application/json`

与 `/v1/rag/invoke` 相同。

**响应** `text/event-stream`

### SSE 事件类型

| 事件 | 说明 | data 示例 |
|------|------|-----------|
| `node_start` | 节点开始执行 | `{"node":"retrieve","status":"running"}` |
| `node_end` | 节点执行完成 | `{"node":"retrieve","status":"done","doc_count":10}` |
| `final` | 流结束，包含最终结果 | `{"status":"ok","answer":"...","citations":[...]}` |
| `error` | 执行异常 | `{"thread_id":"...","message":"..."}` |

### 事件流示例

```text
event: node_start
data: {"node":"graph","status":"running","thread_id":"demo-002"}

event: node_start
data: {"node":"classify","status":"running"}

event: node_end
data: {"node":"classify","status":"done","query_type":"needs_retrieval"}

event: node_start
data: {"node":"rewrite","status":"running"}

event: node_end
data: {"node":"rewrite","status":"done","rewritten_queries":["查询1","查询2","查询3"]}

event: node_start
data: {"node":"retrieve","status":"running"}

event: node_end
data: {"node":"retrieve","status":"done","doc_count":8}

event: node_start
data: {"node":"judge","status":"running"}

event: node_end
data: {"node":"judge","status":"done","relevance_score":0.72}

event: node_start
data: {"node":"rerank","status":"running"}

event: node_end
data: {"node":"rerank","status":"done","doc_count":5}

event: node_start
data: {"node":"generate","status":"running"}

event: node_end
data: {"node":"generate","status":"done","citation_count":5}

event: node_start
data: {"node":"verify","status":"running"}

event: node_end
data: {"node":"verify","status":"done","faithfulness_score":0.85}

event: node_start
data: {"node":"output","status":"running"}

event: node_end
data: {"node":"output","status":"ok"}

event: final
data: {"thread_id":"demo-002","status":"ok","answer":"根据知识库资料……","citations":[...]}
```

**示例**

```bash
curl -N http://127.0.0.1:8006/v1/rag/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "请基于知识库解释核心技术路线。",
    "thread_id": "demo-002"
  }'
```

### Fallback 场景

当知识库无法回答问题时（如"火星地下城市的税收政策"）：

```text
event: node_start
data: {"node":"classify","status":"running"}

event: node_end
data: {"node":"classify","status":"done","query_type":"needs_retrieval"}

event: node_end
data: {"node":"rewrite","status":"done"}

event: node_end
data: {"node":"retrieve","status":"done","doc_count":0}

event: node_end
data: {"node":"judge","status":"done","relevance_score":0.0}

event: node_end
data: {"node":"fallback","status":"done"}

event: node_end
data: {"node":"output","status":"fallback"}

event: final
data: {"status":"fallback","answer":"知识库中未找到足够证据回答该问题。\n\n为了避免幻觉，本系统不会基于模型自身知识强行编造答案。","citations":[]}
```

---

## GET /v1/rag/state/{thread_id}

查询指定 thread 的 checkpoint 状态。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| `thread_id` | string | 会话 ID |

**响应** `200 OK`

```json
{
  "thread_id": "demo-001",
  "checkpoint_exists": true,
  "latest_node": "output",
  "values": {
    "query": "请总结知识库内容",
    "thread_id": "demo-001",
    "final_answer": "根据知识库资料……",
    "citations": [...],
    "status": "ok",
    "events": [...]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `thread_id` | string | 请求的 thread ID |
| `checkpoint_exists` | bool | 是否存在 checkpoint |
| `latest_node` | string | 最后执行的节点名称 |
| `values` | object | 完整的 `RAGState` 快照 |

**示例**

```bash
curl -s http://127.0.0.1:8006/v1/rag/state/demo-001 \
  | python -m json.tool --no-ensure-ascii
```

---

## 错误码

| 状态码 | 说明 | 常见原因 |
|:------:|------|---------|
| 200 | 成功 | — |
| 422 | 请求参数校验失败 | query 为空 / thread_id 为空 / max_retries 超出范围 |
| 500 | 服务端内部错误 | LLM 服务不可达 / Chroma 索引缺失 |
| 503 | 服务不可用 | 模型尚未加载完成 |
