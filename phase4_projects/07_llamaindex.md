# P7: LlamaIndex 知识库应用（Day 65-67，3天）

> 🎯 **核心价值**：掌握另一种主流 RAG 框架，对比 LangChain 方案
> ⏱️ 3 天 | 📊 难度 ⭐⭐⭐

---

## 📋 你将学到什么

- ✅ LlamaIndex 核心抽象：Document / Node / Index / QueryEngine
- ✅ 多种 Index：VectorStoreIndex / SummaryIndex / KeywordTableIndex
- ✅ QueryEngine 组合：Router + SubQuestion + 多引擎融合
- ✅ 数据连接器：加载本地 Markdown / GitHub / Notion
- ✅ LlamaIndex vs LangChain 深度对比

---

## 1️⃣ 环境搭建

```bash
pip install llama-index llama-index-embeddings-huggingface llama-index-llms-openai chromadb
```

---

## 2️⃣ 从文档到问答 — 完整流程

```python
from llama_index.core import (
    VectorStoreIndex, SimpleDirectoryReader, Settings,
    StorageContext, load_index_from_storage,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI

# 全局配置
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)

# 1. 加载文档
documents = SimpleDirectoryReader("./phase2_notes").load_data()
print(f"📄 加载 {len(documents)} 个文档")

# 2. 建索引
index = VectorStoreIndex.from_documents(documents)
print(f"📊 索引构建完成")

# 3. 持久化
index.storage_context.persist(persist_dir="./llamaindex_storage")

# 4. 查询
query_engine = index.as_query_engine(similarity_top_k=5, streaming=True)
response = query_engine.query("什么是 KV Cache？")
print(f"🤖 回答: {response}")
print(f"📎 来源: {[n.node.metadata for n in response.source_nodes]}")
```

---

## 3️⃣ 三种 Index 类型实战

```python
from llama_index.core import (
    VectorStoreIndex, SummaryIndex, 
    KnowledgeGraphIndex, DocumentSummaryIndex,
)

docs = SimpleDirectoryReader("./docs").load_data()

# VectorStoreIndex — 语义搜索（最常用）
vector_index = VectorStoreIndex.from_documents(docs)
vector_engine = vector_index.as_query_engine(similarity_top_k=5)

# SummaryIndex — 适合"总结全文"类问题（非精确检索）
summary_index = SummaryIndex.from_documents(docs)
summary_engine = summary_index.as_query_engine(response_mode="tree_summarize")

# KeywordTableIndex — 关键词精确匹配
from llama_index.core import KeywordTableIndex
keyword_index = KeywordTableIndex.from_documents(docs)
keyword_engine = keyword_index.as_query_engine()

# 对比三种查询
query = "Transformer 的核心组件有哪些？"
print(f"Vector:  {vector_engine.query(query)}")
print(f"Summary: {summary_engine.query(query)}")
print(f"Keyword: {keyword_engine.query(query)}")
```

| Index 类型 | 检索方式 | 适合问题 | 不适合 |
|:----------|:--------|:--------|:-----|
| VectorStoreIndex | 语义相似度 | "什么是 X？" | 精确关键词 |
| SummaryIndex | 全文总结 | "总结一下..." | 精确定位段落 |
| KeywordTableIndex | 关键词匹配 | "API Key 配置" | 语义模糊查询 |

---

## 4️⃣ IngestionPipeline 文档摄取管道

```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.extractors import TitleExtractor, QuestionsAnsweredExtractor

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=500, chunk_overlap=50),
        TitleExtractor(),                    # 自动提取标题
        QuestionsAnsweredExtractor(),        # 自动生成"这段回答什么问题"
        HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5"),
    ],
)

nodes = pipeline.run(documents=docs)
print(f"管道处理完成，生成 {len(nodes)} 个节点")

# 节点自带丰富元数据
for node in nodes[:3]:
    print(f"  内容: {node.text[:80]}...")
    print(f"  元数据: {node.metadata}")
```

---

## 5️⃣ RouterQueryEngine 多知识库

```python
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector

# 知识库 A：Phase 2 笔记
tool_phase2 = QueryEngineTool(
    query_engine=VectorStoreIndex.from_documents(phase2_docs).as_query_engine(),
    metadata=ToolMetadata(
        name="phase2_notes",
        description="包含 Transformer、Attention、KV Cache、RoPE、MoE 的学习笔记",
    ),
)

# 知识库 B：论文
tool_papers = QueryEngineTool(
    query_engine=VectorStoreIndex.from_documents(paper_docs).as_query_engine(),
    metadata=ToolMetadata(
        name="papers",
        description="学术论文：Attention is All You Need、LoRA、DPO",
    ),
)

router = RouterQueryEngine(
    selector=LLMSingleSelector.from_defaults(),
    query_engine_tools=[tool_phase2, tool_papers],
)

# 自动路由
response1 = router.query("什么是 RoPE？")           # → phase2_notes
response2 = router.query("DPO 的损失函数是什么？")  # → papers
print(f"[{response1.metadata['tool_name']}] {response1}")
print(f"[{response2.metadata['tool_name']}] {response2}")
```

---

## 6️⃣ LlamaIndex vs LangChain 代码量对比

| 任务 | LlamaIndex | LangChain | 代码量比 |
|:-----|:----------|:---------|:---:|
| 文档加载+索引+查询 | ~10 行 | ~25 行 | 1:2.5 |
| 多知识库路由 | ~15 行 | ~50 行 | 1:3.3 |
| 带引用的问答 | 内置 | 需手写 Prompt | 1:5+ |
| 复杂 Agent 状态机 | 不支持 | LangGraph 原生 | — |

> 💡 **一句话**：纯 RAG 用 LlamaIndex（省代码），复杂 Agent 用 LangGraph（更灵活）。

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|:-----|:-----|:-----|
| `ImportError: llama_index` | 包拆分 | 按需安装 `llama-index-*` 子包 |
| embedding 维度不匹配 | 换模型后旧索引不兼容 | 删 `./llamaindex_storage/` 重建 |
| Router 总选错 | metadata description 不够具体 | 写清楚"包含什么，不包含什么" |
| chromadb 持久化失败 | 路径权限 | 确保 `persist_dir` 可写 |

---

## ✅ 产出物 Checklist

- [ ] LlamaIndex IngestionPipeline 完整摄取管道
- [ ] VectorStoreIndex / SummaryIndex 两种查询对比
- [ ] RouterQueryEngine 多知识库自动路由
- [ ] LlamaIndex vs LangChain 同任务代码量对比报告
