# 🦙 09 — LlamaIndex 入门

> 🎯 **目标**：掌握 LlamaIndex 的核心抽象，对比 LangChain RAG 方案，知道什么时候用哪个。
> ⏱️ 预计时间：1 天

---

## 📋 LlamaIndex vs LangChain：什么时候用哪个？

| 维度 | LlamaIndex | LangChain |
|:-----|:----------|:---------|
| 核心定位 | 数据→LLM 的桥梁（**数据索引优先**） | 通用 LLM 应用框架（**流程编排优先**） |
| RAG 能力 | ⭐⭐⭐⭐⭐ 原生最强 | ⭐⭐⭐ 需手工组装 |
| Agent 能力 | ⭐⭐ | ⭐⭐⭐⭐ LangGraph |
| 学习曲线 | ⭐⭐⭐ 概念多但 API 统一 | ⭐⭐⭐⭐ 需理解多种组件 |
| 文档摄取管道 | ✅ IngestionPipeline 开箱即用 | 需手动组 DocumentLoader+Splitter+Embedding |
| 查询引擎 | ✅ QueryEngine/Router/SubQuestion | 需手动写 Prompt+检索+生成逻辑 |
| 评测 | ✅ 内置评估模块 | 需集成 Ragas |
| 适合场景 | 知识库/文档问答/RFP 分析 | 复杂 Agent 工作流/多步推理 |

> 🔥 **一句话**：纯 RAG 用 LlamaIndex，复杂 Agent 用 LangGraph，两者可以混用。

---

## 1️⃣ IngestionPipeline：一条命令搞定文档摄取

```bash
pip install llama-index llama-index-embeddings-huggingface
```

```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import SimpleDirectoryReader

# 1. 加载文档
documents = SimpleDirectoryReader("./phase2_notes").load_data()
print(f"加载了 {len(documents)} 个文档")

# 2. 定义处理管道
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=500, chunk_overlap=50),
        HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5"),
    ],
)

# 3. 一键处理（分块 + Embedding）
nodes = pipeline.run(documents=documents)
print(f"生成了 {len(nodes)} 个节点")

# 4. 建索引
from llama_index.core import VectorStoreIndex
index = VectorStoreIndex(nodes=nodes)

# 5. 持久化
index.storage_context.persist(persist_dir="./llamaindex_index")
```

对比 LangChain 需要手动写 DocumentLoader → Splitter → Embedding → VectorStore → add_documents，代码量 3-4x。

---

## 2️⃣ QueryEngine：多种查询模式

### 基础查询

```python
query_engine = index.as_query_engine(
    similarity_top_k=5,
    streaming=True,
)

# 同步
response = query_engine.query("什么是 KV Cache？")
print(response)

# 流式
streaming_response = query_engine.query("解释 Attention 机制")
for token in streaming_response.response_gen:
    print(token, end="")
```

### Citation 引用模式

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import CitationQueryEngine

citation_engine = CitationQueryEngine.from_args(
    index,
    citation_chunk_size=512,
    citation_chunk_overlap=20,
)
response = citation_engine.query("Transformer 的核心组件？")
# 自动附带引用来源
print(response.response)  # 答案
for source in response.source_nodes:
    print(f"[{source.node_id}] {source.text[:100]}... Score: {source.score:.3f}")
```

---

## 3️⃣ RouterQueryEngine：多知识库自动路由

```python
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector

# 为每个知识库创建独立索引
phase2_index = VectorStoreIndex.from_documents(phase2_docs)
paper_index = VectorStoreIndex.from_documents(paper_docs)

# 封装为工具
tool1 = QueryEngineTool(
    query_engine=phase2_index.as_query_engine(),
    metadata=ToolMetadata(
        name="phase2_notes",
        description="Phase 2 学习笔记：Transformer/Attention/KV Cache/RoPE/MoE",
    ),
)
tool2 = QueryEngineTool(
    query_engine=paper_index.as_query_engine(),
    metadata=ToolMetadata(
        name="papers",
        description="学术论文：Attention is All You Need、LoRA、DPO",
    ),
)

# Router 自动选择知识库
router = RouterQueryEngine.from_defaults(
    selector=LLMSingleSelector.from_defaults(),
    query_engine_tools=[tool1, tool2],
)

# 自动路由
response1 = router.query("什么是 KV Cache？")
# → 路由到 phase2_notes

response2 = router.query("DPO 和 RLHF 的数学推导有什么区别？")
# → 路由到 papers
```

---

## 4️⃣ SubQuestionQueryEngine：复杂问题拆解

```python
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.question_gen import LLMQuestionGenerator

engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=[tool1, tool2],
    question_gen=LLMQuestionGenerator.from_defaults(),
    use_async=True,  # 子问题并行查询
)

# 复杂问题自动拆解
response = engine.query("对比 Phase 2 笔记中的 Attention 机制和原论文中的 Attention 机制")
# 自动拆成：
#   Q1: Phase 2 笔记中 Attention 机制是什么？
#   Q2: 原论文中 Attention 机制是什么？
# → 分别查询 → 汇总回答
```

---

## 5️⃣ LlamaIndex + LangGraph 混用

```python
# LlamaIndex 做检索，LangGraph 做 Agent 编排
from langgraph.graph import StateGraph, END
from llama_index.core import VectorStoreIndex

# LlamaIndex 提供检索能力
index = VectorStoreIndex.from_documents(docs)
retriever = index.as_retriever(similarity_top_k=5)

# LangGraph 编排 Agent 流程
class RAGState(TypedDict):
    query: str
    retrieved_docs: list
    rewritten_queries: list
    answer: str

def retrieve_node(state: RAGState) -> RAGState:
    """用 LlamaIndex 检索"""
    state["retrieved_docs"] = retriever.retrieve(state["query"])
    return state

# ... 其余 LangGraph 节点
```

---

## 6️⃣ LlamaIndex 独有功能

| 功能 | LlamaIndex | LangChain |
|:-----|:---------|:--------|
| **IngestionPipeline** | ✅ 一条 pipeline | 需手动串联 |
| **RouterQueryEngine** | ✅ 自动路由 | 需手写路由逻辑 |
| **SubQuestionEngine** | ✅ 自动拆解 | 需手写拆解+汇总 |
| **内置评估** | ✅ `llama-index.evaluation` | 需集成 Ragas |
| **Data Connectors** | ✅ 160+ 数据源 | 需社区扩展 |
| **可观测性** | ✅ Callback + Arize Phoenix | LangSmith |

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|:-----|:-----|:-----|
| `ImportError: llama_index` | llama-index 拆成了多个包 | `pip install llama-index llama-index-embeddings-huggingface` |
| embedding 维度不匹配 | 换了 embedding 模型但索引没重建 | 删旧索引重新 ingestion |
| Router 总选错知识库 | description 不够具体 | metadata 写清楚"包含什么，不包含什么" |
| SubQuestion 拆解太碎 | LLM 过度拆解 | 调低 temperature + 限制子问题数 |

---

## ✅ 产出物 Checklist

- [ ] 用 LlamaIndex IngestionPipeline 完成文档摄取
- [ ] 实现基础 QueryEngine + 流式输出
- [ ] 对比 LlamaIndex 和 LangChain 完成同一 RAG 任务的代码量
- [ ] 尝试 RouterQueryEngine（至少 2 个知识库）
- [ ] （可选）尝试 SubQuestionQueryEngine
